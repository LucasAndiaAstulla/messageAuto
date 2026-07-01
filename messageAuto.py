import time
import csv
import os
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from selenium.common import TimeoutException, ElementNotInteractableException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================ CONFIGURAÇÕES ================
EXCEL_PATH = r"C:\Users\Lucas\PyCharmMiscProject\data\oportunidades01.xlsx"
CHROMEDRIVER_PATH = "chromedriver.exe"  # ajuste se necessário
LOGIN_EMAIL = "AQUI COLOQUE O EMAIL"
LOGIN_PASSWORD = "AQUI PREENCHA A SENHA"
MEU_NOME_CONSULTOR = "LUCAS ANDIA ASTULLA"  # será comparado em uppercase
HEADLESS = False
OUTPUT_CSV = "resultados_automacao.csv"
# ===============================================

# Mensagens (modelos)
MSG_TEMPLATES = {
    1: """Oi, {nome}! Tudo bem? 😀
Aqui é o Lucas, da Academia Gaviões 24h – Pimentas 🦅

Vi que você passou por aqui e fiquei feliz em saber que está pensando em cuidar mais da sua saúde. Isso é um passo muito importante! 👏

A nossa academia é aberta 24h e tem várias aulas coletivas (boxe, zumba, pilates, funcional...) que podem tornar sua rotina mais leve e prazerosa.

Me conta: qual é o seu maior objetivo hoje — ganhar energia, emagrecer, ou melhorar a disposição? Quero te ajudar a alcançar isso do jeito mais simples possível. 💪""",
    2: """Oi, {nome}! 👋
Lembrei de você porque vi que ainda não conseguimos conversar. 😅

Aqui na Gaviões 24h – Pimentas, acreditamos que cada pessoa tem seu próprio ritmo. Por isso, além da academia aberta o dia inteiro, temos aulas pra todos os estilos: dança, lutas, pilates, treinos funcionais...

Seria ótimo entender melhor o que você gosta, pra poder te mostrar a opção ideal. Afinal, quanto mais prazer no treino, mais fácil manter o hábito. 😉""",
    3: """Oi, {nome}! Tudo bem? 😀
Sei que a rotina é corrida, mas queria reforçar que estamos com condições super acessíveis (a partir de R$129/mês) e todas as aulas inclusas.

Mas o que realmente faz diferença não é o preço — é a sensação de sair de cada treino mais leve, com energia e disposição pra encarar o dia.

E eu adoraria te ver conquistando isso com a gente aqui na Gaviões. Que tal dar esse passo essa semana? 🚀""",
    4: """Oi, {nome}! 👋
Antes de encerrar nosso contato, queria te fazer um convite especial: que tal experimentar a Academia Gaviões 24h – Pimentas por conta da casa? 🎟️

Você pode vir fazer um treino ou participar de uma das nossas aulas coletivas sem pagar nada. Assim, não precisa acreditar só nas minhas palavras — pode sentir de perto a energia da academia, as pessoas e o clima que temos aqui.

Tenho certeza que, depois dessa experiência, vai ser muito mais fácil decidir. 😉
Posso reservar esse Free Pass pra você ainda essa semana?"""
}

# Palavras-chave para "scoring" (frases curtas que ajudam identificar cada template)
KEY_PHRASES = {
    1: ["vinha por aqui", "academia é aberta 24h", "qual é o seu maior objetivo", "quero te ajudar"],
    2: ["ainda não conseguimos conversar", "cada pessoa tem seu próprio ritmo", "aulas pra todos os estilos"],
    3: ["a partir de r$129", "todas as aulas inclusas", "que tal dar esse passo"],
    4: ["free pass", "por conta da casa", "posso reservar"]
}

# ================= UTILITÁRIOS SELENIUM =================

def init_driver(headless=False):
    svc = Service(CHROMEDRIVER_PATH)
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=svc, options=opts)
    driver.maximize_window()
    return driver

def wait_for(driver, timeout=20):
    return WebDriverWait(driver, timeout)

def try_find_visible(by, value, wait_obj, driver_obj):
    try:
        return wait_obj.until(EC.visibility_of_element_located((by, value)))
    except TimeoutException:
        frames = driver_obj.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            try:
                driver_obj.switch_to.frame(f)
                return wait_obj.until(EC.visibility_of_element_located((by, value)))
            except Exception:
                driver_obj.switch_to.default_content()
                continue
        raise TimeoutException(f"Elemento {value} não visível nem em iframes.")

def safe_send_keys(el, text, driver_obj):
    try:
        el.click()
    except Exception:
        pass
    try:
        el.clear()
    except Exception:
        pass
    try:
        el.send_keys(text)
        return
    except Exception:
        pass
    try:
        ActionChains(driver_obj).move_to_element(el).click(el).send_keys(text).perform()
        return
    except Exception:
        pass
    try:
        driver_obj.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            el, text
        )
        return
    except Exception as e:
        raise RuntimeError("Não foi possível preencher o campo (incluindo fallback JS).") from e

# ================= LÓGICAS ESPECÍFICAS =================

def login_evo(driver, wait):
    driver.get("https://evo5.w12app.com.br/#/acesso/gavioes/autenticacao")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    # usuário
    try:
        login_input = try_find_visible(By.ID, "usuario", wait, driver)
    except TimeoutException:
        login_input = try_find_visible(By.CSS_SELECTOR, "input[formcontrolname='usuario']", wait, driver)
    safe_send_keys(login_input, LOGIN_EMAIL, driver)
    # senha
    try:
        senha_input = try_find_visible(By.ID, "senha", wait, driver)
    except TimeoutException:
        senha_input = try_find_visible(By.CSS_SELECTOR, "input[formcontrolname='senha']", wait, driver)
    safe_send_keys(senha_input, LOGIN_PASSWORD, driver)
    # botão entrar
    for by, sel in [(By.CSS_SELECTOR, "button[type='submit']"), (By.CSS_SELECTOR, "button.btn-primary")]:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            return True
        except Exception:
            continue
    return False

def search_and_open_profile(driver, wait, nome):
    try:
        campo_busca = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='Pesquise por nome']")))
        campo_busca.click()
        campo_busca.clear()
        campo_busca.send_keys(nome)
        campo_busca.send_keys(Keys.ENTER)
        time.sleep(2)
        # checa "Nenhum resultado"
        try:
            driver.find_element(By.XPATH, "//small[contains(., 'Nenhum resultado encontrado')]")
            return False, "Nenhum resultado"
        except:
            pass
        # clica no primeiro resultado
        perfil = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.buscas")))
        perfil.click()
        time.sleep(1)
        # dentro do resultado, clicar no span do perfil para abrir (se necessário)
        try:
            elemento_perfil = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.truncate.max-350.m-x-xs")))
            elemento_perfil.click()
        except:
            pass
        time.sleep(1)
        return True, "Perfil aberto"
    except Exception as e:
        return False, f"Erro busca: {e}"

def abrir_aba_whatsapp(driver, wait):
    try:
        aba_whats = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'WhatsApp')]")))
        aba_whats.click()
        time.sleep(1.2)
        return True
    except Exception:
        return False

def pegar_consultor_do_perfil(driver, wait):
    try:
        consultor_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "span[data-cy='quem-enviou']")))
        return consultor_el.text.strip().upper()
    except Exception:
        return ""

def pegar_historico_whatsapp(driver):
    """
    Coleta textos relevantes do histórico:
    - <p data-cy="tipo-contato"> ... </p>
    - span[data-cy='texto-wpp']
    Retorna lista de textos (ordem do mais antigo para o mais recente)
    """
    textos = []
    try:
        ps = driver.find_elements(By.CSS_SELECTOR, "p[data-cy='tipo-contato']")
        spans = driver.find_elements(By.CSS_SELECTOR, "span[data-cy='texto-wpp']")
        # junta ambos mantendo ordem aproximada: preferimos spans (conteúdo das mensagens),
        # mas também pega p (descrição)
        for e in ps:
            t = e.text.strip()
            if t:
                textos.append(t)
        for e in spans:
            t = e.text.strip()
            if t:
                textos.append(t)
    except Exception:
        pass
    return textos

def score_match(historico):
    """
    Para cada template (1..4) calcula um score somando ocorrências de key phrases.
    Retorna o número da mensagem mais provável enviada (o índice da template com maior score),
    e se nenhum score > 0, retorna None.
    """
    scores = {k: 0 for k in KEY_PHRASES.keys()}
    joined = " ".join(historico).lower()
    for idx, phrases in KEY_PHRASES.items():
        for ph in phrases:
            if ph.lower() in joined:
                scores[idx] += 1
    # pega maior score
    best_idx = None
    best_score = 0
    for k, v in scores.items():
        if v > best_score:
            best_score = v
            best_idx = k
    return best_idx  # pode ser None

def determinar_proxima_msg(historico):
    """
    Determina qual mensagem enviar:
    - usa score_match para identificar última mensagem (aquela com maior score)
    - se identificar N -> envia N+1 (ou 1 se N==4)
    - se não identificar -> envia 1
    """
    matched = score_match(historico)
    if matched is None:
        return 1
    else:
        return matched + 1 if matched < 4 else 1

def abrir_painel_nova_msg(driver, wait):
    try:
        botao = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Nova Mensagem WhatsApp')]")))
        botao.click()
        time.sleep(0.8)
        return True
    except Exception:
        return False

def clicar_link_enviar_whatsapp(driver, wait):
    try:
        link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Clique aqui') and contains(., 'WhatsApp')]")))
        link.click()
        time.sleep(0.8)
        return True
    except Exception:
        return False

def preencher_textarea_e_salvar(driver, wait, mensagem):
    try:
        textarea = wait.until(EC.visibility_of_element_located((By.ID, "observacoes")))
        safe_send_keys(textarea, mensagem, driver)
        time.sleep(0.5)
        btn_salvar = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'SALVAR')]")))
        btn_salvar.click()
        time.sleep(1.0)
        return True
    except Exception as e:
        print("Erro ao preencher/salvar:", e)
        return False

def registrar_resultado_csv(nome, status, detalhe=""):
    header = ["Nome", "Status", "Detalhe", "Timestamp"]
    row = [nome, status, detalhe, time.strftime("%Y-%m-%d %H:%M:%S")]
    exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(header)
        writer.writerow(row)

# ================= FLUXO PRINCIPAL =================

def main():
    df = pd.read_excel(EXCEL_PATH)
    # remove colunas que não usamos (mesma lógica sua)
    colunas_remover = ["Passo atual", "Mês de aniversário", "PAR-Q válido", "Termos de uso aceito", "Temperatura"]
    df = df.drop(columns=colunas_remover, errors='ignore')

    driver = init_driver(headless=HEADLESS)
    wait = wait_for(driver)

    try:
        ok = login_evo(driver, wait)
        if not ok:
            print("Falha no login inicial. Verifique seletores/credenciais.")
            return

        nomes = df["Nome"].tolist()

        for nome in tqdm(nomes, desc="Processando clientes"):
            try:
                sucesso, detalhe = search_and_open_profile(driver, wait, nome)
                if not sucesso:
                    print(f"[X] {nome} -> {detalhe}")
                    registrar_resultado_csv(nome, "Não encontrado", detalhe)
                    continue

                # abriu perfil, agora abrir aba whatsapp
                if not abrir_aba_whatsapp(driver, wait):
                    print(f"[X] {nome} -> Não abriu aba WhatsApp")
                    registrar_resultado_csv(nome, "Erro", "Não abriu aba WhatsApp")
                    driver.back()
                    time.sleep(0.5)
                    continue

                consultor = pegar_consultor_do_perfil(driver, wait)
                if MEU_NOME_CONSULTOR.upper() not in consultor:
                    print(f"[X] {nome} pertence ao consultor: '{consultor}'. Pulando.")
                    registrar_resultado_csv(nome, "Pulou - outro consultor", consultor)
                    driver.back()
                    time.sleep(0.5)
                    continue

                historico = pegar_historico_whatsapp(driver)
                prox_idx = determinar_proxima_msg(historico)
                primeiro_nome = nome.split()[0].capitalize()
                mensagem_a_enviar = MSG_TEMPLATES[prox_idx].format(nome=primeiro_nome)

                # abrir painel nova mensagem e enviar
                if not abrir_painel_nova_msg(driver, wait):
                    print(f"[X] {nome} -> Não abriu painel Nova Mensagem")
                    registrar_resultado_csv(nome, "Erro", "Não abriu painel Nova Mensagem")
                    driver.back()
                    time.sleep(0.5)
                    continue

                if not clicar_link_enviar_whatsapp(driver, wait):
                    print(f"[X] {nome} -> Não clicou link enviar WhatsApp")
                    registrar_resultado_csv(nome, "Erro", "Não clicou link enviar WhatsApp")
                    driver.back()
                    time.sleep(0.5)
                    continue

                enviado = preencher_textarea_e_salvar(driver, wait, mensagem_a_enviar)
                if enviado:
                    print(f"[✔] {nome} -> Mensagem ({prox_idx}) enviada.")
                    registrar_resultado_csv(nome, "Mensagem enviada", f"Mensagem {prox_idx}")
                else:
                    print(f"[X] {nome} -> Falha ao enviar mensagem.")
                    registrar_resultado_csv(nome, "Erro", "Falha ao enviar mensagem")

                # volta para lista/perfil anterior
                driver.back()
                time.sleep(1)

            except Exception as e:
                print(f"Erro no cliente {nome}: {e}")
                registrar_resultado_csv(nome, "Erro exceção", str(e))
                try:
                    driver.back()
                except:
                    pass
                time.sleep(1)

    finally:
        time.sleep(1)
        driver.quit()
        print("Execução finalizada.")

if __name__ == "__main__":
    main()

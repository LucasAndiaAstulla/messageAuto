import time
import pandas as pd
from selenium import webdriver
from selenium.common import TimeoutException, ElementNotInteractableException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ====================================================================================================
# 1. Ler planilha
# ====================================================================================================

data = pd.read_excel(r"C:\Users\Lucas\PyCharmMiscProject\data\oportunidades01.xlsx")
print(data.head())
resultados = []

colunas_remover = ["Passo atual", "Mês de aniversário", "PAR-Q válido", "Termos de uso aceito", "Temperatura"]
data = data.drop(columns=colunas_remover, errors='ignore')


# ====================================================================================================
# 2. Configuração dos Drivers
# ====================================================================================================

# ======== CONFIGURAÇÃO DO CHROME DRIVER =========
service = Service("chromedriver.exe")  # Inicia o serviço com o chromedrive
options = webdriver.ChromeOptions() # Cria uma configuração para o chrome
driver = webdriver.Chrome(service=service, options=options) # Iniciação das atividades
wait = WebDriverWait(driver, 20) # Time para finalizar caso não esteja em ação


# ====================================================================================================
# 3. Funções para encontrar o componente e também colocar os dados desejados
# ====================================================================================================


def try_find_visible(by, value, wait_obj, driver_obj):
    """
    Função que tenta achar a variável correta
    """
    try:
        return wait_obj.until(EC.visibility_of_element_located((by, value)))
    except TimeoutException:
        # tenta dentro de iframes
        frames = driver_obj.find_elements(By.TAG_NAME, "iframe")
        for i, f in enumerate(frames):
            try:
                driver_obj.switch_to.frame(f)
                return wait_obj.until(EC.visibility_of_element_located((by, value)))
            except Exception:
                driver_obj.switch_to.default_content()
                continue
        # não encontrou
        raise TimeoutException(f"Elemento {value} não visível nem em iframes.")

def safe_send_keys(el, text, driver_obj):
    """
    Tenta enviar o texto desejado no input de diversas formas, pois
    dependendo do tipo de content você precisa fazer diferentes casos
    """
    #Tentativa 1
    try:
        el.click()
    except Exception:
        pass

    # Tentativa 2
    try:
        el.clear()
    except Exception:
        pass
    # Tentativa 3
    try:
        el.send_keys(text)
        return
    except (ElementNotInteractableException, Exception):
        pass

    # ActionChains tentativa
    try:
        ActionChains(driver_obj).move_to_element(el).click(el).send_keys(text).perform()
        return
    except Exception:
        pass

    # Fallback: inserir via JS e disparar evento input
    try:
        driver_obj.execute_script(
            "arguments[0].value = arguments[1]; "
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            el, text
        )
        return
    except Exception as e:
        raise RuntimeError("Não foi possível preencher o campo (incluindo fallback JS).") from e


# ====================================================================================================
# 4. Automação de forma mais direta
# ====================================================================================================
try:
    driver.get("https://evo5.w12app.com.br/#/acesso/gavioes/autenticacao")

    # aguarda carregamento mínimo da página
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Tente localizar o input de usuário (ajuste os seletores se precisar)
    try:
        login_input = try_find_visible(By.ID, "usuario", wait, driver)
    except TimeoutException:
        # caso o id seja diferente, podemos tentar por name ou CSS
        login_input = try_find_visible(By.CSS_SELECTOR, "input[formcontrolname='usuario']", wait, driver)

    safe_send_keys(login_input, "email-aqui", driver)

    # campo senha
    try:
        senha_input = try_find_visible(By.ID, "senha", wait, driver)
    except TimeoutException:
        senha_input = try_find_visible(By.CSS_SELECTOR, "input[formcontrolname='senha']", wait, driver)

    safe_send_keys(senha_input, "senha aqui", driver)

    # tentar clicar no botão de login - tenta vários seletores comuns
    login_btn = None
    possible_btn_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button.btn-primary"),
    ]
    for by, sel in possible_btn_selectors:
        try:
            login_btn = wait.until(EC.element_to_be_clickable((by, sel)))
            login_btn.click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            break
        except Exception:
            login_btn = None
            continue

    for i, row in data.iterrows():
        nome = row["Nome"]
        print(f"Pesquisando: {nome}")

        try:
            # localiza o campo de pesquisa principal
            campo_busca = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[placeholder*='Pesquise por nome']")
            ))

            # limpa e digita o nome
            campo_busca.click()
            campo_busca.clear()
            campo_busca.send_keys(nome)
            campo_busca.send_keys(Keys.ENTER)

            # aguarda resultados
            time.sleep(2)
            try:
                resultado_elemento = driver.find_element(By.XPATH,
                                                         "//small[contains(., 'Nenhum resultado encontrado')]")
                resultado_texto = resultado_elemento.text
            except:
                resultado_texto = "Encontrado"
        except Exception as e:
            print(f"Erro ao pesquisar {nome}: {e}")
            resultado_texto = "Erro"

        resultados.append(resultado_texto)

    # tempo para você ver o resultado durante testes
    time.sleep(6)

except Exception as e:
    print("Erro durante a automação:", repr(e))
finally:
    driver.quit()
import time
import pandas as pd
from selenium import webdriver
from selenium.common import TimeoutException, ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ====================================================================================================
# 1. Ler planilha
# ====================================================================================================

data = pd.read_excel(r"C:\Users\Lucas\PyCharmMiscProject\data\oportunidades01.xlsx")

colunas_remover = ["Passo atual", "Mês de aniversário", "PAR-Q válido", "Termos de uso aceito", "Temperatura"]
data = data.drop(columns=colunas_remover, errors='ignore')

# ====================================================================================================
# 2. Abrir navegador e acessar o site
# ====================================================================================================

# ======== CONFIGURAÇÃO DO CHROME DRIVER =========
service = Service("chromedriver.exe")  # ou caminho absoluto
options = webdriver.ChromeOptions()
# opções úteis (descomente se quiser conectar a um Chrome já aberto)
# options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

def try_find_visible(by, value, wait_obj, driver_obj):
    """
    Tenta achar o elemento visível no contexto atual.
    Se não encontrar, busca dentro de iframes (tentando cada um).
    Retorna o elemento encontrado ou lança TimeoutException.
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
    Tenta enviar texto de forma robusta:
    1) click + clear + send_keys
    2) ActionChains (move + click + send)
    3) fallback para JS (set value + disparar event input)
    """
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

    safe_send_keys(login_input, "EMAIL AQUI", driver)

    # campo senha
    try:
        senha_input = try_find_visible(By.ID, "senha", wait, driver)
    except TimeoutException:
        senha_input = try_find_visible(By.CSS_SELECTOR, "input[formcontrolname='senha']", wait, driver)

    safe_send_keys(senha_input, "SENHA AQUI", driver)

    # tentar clicar no botão de login - tenta vários seletores comuns
    login_btn = None
    possible_btn_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(., 'Entrar') or contains(., 'Login') or contains(., 'Acessar')]"),
        (By.CSS_SELECTOR, "button.btn-primary"),
    ]
    for by, sel in possible_btn_selectors:
        try:
            login_btn = wait.until(EC.element_to_be_clickable((by, sel)))
            login_btn.click()
            break
        except Exception:
            login_btn = None
            continue

    if not login_btn:
        # Se não achou e clicou, tentar submeter via ENTER no campo senha (ou via JS)
        try:
            senha_input.send_keys("\n")
        except Exception:
            # fallback JS para submeter forms
            driver.execute_script("document.querySelector('form')?.submit?.()")

    # aguardar algum sinal de login bem-sucedido (ajuste o seletor conforme o que muda após o login)
    try:
        wait.until(EC.url_changes("https://evo5.w12app.com.br/#/acesso/gavioes/autenticacao"))
    except Exception:
        # se a url não mudar, talvez apareça um painel; aguarde um elemento que indique login.
        pass

    # tempo para você ver o resultado durante testes
    time.sleep(6)

except Exception as e:
    print("Erro durante a automação:", repr(e))
finally:
    driver.quit()
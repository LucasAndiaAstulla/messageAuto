import time
import pandas as pd
from selenium import webdriver
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

service = Service("chromedriver.exe")  # ou o caminho completo no seu PC
driver = webdriver.Chrome(service=service)

driver.get("https://evo5.w12app.com.br/#/acesso/gavioes/autenticacao")

driver.maximize_window()

try:

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "usuario"))  # <-- troque conforme o site
    ).send_keys("lucas.andia.a@gmail.com")


    driver.find_element(By.ID, "senha").send_keys("_Lukinnhas_20041702_")


    driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]").click()

    time.sleep(5)

    print("Login realizado com sucesso (simulado)!")

except Exception as e:
    print("Erro durante o login:", e)

finally:

    driver.quit()
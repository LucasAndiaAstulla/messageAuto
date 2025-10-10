import pandas as pd

# ====================================================================================================
# Abrindo o excel a ser analisado
# ====================================================================================================

data = pd.read_excel(r"C:\Users\Lucas\PyCharmMiscProject\data\oportunidades01.xlsx")


# ====================================================================================================
# Informação do data
# ====================================================================================================

data.head(10)
data.describe()
data.info()

# ====================================================================================================
# Remover erros em colunas
# ====================================================================================================
# Era para excluir colunas não uteis
data = data.drop(["Passo atual"], axis=1)
data = data.drop(["Mês de aniversário"], axis=1)
data = data.drop(["PAR-Q válido"], axis=1)
data = data.drop(["Termos de uso aceito"], axis=1)
data = data.drop(["Temperatura"], axis=1)

# ====================================================================================================
# Remover erros em colunas
# ====================================================================================================

nome = data["Nome"].tolist()

for nome in data["Nome"]:
    msg = f"Olá, {nome}, dados processados!"
    print(msg)
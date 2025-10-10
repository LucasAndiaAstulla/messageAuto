# 🧠 Projeto de Automação de Mensagens para Clientes
### 📋 Descrição do Projeto

Este projeto tem como objetivo automatizar o contato com clientes a partir de dados registrados em uma planilha Excel.
A ideia é integrar a leitura, análise e envio de mensagens personalizadas via WhatsApp Web, otimizando o processo de comunicação e aumentando as chances de conversão de clientes para o plano oferecido.

Atualmente, o projeto está sendo desenvolvido em Python e evoluirá em etapas bem definidas.

### ⚙️  Funcionalidades Planejadas
#### ✅ Etapa 1 — Leitura e análise da planilha Excel

Leitura de dados utilizando a biblioteca pandas;

Extração de informações importantes, como:

ID do cliente

Nome

Mensagem mais recente

Conversão dos dados para listas e dicionários para uso posterior.

📌 Status: Concluído 🟢

#### 🔄 Etapa 2 — Busca de perfis em site

Automatizar o acesso a um site de perfis (por exemplo, sistema de oportunidades);

Procurar os clientes com base nas informações da planilha (ID, nome ou outro identificador);

Armazenar dados adicionais encontrados no site para análise posterior.

📌 Status: Em desenvolvimento 🟡

#### 💬 Etapa 3 — Análise e seleção de mensagens

Avaliar a última mensagem trocada com o cliente;

Escolher automaticamente a mensagem mais adequada com base no contexto (interesse, tempo sem resposta, status do cadastro, etc.);

Preparar mensagens personalizadas com o nome do cliente e informações do plano.

📌 Status: Planejado ⚪

#### 🤖 Etapa 4 — Envio automatizado pelo WhatsApp Web

Conexão com o WhatsApp Web via automação com Selenium ou pywhatkit;

Envio das mensagens corretas para cada cliente;

Registro de logs e resultados (clientes contatados, mensagens enviadas, erros, etc.).

📌 Status: Planejado ⚪

#### 🛠️ Tecnologias Utilizadas

Python 3.10+

Pandas — leitura e manipulação de planilhas Excel

OpenPyXL — suporte adicional para arquivos .xlsx

Selenium / PyWhatKit (planejado) — automação de navegador e envio de mensagens

Time / Logging — controle de tempo e registros de execução

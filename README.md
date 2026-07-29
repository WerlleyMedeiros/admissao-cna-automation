\# Admissão CNA — Automação



App local (Streamlit) que automatiza o processo de admissão de colaboradores

da CNA Idiomas: envio de e-mail de admissão, e-mail de cadastro de benefícios

(Ifood) e criação da planilha de banco de horas para professores.



\## Tecnologias utilizadas



\- Python 3

\- Streamlit — interface do formulário

\- Gmail API (OAuth 2.0) — envio de e-mails com anexos inline

\- Google Drive API / Google Sheets API — criação e preenchimento da

&#x20; planilha de banco de horas

\- python-dotenv — variáveis de ambiente



\## Como instalar/configurar



1\. Clone o repositório e crie o ambiente virtual:



```bash

&#x20;  python -m venv .venv

&#x20;  .venv\\Scripts\\activate      # Windows

&#x20;  pip install -r requirements.txt

```



2\. Configure a Gmail API (necessário para o envio real):

&#x20;  - Crie um projeto no \[Google Cloud Console](https://console.cloud.google.com/)

&#x20;  - Ative a Gmail API, a Drive API e a Sheets API

&#x20;  - Configure a tela de consentimento OAuth

&#x20;  - Gere credenciais OAuth do tipo "App para computador" e salve como

&#x20;    `credentials.json` na raiz do projeto

&#x20;  - Na primeira execução, uma aba do navegador vai pedir autorização —

&#x20;    depois disso o token fica salvo (`token.json`) e não pede de novo



3\. Ajuste `config.py` com os mapeamentos da sua organização (razão social

&#x20;  → escola, destinatários de e-mail, IDs de pasta/planilha do Drive)



4\. Rode o app:



```bash

&#x20;  streamlit run app.py

```



\## Exemplo de uso



1\. Abra `http://localhost:8501`

2\. Escolha o tipo de colaborador (Professor ou Administrativo) e quais

&#x20;  e-mails enviar (admissão, benefícios ou ambos)

3\. Preencha os dados e anexe os documentos exigidos

4\. Clique em processar — o app envia os e-mails, cria a planilha de banco

&#x20;  de horas (se for professor) e remove os documentos temporários ao final



\## Estrutura do repositório


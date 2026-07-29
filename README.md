# Admissão CNA — Automação

App local (Streamlit) que automatiza o processo de admissão de colaboradores
da CNA Idiomas: envio de e-mail de admissão, e-mail de cadastro de benefícios
(Ifood) e criação da planilha de banco de horas para professores.

## Tecnologias utilizadas

- Python 3
- Streamlit — interface do formulário
- Gmail API (OAuth 2.0) — envio de e-mails com anexos inline
- Google Drive API / Google Sheets API — criação e preenchimento da
  planilha de banco de horas
- python-dotenv — variáveis de ambiente

## Como instalar/configurar

1. Clone o repositório e crie o ambiente virtual:

```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
```

2. Configure a Gmail API (necessário para o envio real):
   - Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
   - Ative a Gmail API, a Drive API e a Sheets API
   - Configure a tela de consentimento OAuth
   - Gere credenciais OAuth do tipo "App para computador" e salve como
     `credentials.json` na raiz do projeto
   - Na primeira execução, uma aba do navegador vai pedir autorização —
     depois disso o token fica salvo (`token.json`) e não pede de novo

3. Ajuste `config.py` com os mapeamentos da sua organização (razão social
   → escola, destinatários de e-mail, IDs de pasta/planilha do Drive)

4. Rode o app:

```bash
   streamlit run app.py
```

## Exemplo de uso

1. Abra `http://localhost:8501`
2. Escolha o tipo de colaborador (Professor ou Administrativo) e quais
   e-mails enviar (admissão, benefícios ou ambos)
3. Preencha os dados e anexe os documentos exigidos
4. Clique em processar — o app envia os e-mails, cria a planilha de banco
   de horas (se for professor) e remove os documentos temporários ao final

## Estrutura sugerida do repositório

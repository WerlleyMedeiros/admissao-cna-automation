# Gupy CV Downloader Bot

Bot que automatiza o download em lote de currículos de candidatos na
plataforma Gupy, renomeando cada PDF com o nome do candidato.

## Tecnologias utilizadas

- Python 3
- Selenium (conexão via porta de depuração remota do Chrome — CDP)
- webdriver-manager
- keyboard (atalho F2 para parar a execução)

## Como instalar/configurar

```bash
pip install selenium webdriver-manager keyboard
```

Ajuste no início do script, se necessário:
- `PASTA_DESTINO` — pasta onde os currículos serão salvos
- `CHROME_EXE` — caminho do executável do Chrome na sua máquina

## Exemplo de uso

1. Rode o script:

```bash
   python bot_gupy_download_cv.py
```

2. O bot fecha qualquer Chrome aberto e abre uma nova instância já com a
   porta de depuração ativa
3. Faça login na Gupy manualmente e navegue até a página do primeiro candidato
4. Volte ao terminal e pressione Enter para iniciar
5. O bot baixa o CV, renomeia com o nome do candidato e avança
   automaticamente para o próximo, repetindo até não haver mais candidatos
6. Pressione **F2** a qualquer momento para interromper com segurança

## Estrutura sugerida do repositório

```
gupy-cv-downloader-bot/
├── bot_gupy_download_cv.py
├── requirements.txt
└── README.md
```

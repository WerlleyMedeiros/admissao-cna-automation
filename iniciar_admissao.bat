@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Admissao CNA - Iniciando...
echo ============================================

if not exist ".venv" (
    echo Primeira vez rodando: criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Python nao foi encontrado. Instale o Python em python.org
        echo e marque a opcao "Add Python to PATH" durante a instalacao.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias pela primeira vez, aguarde...
    pip install -r requirements.txt
)

echo.
echo Abrindo o app no navegador...
echo (Para fechar o app, feche esta janela.)
echo.

streamlit run app.py

pause

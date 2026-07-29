"""
modules/sheets_manager.py

Fase 3 do projeto Admissão CNA: cria o banco de horas real do professor.

Fluxo:
    1. Localiza a subpasta da escola dentro da pasta pai no Google Drive.
    2. Copia a planilha modelo de banco de horas para dentro dessa subpasta,
       já renomeada com o nome do professor.
    3. Escreve o nome do professor na célula fixa (D2) da aba "2026.2".

Depende dos escopos Drive + Sheets nas credenciais OAuth (ver gmail_auth.py).
"""

import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from modules import gmail_auth

logger = logging.getLogger(__name__)

# --- Constantes da Fase 3 (IDs confirmados por Well em 20/07/2026) ---

PASTA_PAI_DRIVE_ID = "1hfUG97vyyJx_IdoWtSormNcghRteEODh"
PLANILHA_MODELO_ID = "1O7iQXtEWaI8JsJNjU8y0rfoZ882iCxKyNg7CLmDFmcM"
ABA_BANCO_DE_HORAS = "2026.2"
CELULA_NOME_PROFESSOR = "D2"

# Mapeamento: nome da escola (como usado no config.py) -> nome exato da
# subpasta dentro da pasta pai no Drive.
ESCOLA_PASTA_DRIVE = {
    "CNA Aldeota Costa Barros": "Aldeota",
    "CNA Campina Grande": "Campina Grande",
    "CNA Eusébio": "Eusébio",
    "CNA Juazeiro do Norte": "Juazeiro do Norte",
    "CNA Maracanaú": "Maracanaú",
    "CNA Natal Zona Norte": "Natal",
    "CNA Passaré": "Passaré",
}


class SheetsManagerError(Exception):
    """Erro genérico do fluxo de banco de horas (Drive/Sheets)."""
    pass


def _get_drive_service():
    creds = gmail_auth.obter_credenciais()
    if creds is None:
        raise SheetsManagerError(
            "credentials.json não configurado ainda — não é possível criar "
            "o banco de horas real (sem modo simulação para esta etapa)."
        )
    return build("drive", "v3", credentials=creds)


def _get_sheets_service():
    creds = gmail_auth.obter_credenciais()
    if creds is None:
        raise SheetsManagerError(
            "credentials.json não configurado ainda — não é possível criar "
            "o banco de horas real (sem modo simulação para esta etapa)."
        )
    return build("sheets", "v4", credentials=creds)


def _encontrar_pasta_escola(drive_service, nome_escola: str) -> str:
    """
    Retorna o ID da subpasta da escola dentro da pasta pai.
    Lança SheetsManagerError se a escola não estiver mapeada ou a pasta
    não for encontrada no Drive (nome pode ter mudado, etc).
    """
    nome_pasta = ESCOLA_PASTA_DRIVE.get(nome_escola)
    if not nome_pasta:
        raise SheetsManagerError(
            f"Escola '{nome_escola}' não está mapeada em ESCOLA_PASTA_DRIVE. "
            f"Verifique config.py e sheets_manager.py."
        )

    query = (
        f"'{PASTA_PAI_DRIVE_ID}' in parents "
        f"and name = '{nome_pasta}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    try:
        resultado = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            spaces="drive",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives",
        ).execute()
    except HttpError as e:
        raise SheetsManagerError(f"Erro ao buscar pasta da escola no Drive: {e}")

    arquivos = resultado.get("files", [])
    if not arquivos:
        raise SheetsManagerError(
            f"Subpasta '{nome_pasta}' não encontrada dentro da pasta pai no Drive. "
            f"Confira se o nome está exatamente igual ao do Drive."
        )
    return arquivos[0]["id"]


def _copiar_planilha_modelo(drive_service, pasta_destino_id: str, nome_professor: str) -> str:
    """
    Copia a planilha modelo para dentro da pasta da escola, já renomeada.
    Retorna o ID da nova planilha.
    """
    novo_nome = f"Banco de Horas - {nome_professor}"
    corpo = {
        "name": novo_nome,
        "parents": [pasta_destino_id],
    }
    try:
        nova_planilha = drive_service.files().copy(
            fileId=PLANILHA_MODELO_ID,
            body=corpo,
            fields="id, name, webViewLink",
            supportsAllDrives=True,
        ).execute()
    except HttpError as e:
        raise SheetsManagerError(f"Erro ao copiar planilha modelo: {e}")

    logger.info("Planilha criada: %s (%s)", nova_planilha["name"], nova_planilha["id"])
    return nova_planilha["id"]


def _preencher_nome_professor(sheets_service, spreadsheet_id: str, nome_professor: str):
    """Escreve o nome do professor na célula fixa da aba 2026.2."""
    intervalo = f"{ABA_BANCO_DE_HORAS}!{CELULA_NOME_PROFESSOR}"
    corpo = {"values": [[nome_professor]]}
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=intervalo,
            valueInputOption="USER_ENTERED",
            body=corpo,
        ).execute()
    except HttpError as e:
        raise SheetsManagerError(
            f"Erro ao escrever nome do professor na célula {CELULA_NOME_PROFESSOR} "
            f"da aba '{ABA_BANCO_DE_HORAS}': {e}"
        )


def criar_planilha_banco_horas(nome_completo: str, nome_escola: str) -> str:
    """
    Função principal chamada pelo orquestrador.

    Autentica sozinha (mesmo padrão do email_sender.send_email, via
    gmail_auth), copia a planilha modelo para a pasta da escola certa e
    preenche o nome do professor na aba "2026.2".

    Args:
        nome_completo: nome completo do professor, como preenchido no formulário.
        nome_escola: nome da escola já mapeado (ex: "CNA Aldeota Costa Barros"),
               igual ao valor retornado pelo mapeamento razão social -> escola
               no config.py.

    Returns:
        Link (string) da planilha criada em caso de sucesso, ou "" em caso
        de falha — para bater com o `bool(link_planilha)` usado no
        orquestrador.
    """
    try:
        drive_service = _get_drive_service()
        sheets_service = _get_sheets_service()

        pasta_escola_id = _encontrar_pasta_escola(drive_service, nome_escola)
        spreadsheet_id = _copiar_planilha_modelo(drive_service, pasta_escola_id, nome_completo)
        _preencher_nome_professor(sheets_service, spreadsheet_id, nome_completo)

        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        logger.info("Banco de horas criado com sucesso para %s: %s", nome_completo, url)
        return url

    except SheetsManagerError as e:
        logger.error("Falha ao criar banco de horas para %s: %s", nome_completo, e)
        print(f"[ERRO] Falha ao criar banco de horas para '{nome_completo}': {e}")
        return ""

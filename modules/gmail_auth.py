"""
Autenticação OAuth com a Gmail API.

Na primeira vez que o app tentar enviar um e-mail de verdade, abre uma aba
do navegador pedindo pra você logar com a conta do Gmail que vai enviar os
e-mails (a mesma do EMAIL_REMETENTE em config.py) e autorizar o envio.
Depois disso, o token fica salvo em token.json e não pede login de novo
(a não ser que o token expire ou seja revogado).
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

# gmail.send: enviar e-mails.
# gmail.settings.basic: só pra LER a assinatura cadastrada no Gmail (não
# apaga nem muda nada nas suas configurações).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def credenciais_configuradas() -> bool:
    """True se o arquivo credentials.json (baixado do Google Cloud Console) existe."""
    return CREDENTIALS_PATH.exists()


def obter_credenciais():
    """
    Carrega (ou renova/gera via fluxo OAuth) as credenciais do Google usadas
    em todo o projeto — Gmail, Drive e Sheets compartilham a mesma
    autenticação. Retorna None se credentials.json ainda não foi configurado.
    """
    if not credenciais_configuradas():
        return None
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def obter_servico_gmail():
    """
    Retorna um serviço autenticado da Gmail API, ou None se credentials.json
    ainda não foi configurado (nesse caso, quem chamar deve cair pra modo
    simulação em vez de quebrar).
    """
    creds = obter_credenciais()
    if creds is None:
        return None
    return build("gmail", "v1", credentials=creds)
def obter_assinatura(servico, email_remetente: str) -> str | None:
    """
    Busca a assinatura cadastrada no Gmail (Configurações > Ver todas as
    configurações > Geral > Assinatura) pra conta que está enviando.

    Retorna o HTML da assinatura, ou None se não encontrar/der erro (quem
    chamar deve usar uma assinatura de reserva nesse caso).
    """
    try:
        resposta = servico.users().settings().sendAs().list(userId="me").execute()
        enderecos = resposta.get("sendAs", [])

        # Procura o endereço que bate com o remetente configurado; se não
        # achar, usa o que estiver marcado como padrão da conta.
        escolhido = next(
            (e for e in enderecos if e.get("sendAsEmail", "").lower() == email_remetente.lower()),
            None,
        ) or next((e for e in enderecos if e.get("isDefault")), None)

        if escolhido:
            return escolhido.get("signature") or None
    except Exception as e:
        print(f"[AVISO] Não foi possível buscar a assinatura do Gmail: {e}")
    return None

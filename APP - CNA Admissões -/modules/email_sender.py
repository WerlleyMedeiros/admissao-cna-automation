"""
Módulo de envio de e-mails via Gmail API.

STATUS: envio real implementado. Se o arquivo credentials.json ainda não
foi configurado (veja o README, seção "Configurar a Gmail API"), cai
automaticamente em modo simulação (dry-run) — assim o app não quebra
enquanto você não tiver feito essa configuração.

FORMATAÇÃO DO CORPO: pra colocar uma palavra ou trecho em negrito no
corpo do e-mail, envolva com ** (estilo Markdown), ex: "**Nome:**".
Isso é convertido pra <b> na versão HTML do e-mail e some na versão em
texto puro (que é usada como fallback pra clientes de e-mail que não
leem HTML).
"""
import base64
import html
import mimetypes
import re
import uuid
from dataclasses import dataclass, field
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import List
from pathlib import Path

import requests

import config
from modules import gmail_auth


@dataclass
class EmailDraft:
    subject: str
    to: List[str]
    cc: List[str]
    body: str
    attachments: List[Path] = field(default_factory=list)


def _destinatarios(destinatarios_reais: dict) -> tuple:
    """
    Retorna (to, cc) a usar. Em MODO_TESTE, redireciona tudo pra
    config.EMAIL_TESTE e limpa o cc, pra nenhum e-mail real ser tocado
    durante os testes.
    """
    if config.MODO_TESTE:
        return [config.EMAIL_TESTE], []
    return destinatarios_reais["to"], destinatarios_reais["cc"]


def montar_email_admissao(dados: dict) -> EmailDraft:
    """Monta o e-mail de admissão a partir dos dados do formulário."""
    subject = f"Admissão | {dados['nome_completo']} | {dados['razao_social']}"
    if config.MODO_TESTE:
        subject = f"[TESTE] {subject}"

    linhas = [
        f"Bom dia, Stee! Tudo bom?\nSeguiremos com a admissão da colaboradora(or) abaixo:\n",
        f"**Nome:** {dados['nome_completo']}",
        f"**Profissão:** {dados['profissao']}",
        f"**Escola:** {dados['escola']}",
        f"**Salário:** R$ {dados['salario']}",
        f"**Data de início:** {dados['data_inicio']}",
    ]

    if dados.get("tipo") == "Administrativo" and dados.get("jornada_trabalho"):
        linhas += ["", "**Jornada de trabalho:**", dados["jornada_trabalho"]]

    body = "\n".join(linhas)

    to, cc = _destinatarios(config.EMAIL_ADMISSAO_DESTINATARIOS)
    return EmailDraft(
        subject=subject,
        to=to,
        cc=cc,
        body=body,
        attachments=dados.get("documentos", []),
    )


def montar_email_beneficios(dados: dict) -> EmailDraft:
    """Monta o e-mail de cadastro de benefícios (Ifood) a partir dos dados do formulário."""
    subject = f"Cadastro Ifood | {dados['nome_completo']} | {dados['razao_social']}"
    if config.MODO_TESTE:
        subject = f"[TESTE] {subject}"

    linhas = [
        f"Bom dia! Tudo bom?\nPoderiam fazer o cadastro da colaboradora(or) abaixo, por favor?\n",
        f"**Nome completo:** {dados['nome_completo']}",
        f"**Data de nascimento:** {dados['data_nascimento']}",
        f"**CPF:** {dados['cpf']}",
        f"**Número de telefone:** {dados['telefone']}",
        f"**Escola:** {dados['escola']}",
    ]
    body = "\n".join(linhas)

    to, cc = _destinatarios(config.EMAIL_BENEFICIOS_DESTINATARIOS)
    return EmailDraft(
        subject=subject,
        to=to,
        cc=cc,
        body=body,
    )


def _remover_marcadores_negrito(texto: str) -> str:
    """Remove os marcadores **texto** do corpo, deixando só o texto puro (sem negrito)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", texto)


def _corpo_para_html(texto: str) -> str:
    """
    Converte o corpo em texto puro pra HTML: escapa caracteres especiais,
    troca \\n por <br> e converte **texto** em <b>texto</b>.
    """
    partes = texto.split("**")
    html_partes = []
    for i, parte in enumerate(partes):
        escapada = html.escape(parte).replace("\n", "<br>")
        if i % 2 == 1:
            html_partes.append(f"<b>{escapada}</b>")
        else:
            html_partes.append(escapada)
    return "".join(html_partes)


def _texto_da_assinatura_html(assinatura_html: str) -> str:
    """Versão em texto puro da assinatura HTML, pra usar na parte 'plain' do e-mail."""
    texto = re.sub(r"<br\s*/?>", "\n", assinatura_html, flags=re.IGNORECASE)
    texto = re.sub(r"</(p|div|tr|li)>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    return html.unescape(texto).strip()


def _inlinear_imagens_assinatura(assinatura_html: str) -> tuple:
    """
    Baixa as imagens referenciadas na assinatura (ícones, banner etc.) e
    embute cada uma como anexo inline (Content-ID) dentro do próprio e-mail.

    Isso resolve o problema de fotos que não apareciam pro destinatário:
    a assinatura vinda da API do Gmail referencia as imagens por link
    (ou por um id que só existe dentro do Gmail), e nem todo cliente de
    e-mail consegue carregar isso. Embutindo a imagem de verdade dentro
    da mensagem, ela aparece sempre, em qualquer lugar que o e-mail for
    aberto.

    Retorna (html_com_referencias_cid, lista_de_partes_MIMEImage).
    """
    partes_imagem = []

    def _baixar_e_substituir(match):
        src = match.group(1)

        if src.startswith("cid:"):
            # Já é uma referência inline — não tem como buscar o arquivo
            # original via essa API, deixa como está.
            return match.group(0)

        try:
            if src.startswith("data:"):
                cabecalho, dados_b64 = src.split(",", 1)
                conteudo = base64.b64decode(dados_b64)
                tipo = cabecalho.split(";")[0].replace("data:", "") or "image/png"
            else:
                resposta = requests.get(src, timeout=10)
                resposta.raise_for_status()
                conteudo = resposta.content
                tipo = resposta.headers.get("Content-Type", "image/png").split(";")[0]

            subtipo = tipo.split("/")[-1] if "/" in tipo else "png"
            content_id = uuid.uuid4().hex
            imagem = MIMEImage(conteudo, _subtype=subtipo)
            imagem.add_header("Content-ID", f"<{content_id}>")
            imagem.add_header("Content-Disposition", "inline")
            partes_imagem.append(imagem)

            return match.group(0).replace(src, f"cid:{content_id}")
        except Exception as e:
            print(f"[AVISO] Não consegui baixar uma imagem da assinatura ({src[:60]}...): {e}")
            return match.group(0)

    html_modificado = re.sub(
        r'<img[^>]+src=["\']([^"\']+)["\']', _baixar_e_substituir, assinatura_html
    )
    return html_modificado, partes_imagem


def _montar_mime(draft: EmailDraft, assinatura_html: str = None) -> dict:
    """
    Monta a mensagem MIME (com anexos) no formato que a Gmail API espera.

    O corpo sempre é enviado em dois formatos (multipart/alternative):
    texto puro (sem os marcadores de negrito) e HTML (com o negrito
    aplicado de fato). Isso garante que o negrito apareça mesmo quando
    não há assinatura HTML do Gmail (modo simulação, ou conta sem
    assinatura cadastrada) — nesse caso usa a assinatura de reserva em
    texto (config.ASSINATURA), só que também espelhada em HTML.

    Se assinatura_html vier preenchida (buscada da conta do Gmail), as
    imagens da assinatura são embutidas de verdade (não só linkadas).
    """
    mensagem = MIMEMultipart("mixed")
    mensagem["to"] = ", ".join(draft.to)
    if draft.cc:
        mensagem["cc"] = ", ".join(draft.cc)
    mensagem["subject"] = draft.subject

    imagens_assinatura = []
    if assinatura_html:
        assinatura_html, imagens_assinatura = _inlinear_imagens_assinatura(assinatura_html)
        assinatura_texto = _texto_da_assinatura_html(assinatura_html)
    else:
        assinatura_texto = config.ASSINATURA
        assinatura_html = "".join(
            f"<p>{html.escape(linha)}</p>" for linha in config.ASSINATURA.split("\n")
        )

    texto_plano = _remover_marcadores_negrito(draft.body) + "\n\n" + assinatura_texto
    corpo_html = _corpo_para_html(draft.body)
    html_completo = (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;">'
        f"{corpo_html}</div><br>{assinatura_html}"
    )

    alternativo = MIMEMultipart("alternative")
    alternativo.attach(MIMEText(texto_plano, "plain", "utf-8"))
    alternativo.attach(MIMEText(html_completo, "html", "utf-8"))

    if imagens_assinatura:
        relacionado = MIMEMultipart("related")
        relacionado.attach(alternativo)
        for imagem in imagens_assinatura:
            relacionado.attach(imagem)
        mensagem.attach(relacionado)
    else:
        mensagem.attach(alternativo)

    for caminho in draft.attachments:
        caminho = Path(caminho)
        if not caminho.exists():
            print(f"[AVISO] Anexo não encontrado, pulando: {caminho}")
            continue
        tipo, _ = mimetypes.guess_type(str(caminho))
        tipo_principal, subtipo = (tipo or "application/octet-stream").split("/", 1)
        with open(caminho, "rb") as f:
            parte = MIMEBase(tipo_principal, subtipo)
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", "attachment", filename=caminho.name)
        mensagem.attach(parte)

    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    return {"raw": raw}


def send_email(draft: EmailDraft) -> bool:
    """
    Envia o e-mail via Gmail API, usando a assinatura cadastrada na conta do
    Gmail. Se credentials.json ainda não foi configurado, cai em modo
    simulação (dry-run) automaticamente, usando a assinatura de reserva.
    """
    servico = gmail_auth.obter_servico_gmail()

    if servico is None:
        print("=" * 60)
        print("[DRY-RUN] credentials.json não configurado ainda — simulando envio.")
        print(f"Assunto: {draft.subject}")
        print(f"Para: {draft.to}")
        print(f"Cc: {draft.cc}")
        print(f"Anexos: {[str(a) for a in draft.attachments]}")
        print("-" * 60)
        print(_remover_marcadores_negrito(draft.body))
        print()
        print(config.ASSINATURA)
        print("=" * 60)
        return True

    assinatura_html = gmail_auth.obter_assinatura(servico, config.EMAIL_REMETENTE)
    if not assinatura_html:
        print("[AVISO] Não achei assinatura cadastrada no Gmail — usando a de reserva.")

    try:
        mensagem = _montar_mime(draft, assinatura_html)
        servico.users().messages().send(userId="me", body=mensagem).execute()
        print(f"✅ E-mail enviado de verdade: '{draft.subject}' para {draft.to}")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao enviar e-mail '{draft.subject}': {e}")
        return False

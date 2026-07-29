"""
Orquestrador: recebe os dados do formulário e executa as etapas corretas
conforme o tipo de colaborador (Professor ou Administrativo).
"""
from pathlib import Path
from typing import List

from modules import email_sender, sheets_manager


def processar_admissao(dados: dict) -> dict:
    """
    Executa o fluxo completo de admissão.

    dados: dict com as chaves nome_completo, tipo, envio_emails ("ambos",
    "somente_admissao" ou "somente_beneficios"), razao_social, escola,
    profissao, salario, data_inicio, data_nascimento, cpf, telefone,
    jornada_trabalho, documentos (lista de paths dos arquivos enviados).

    Retorna um dict com o status de cada etapa executada.
    """
    resultado = {"etapas": [], "sucesso_geral": True}
    envio_emails = dados.get("envio_emails", "ambos")
    enviar_admissao = envio_emails in ("ambos", "somente_admissao")
    enviar_beneficios = envio_emails in ("ambos", "somente_beneficios")

    # 1. E-mail de admissão — só quando escolhido no formulário. Já inclui
    #    a jornada de trabalho quando for Administrativo.
    if enviar_admissao:
        draft_admissao = email_sender.montar_email_admissao(dados)
        ok_admissao = email_sender.send_email(draft_admissao)
        resultado["etapas"].append({"etapa": "E-mail de admissão", "sucesso": ok_admissao})
        resultado["sucesso_geral"] &= ok_admissao

    # 2. E-mail de benefícios / Ifood — só quando escolhido no formulário
    if enviar_beneficios:
        draft_beneficios = email_sender.montar_email_beneficios(dados)
        ok_beneficios = email_sender.send_email(draft_beneficios)
        resultado["etapas"].append({"etapa": "E-mail de cadastro Ifood", "sucesso": ok_beneficios})
        resultado["sucesso_geral"] &= ok_beneficios

    # 3. Banco de horas — sempre roda para Professor, independente de
    #    quais e-mails foram escolhidos (Administrativo não tem essa etapa)
    if dados["tipo"] == "Professor":
        link_planilha = sheets_manager.criar_planilha_banco_horas(
            dados["nome_completo"], dados["escola"]
        )
        resultado["etapas"].append({
            "etapa": "Planilha de banco de horas",
            "sucesso": bool(link_planilha),
            "link": link_planilha,
        })
        resultado["link_planilha_banco_horas"] = link_planilha
        resultado["sucesso_geral"] &= bool(link_planilha)

    # 4. Limpeza dos documentos temporários — só se tudo deu certo
    if resultado["sucesso_geral"]:
        limpar_documentos_temporarios(dados.get("documentos", []))
        resultado["documentos_removidos"] = True
    else:
        resultado["documentos_removidos"] = False

    return resultado


def limpar_documentos_temporarios(documentos: List[Path]) -> None:
    """Remove os arquivos de documentos do colaborador após uso bem-sucedido."""
    for doc in documentos:
        try:
            Path(doc).unlink(missing_ok=True)
        except Exception as e:
            print(f"[AVISO] Não foi possível remover {doc}: {e}")

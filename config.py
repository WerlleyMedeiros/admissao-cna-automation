"""
Configurações centrais do app de admissão CNA.

IMPORTANTE: o mapeamento RAZAO_SOCIAL_ESCOLAS abaixo está com um "melhor palpite"
baseado nos nomes. Confirme e corrija os pares antes de usar em produção —
um mapeamento errado faz o e-mail sair com a razão social errada no assunto.
"""

# Razão social (unidade/grupo) -> escola (nome fantasia)
# Confirmado com o Well em 14/07/2026
RAZAO_SOCIAL_ESCOLAS = {
    "MSG Ensino": "CNA Aldeota Costa Barros",
    "Eusébio Ensino": "CNA Eusébio",
    "MPL Ensino": "CNA Juazeiro do Norte",
    "Natal Ensino": "CNA Natal Zona Norte",
    "MR Hub": "CNA Passaré",
    "CPG M7 Ensino": "CNA Campina Grande",
    "Capital Connect": "CNA Maracanaú",
}

# Lista de razões sociais (chaves do dict acima), pra popular o dropdown
RAZOES_SOCIAIS = list(RAZAO_SOCIAL_ESCOLAS.keys())

# E-mails fixos usados nos fluxos (ajuste conforme necessário)
EMAIL_REMETENTE = "pessoas.grupom7x@cna.com.br"

# --------------------------------------------------------------------------
# MODO TESTE: enquanto True, TODOS os e-mails (admissão e benefícios) são
# redirecionados para EMAIL_TESTE, ignorando os destinatários reais abaixo.
# Só trocar para False quando o Well validar que tudo está correto.
# --------------------------------------------------------------------------
MODO_TESTE = False
EMAIL_TESTE = "velozdomal@gmail.com"

# Destinatários REAIS (usados apenas quando MODO_TESTE = False)
EMAIL_ADMISSAO_DESTINATARIOS = {
    "to": ["stephany@atualcontabil.com", "nel@atualcontabil.com"],
    "cc": ["marcello@grupom7x.com.br", "andrea.oliveira@cna.com.br"],
}

EMAIL_BENEFICIOS_DESTINATARIOS = {
    "to": ["andrea.oliveira@cna.com.br", "financeiro.grupom7x@cna.com.br"],
    "cc": ["marcello@grupom7x.com.br"],
}

ASSINATURA = """Atenciosamente,

Werlley Medeiros
Departamento Pessoal
(85) 98968-2262
pessoas.grupom7x@cna.com.br"""

# Documentos exigidos no e-mail de admissão
DOCUMENTOS_ADMISSAO = [
    "RG, CNH ou CNE",
    "Diploma de estudos ou declaração de matrícula",
    "Título de eleitor ou certidão de quitação eleitoral",
    "Comprovante de endereço",
    "CTPS (digital ou foto da física)",
    "ASO",
    "Certificado de reservista (apenas para homens)",
]

# Link da pasta raiz do Drive compartilhado com as pastas de cada escola
DRIVE_PASTA_RAIZ = "https://drive.google.com/drive/folders/1hfUG97vyyJx_IdoWtSormNcghRteEODh"

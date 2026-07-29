"""
App de automação de admissão CNA — formulário principal.

Rodar com: streamlit run app.py
"""
import base64
import re
import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

import config
from modules.orquestrador import processar_admissao

st.set_page_config(page_title="Admissão CNA", page_icon="📋", layout="centered")

ASSETS_DIR = Path(__file__).parent / "assets"


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


logo_cna_b64 = _b64(ASSETS_DIR / "logo_cna_faded.png")
logo_m7x_b64 = _b64(ASSETS_DIR / "logo_m7x_faded.png")

# --------------------------------------------------------------------------
# CSS: cores do CNA + logos fixas no canto da tela.
#
# IMPORTANTE: as logos usam position:fixed (ligadas à janela do navegador),
# não background-attachment. Isso garante que elas fiquem sempre visíveis
# no canto, mesmo se o conteúdo da página for mais curto que a tela — foi
# exatamente esse o motivo de elas "sumirem" durante o uso normal antes.
#
# AJUSTE MANUAL: pra mudar posição/tamanho de cada logo, mexa nos valores
# de "left/right/bottom" (posição, em pixels) e "width" (tamanho) das
# classes .marca-dagua-cna e .marca-dagua-m7x logo abaixo.
# --------------------------------------------------------------------------
st.markdown(f"""
<style>
    h1 {{ color: #E4032E !important; font-size: 1.9rem !important; }}

    .stButton>button {{
        background-color: #E4032E;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.6rem 0;
    }}
    .stButton>button:hover {{
        background-color: #B80224;
        color: white;
    }}

    .st-key-cartao_dados {{
        background-color: rgba(255, 255, 255, 0.92);
        border: 1px solid #E4032E33;
        border-radius: 10px;
        padding: 0.6rem 1.2rem 1.2rem 1.2rem;
    }}

    .secao-titulo {{
        color: #0A2E52;
        font-weight: 700;
        font-size: 1.05rem;
        margin: 0.4rem 0 0.4rem 0;
    }}

    /* Marca d'água aplicada no <body> (sempre ocupa a tela inteira, ao
       contrário de outros elementos do Streamlit que só têm a altura do
       conteúdo) — por isso não fica mais cortada/invisível durante o uso
       normal, só aparecendo antes na exportação de PDF. */
    body {{
        background-image:
            url("data:image/png;base64,{logo_cna_b64}"),
            url("data:image/png;base64,{logo_m7x_b64}");
        background-repeat: no-repeat, no-repeat;
        background-position: left 16px bottom 16px, right 16px bottom 16px;
        background-size: 170px auto, 100px auto;
        background-attachment: fixed, fixed;
    }}
</style>
""", unsafe_allow_html=True)

st.title("📋 Admissão de Colaboradores")
st.caption("Preencha os dados abaixo e o sistema cuida do resto: e-mails e "
           "banco de horas.")

# Intervalo amplo de datas (sem limitar a 10 anos como o padrão do Streamlit)
DATA_MIN = date(1950, 1, 1)
DATA_MAX = date(2100, 12, 31)


# --------------------------------------------------------------------------
# Máscaras de CPF e telefone: formatam o valor quando o campo perde o foco
# (padrão de UX comum — o Streamlit não reformata a cada tecla digitada).
# --------------------------------------------------------------------------
def _formatar_cpf():
    digitos = re.sub(r"\D", "", st.session_state.get("cpf_input", ""))[:11]
    if len(digitos) > 9:
        valor = f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    elif len(digitos) > 6:
        valor = f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:]}"
    elif len(digitos) > 3:
        valor = f"{digitos[:3]}.{digitos[3:]}"
    else:
        valor = digitos
    st.session_state["cpf_input"] = valor


def _formatar_telefone():
    digitos = re.sub(r"\D", "", st.session_state.get("telefone_input", ""))[:11]
    if len(digitos) <= 2:
        valor = f"({digitos}" if digitos else ""
    elif len(digitos) <= 6:
        valor = f"({digitos[:2]}) {digitos[2:]}"
    elif len(digitos) <= 10:
        valor = f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    else:
        valor = f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    st.session_state["telefone_input"] = valor


# --------------------------------------------------------------------------
# Seção 1: Unidade e tipo
#
# AJUSTE MANUAL: pra mudar a proporção das colunas "Razão social" x "Escola",
# troque os números da lista COLUNAS_UNIDADE abaixo (são proporções, não px
# — [1, 1] = mesma largura pras duas; [2, 1] = razão social 2x mais larga
# que escola; [1, 2] = o contrário).
# --------------------------------------------------------------------------
COLUNAS_UNIDADE = [1, 1]

st.markdown('<div class="secao-titulo">🏫 Unidade</div>', unsafe_allow_html=True)

col_razao, col_escola = st.columns(COLUNAS_UNIDADE)
with col_razao:
    razao_social = st.selectbox("Razão social *", config.RAZOES_SOCIAIS)
with col_escola:
    escola = config.RAZAO_SOCIAL_ESCOLAS[razao_social]
    st.text_input("Escola (nome fantasia)", value=escola, disabled=True)

tipo = st.radio("Tipo de colaborador", ["Professor", "Administrativo"], horizontal=True)

OPCOES_ENVIO = {
    "Enviar os dois e-mails": "ambos",
    "Somente e-mail de admissão": "somente_admissao",
    "Somente e-mail de benefícios (Ifood)": "somente_beneficios",
}
label_envio = st.radio("E-mails a enviar", list(OPCOES_ENVIO.keys()))
envio_emails = OPCOES_ENVIO[label_envio]
enviar_admissao = envio_emails in ("ambos", "somente_admissao")
enviar_beneficios = envio_emails in ("ambos", "somente_beneficios")

st.divider()

# --------------------------------------------------------------------------
# Seção 2: Dados do colaborador (fora do st.form, pra permitir a formatação
# automática de CPF/telefone ao sair do campo)
# --------------------------------------------------------------------------
with st.container(key="cartao_dados"):
    st.markdown('<div class="secao-titulo">🧑‍💼 Dados do colaborador</div>', unsafe_allow_html=True)

    nome_completo = st.text_input("Nome completo *")

    profissao = ""
    cpf = ""
    if enviar_admissao and enviar_beneficios:
        col1, col2 = st.columns(2)
        with col1:
            profissao = st.text_input("Profissão *")
        with col2:
            cpf = st.text_input(
                "CPF *", key="cpf_input", placeholder="000.000.000-00",
                max_chars=14, on_change=_formatar_cpf,
            )
    elif enviar_admissao:
        profissao = st.text_input("Profissão *")
    elif enviar_beneficios:
        cpf = st.text_input(
            "CPF *", key="cpf_input", placeholder="000.000.000-00",
            max_chars=14, on_change=_formatar_cpf,
        )

    data_nascimento = None
    telefone = ""
    if enviar_beneficios:
        col3, col4 = st.columns(2)
        with col3:
            data_nascimento = st.date_input(
                "Data de nascimento *", format="DD/MM/YYYY",
                min_value=DATA_MIN, max_value=DATA_MAX, value=None,
            )
        with col4:
            telefone = st.text_input(
                "Telefone *", key="telefone_input", placeholder="(85) 90000-0000",
                max_chars=15, on_change=_formatar_telefone,
            )

    salario = ""
    data_inicio = None
    if enviar_admissao:
        col5, col6 = st.columns(2)
        with col5:
            salario = st.text_input("Salário (R$) *", placeholder="1.685,84")
        with col6:
            data_inicio = st.date_input(
                "Data de início *", format="DD/MM/YYYY",
                min_value=DATA_MIN, max_value=DATA_MAX, value=None,
            )

    jornada_trabalho = ""
    if tipo == "Administrativo" and enviar_admissao:
        st.markdown('<div class="secao-titulo">🕒 Jornada de trabalho</div>', unsafe_allow_html=True)
        jornada_trabalho = st.text_area(
            "Jornada de trabalho *",
            placeholder=(
                "Segunda a Quinta: 12h00 às 21h00 | Intervalo: 15h30 às 16h30\n"
                "Sexta: 12h00 às 19h00 | Intervalo: 15h30 às 16h30\n"
                "Sábado: 08h00 às 14h00"
            ),
            height=100,
            label_visibility="collapsed",
        )

    documentos_upload = []
    if enviar_admissao:
        st.markdown('<div class="secao-titulo">📎 Documentos</div>', unsafe_allow_html=True)
        st.caption("RG/CNH/CNE, diploma ou declaração de matrícula, título de eleitor "
                   "ou certidão de quitação eleitoral, comprovante de endereço, CTPS, "
                   "ASO e reservista (se homem)")
        documentos_upload = st.file_uploader(
            "Anexar documentos (PDF ou foto)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

st.write("")
enviado = st.button("🚀 Processar admissão", use_container_width=True)

if enviado:
    campos_obrigatorios = [nome_completo]
    if enviar_admissao:
        campos_obrigatorios += [profissao, salario, data_inicio]
    if enviar_beneficios:
        campos_obrigatorios += [cpf, telefone, data_nascimento]

    if not all(campos_obrigatorios):
        st.error("Preencha todos os campos obrigatórios (*) antes de continuar.")
    elif tipo == "Administrativo" and enviar_admissao and not jornada_trabalho.strip():
        st.error("Preencha a jornada de trabalho.")
    elif enviar_beneficios and len(re.sub(r"\D", "", cpf)) != 11:
        st.error("CPF incompleto — precisa ter 11 dígitos.")
    elif enviar_beneficios and len(re.sub(r"\D", "", telefone)) not in (10, 11):
        st.error("Telefone incompleto — confira o DDD e o número.")
    else:
        # Salva os documentos enviados em arquivos temporários
        paths_documentos = []
        if documentos_upload:
            tmp_dir = Path(tempfile.mkdtemp(prefix="admissao_"))
            for arquivo in documentos_upload:
                destino = tmp_dir / arquivo.name
                destino.write_bytes(arquivo.getbuffer())
                paths_documentos.append(destino)

        dados = {
            "tipo": tipo,
            "envio_emails": envio_emails,
            "nome_completo": nome_completo,
            "profissao": profissao,
            "razao_social": razao_social,
            "escola": escola,
            "data_nascimento": data_nascimento.strftime("%d/%m/%Y") if data_nascimento else "",
            "cpf": cpf,
            "telefone": telefone,
            "salario": salario,
            "data_inicio": data_inicio.strftime("%d/%m/%Y") if data_inicio else "",
            "jornada_trabalho": jornada_trabalho.strip(),
            "documentos": paths_documentos,
        }

        with st.spinner("Processando admissão..."):
            resultado = processar_admissao(dados)

        if resultado["sucesso_geral"]:
            st.success("✅ Admissão processada com sucesso!")
        else:
            st.warning("⚠️ Algumas etapas falharam — confira abaixo.")

        for etapa in resultado["etapas"]:
            icone = "✅" if etapa["sucesso"] else "❌"
            st.write(f"{icone} {etapa['etapa']}")

        if resultado.get("link_planilha_banco_horas"):
            st.info(
                f"📊 **Planilha de banco de horas criada:** "
                f"[Abrir planilha]({resultado['link_planilha_banco_horas']})"
            )

        if resultado.get("documentos_removidos"):
            st.caption("🗑️ Documentos temporários removidos após conclusão.")

st.divider()
st.caption(
    "✅ E-mails e planilha de banco de horas são enviados/criados de verdade. "
    "Confira sempre os dados antes de clicar em \"Processar admissão\"."
)

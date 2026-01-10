import streamlit as st
import requests
import unicodedata
from datetime import datetime

DISCORD_WEBHOOK_URL = st.secrets["discord"]["webhook_url"]

st.set_page_config(page_title="BVI - Ocorrências", page_icon="logo.png", layout="centered")

# --- ESTILO PARA CENTRALIZAR LEGENDAS ---
st.markdown("<style>.stCaption {text-align: center;}</style>", unsafe_allow_html=True)

# --- DICIONÁRIO DE CORREÇÕES ---
CORRECOES = {
    "SEDUREZE": "SEDUREZ",
    "SIDOUREZ": "SEDUREZ",
    "SINCOPLE": "SÍNCOPE",
    "FEMENINO": "FEMININO",
    "COELOSO": "COELHOSO",
    "BRAGANCA": "BRAGANÇA",
    "TRAS": "TRÁS",
    "STº": "SANTO",
    "AV.": "AVENIDA",
    "SRA": "SENHORA",
    "P/": "PARA",
    "R.": "RUA",
    "DR.": "DOUTOR",
    "HOSP.": "HOSPITAL",
    "AMB": "AMBULÂNCIA",
    "URG": "URGÊNCIA",
    "ACID.": "ACIDENTE"
}

# --- FUNÇÕES ---
def normalizar_para_busca(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                  if unicodedata.category(c) != 'Mn').upper()

def corretor_inteligente(texto):
    if not texto: return ""
    palavras = texto.upper().split()
    texto_corrigido = []
    for p in palavras:
        limpa = p.rstrip(".,;:") 
        pontuacao = p[len(limpa):]
        if limpa in CORRECOES:
            texto_corrigido.append(f"{CORRECOES[limpa]}{pontuacao}")
        else:
            texto_corrigido.append(p)
    return " ".join(texto_corrigido)

# --- DADOS ---
pessoal_original = [
    "Luis Esmenio", "Denis Moreira", "Rafael Fernandes", "Marcia Mondego",
    "Francisco Oliveira", "Rui Parada", "Francisco Ferreira", "Pedro Veiga",
    "Rui Dias", "Artur Lima", "Óscar Oliveira", "Carlos Mendes",
    "Eric Mauricio", "José Melgo", "Andreia Afonso", "Roney Menezes",
    "EIP1", "EIP2", "Daniel Fernandes", "Danitiele Menezes",
    "Diogo Costa", "David Choupina", "Manuel Pinto", "Paulo Veiga",
    "Ana Maria", "Artur Parada", "Jose Fernandes", "Emilia Melgo",
    "Alex Gralhos", "Ricardo Costa", "Óscar Esmenio", "D. Manuel Pinto",
    "Rui Domingues"
]

mapa_pessoal = {normalizar_para_busca(n): n for n in pessoal_original}
lista_para_selecao = sorted(mapa_pessoal.keys())
lista_meios = sorted(["ABSC-03", "ABSC-04", "VFCI-04", "VFCI-05","VUCI-02", "VTTU-01", "VTTU-02", "VCOT-02","VLCI-01", "VLCI-03", "VETA-02"])

st.title("Registo de Ocorrências")

with st.form("formulario_ocorrencia", clear_on_submit=True):
    st.subheader("Preencha os dados:")
    nr_ocorrencia = st.text_input("📕 OCORRÊNCIA Nº")
    hora_input = st.text_input("🕜 HORA")
    motivo = st.text_input("🦺 MOTIVO")
    sexo_idade_input = st.text_input("👨 SEXO/IDADE")
    localidade = st.text_input("📍 LOCALIDADE")
    morada = st.text_input("🏠 MORADA")
    
    meios_sel = st.multiselect("🚒 MEIOS", options=lista_meios)
    ops_sel_limpos = st.multiselect("👨🏻‍🚒 OPERACIONAIS", options=lista_para_selecao)
    outros_meios = st.text_input("🚨 OUTROS MEIOS", value="NENHUM")
    
    submit = st.form_submit_button("SUBMETER", use_container_width=True)

if submit:
    if not (nr_ocorrencia and hora_input and motivo and sexo_idade_input and localidade and morada and meios_sel and ops_sel_limpos):
        st.error("⚠️ Por favor, preencha todos os campos obrigatórios!")
    else:
        hora_corrigida = hora_input.replace(".", ":")
        motivo_final = corretor_inteligente(motivo)
        localidade_final = corretor_inteligente(localidade)
        morada_final = corretor_inteligente(morada)
        
        val = sexo_idade_input.strip().upper()
        if val.startswith("F"): sexo_idade_final = val.replace("F", "FEMININO", 1)
        elif val.startswith("M"): sexo_idade_final = val.replace("M", "MASCULINO", 1)
        else: sexo_idade_final = val

        ops_originais = [mapa_pessoal[nome] for nome in ops_sel_limpos]
        ops_txt = ", ".join(ops_originais).upper()
        meios_txt = ", ".join(meios_sel).upper()

        texto_final = (
            f"📕 **OCORRENCIA Nº** ▶️ {nr_ocorrencia.upper()}\n"
            f"🕜 **HORA** ▶️ {hora_corrigida}\n"
            f"🦺 **MOTIVO** ▶️ {motivo_final}\n"
            f"👨 **SEXO/IDADE** ▶️ {sexo_idade_final}\n"
            f"📍 **LOCALIDADE** ▶️ {localidade_final}\n"
            f"🏠 **MORADA** ▶️ {morada_final}\n"
            f"🚒 **MEIOS** ▶️ {meios_txt}\n"
            f"👨🏻‍🚒 **OPERACIONAIS** ▶️ {ops_txt}\n"
            f"🚨 **OUTROS MEIOS** ▶️ {outros_meios.upper()}"
        )

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json={"content": texto_final})
            if response.status_code == 204:
                st.success("✅ Enviado com sucesso!")
            else:
                st.error(f"❌ Erro no Discord: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Erro de ligação: {e}")


# --- RODAPÉ ALINHADO À DIREITA (TRANSPARENTE E SEM FUNDO) ---
agora = datetime.now()

# Dicionário de tradução dos meses
meses_pt = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

data_extenso = f"{meses_pt[agora.month]} {agora.year}"

st.markdown(
    f"""
    <style>
    .rodape-limpo {{
        text-align: right;
        background-color: transparent; /* Garante que não há cor de fundo */
        color: #808495;
        font-size: 0.85rem;
        margin-top: 60px;
        border: none;
        padding: 0;
    }}
    </style>
    <div class="rodape-limpo">
        {data_extenso}<br>
        © DIREITOS RESERVADOS AOS BOMBEIROS VOLUNTÁRIOS DE IZEDA
    </div>
    """,
    unsafe_allow_html=True
)




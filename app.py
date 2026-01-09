import streamlit as st
import requests
import unicodedata

# URL do teu Webhook do Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1459146538235465850/0jdNsZWbwEFGTQmy-WuNVhVrWsDzk4nQDrwfJuGO_b2NORdDMZEB1sa6w_lW1X0sGRIB" \
""

st.set_page_config(page_title="BVI - Ocorrências", page_icon="logo.png", layout="centered")

# --- DICIONÁRIO DE CORREÇÕES AUTOMÁTICAS (Expandido) ---
CORRECOES = {
    "SEDUREZE": "SEDUREZ",
    "SIDOUREZ": "SEDUREZ",
    "SINCOPLE": "SÍNCOPE",
    "FEMENINO": "FEMININO",
    "COELOSO": "COELHOSO",
    "BRAGANCA": "BRAGANÇA",
    "STº": "SANTO",
    "AV.": "AVENIDA",
    "SRA": "SENHORA",
    "P/": "PARA",
    "TRAS": "TRÁS"
}

# --- FUNÇÕES DE APOIO ---
def normalizar_para_busca(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                  if unicodedata.category(c) != 'Mn').upper()

def corretor_inteligente(texto):
    palavras = texto.upper().split()
    texto_corrigido = []
    for p in palavras:
        limpa = p.replace(".", "").replace(",", "")
        if limpa in CORRECOES:
            # Mantém a pontuação original se existir
            prefixo = p[:p.find(limpa)]
            sufixo = p[p.find(limpa)+len(limpa):]
            texto_corrigido.append(f"{prefixo}{CORRECOES[limpa]}{sufixo}")
        else:
            texto_corrigido.append(p)
    return " ".join(texto_corrigido)

# --- CONFIGURAÇÃO DE DADOS ---
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

lista_meios = sorted([
    "ABSC-03", "ABSC-04", "VFCI-04", "VFCI-05","VUCI-02", "VTTU-01",
    "VTTU-02", "VCOT-02","VLCI-01", "VLCI-03", "VETA-02",
])

st.title("🚒 Registo de Ocorrências")

with st.form("formulario_ocorrencia", clear_on_submit=True):
    st.subheader("Preencha os dados:")
    
   
    nr_ocorrencia = st.text_input("📕 OCORRÊNCIA Nº")
    
    hora_input = st.text_input("🕜 HORA")

    motivo = st.text_input("🦺 MOTIVO")
    sexo_idade_input = st.text_input("👨 SEXO/IDADE (Ex: F 93)")
    localidade = st.text_input("📍 LOCALIDADE")
    morada = st.text_input("🏠 MORADA")
    
    meios_sel = st.multiselect("🚒 MEIOS", options=lista_meios)
    ops_sel_limpos = st.multiselect("👨🏻‍🚒 OPERACIONAIS", options=lista_para_selecao)
    
    outros_meios = st.text_input("🚨 OUTROS MEIOS", value="NENHUM")
    
    submit = st.form_submit_button("ENVIAR", use_container_width=True)

if submit:
    if not (nr_ocorrencia and hora_input and motivo and sexo_idade_input and localidade and morada and meios_sel and ops_sel_limpos):
        st.error("⚠️ Por favor, preencha todos os campos obrigatórios!")
    else:
        # 1. Hora
        hora_corrigida = hora_input.replace(".", ":")
        
        # 2. Correções Automáticas (Sedureze -> SEDUREZ, etc)
        motivo_final = corretor_inteligente(motivo)
        localidade_final = corretor_inteligente(localidade)
        morada_final = corretor_inteligente(morada)
        
        # 3. Sexo/Idade
        val = sexo_idade_input.strip().upper()
        if val.startswith("F"):
            sexo_idade_final = val.replace("F", "FEMININO", 1)
        elif val.startswith("M"):
            sexo_idade_final = val.replace("M", "MASCULINO", 1)
        else:
            sexo_idade_final = val

        # 4. Operacionais
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
                st.code(texto_final, language=None)
                st.balloons()
            else:
                st.error(f"❌ Erro no Discord: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Erro de ligação: {e}")
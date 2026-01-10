import streamlit as st
import requests
import unicodedata
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
DISCORD_WEBHOOK_URL = st.secrets["discord"]["webhook_url"]


st.set_page_config(page_title="BVI - Ocorrências", page_icon="logo.png", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)


CORRECOES = {
    "SEDUREZE": "SEDUREZ", "SIDOUREZ": "SEDUREZ", "SINCOPLE": "SÍNCOPE",
    "FEMENINO": "FEMININO", "COELOSO": "COELHOSO", "BRAGANCA": "BRAGANÇA",
    "TRAS": "TRÁS", "STº": "SANTO", "AV.": "AVENIDA", "SRA": "SENHORA",
    "P/": "PARA", "R.": "RUA", "DR.": "DOUTOR", "HOSP.": "HOSPITAL",
    "AMB": "AMBULÂNCIA", "URG": "URGÊNCIA", "ACID.": "ACIDENTE"
}

def normalizar_para_busca(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn').upper()

def corretor_inteligente(texto):
    if not texto: return ""
    palavras = texto.upper().split()
    return " ".join([CORRECOES.get(p.rstrip(".,;:"), p.rstrip(".,;:")) + p[len(p.rstrip(".,;:")):] for p in palavras])

# --- DADOS ---
pessoal_original = ["Luis Esmenio", "Denis Moreira", "Rafael Fernandes", "Marcia Mondego", "Francisco Oliveira", "Rui Parada", "Francisco Ferreira", "Pedro Veiga", "Rui Dias", "Artur Lima", "Óscar Oliveira", "Carlos Mendes", "Eric Mauricio", "José Melgo", "Andreia Afonso", "Roney Menezes", "EIP1", "EIP2", "Daniel Fernandes", "Danitiele Menezes", "Diogo Costa", "David Choupina", "Manuel Pinto", "Paulo Veiga", "Ana Maria", "Artur Parada", "Jose Fernandes", "Emilia Melgo", "Alex Gralhos", "Ricardo Costa", "Óscar Esmenio", "D. Manuel Pinto", "Rui Domingues"]
mapa_pessoal = {normalizar_para_busca(n): n for n in pessoal_original}
lista_para_selecao = sorted(mapa_pessoal.keys())
lista_meios = sorted(["ABSC-03", "ABSC-04", "VFCI-04", "VFCI-05","VUCI-02", "VTTU-01", "VTTU-02", "VCOT-02","VLCI-01", "VLCI-03", "VETA-02"])

st.title("🚒 Registo de Ocorrências")

with st.form("formulario_ocorrencia", clear_on_submit=True):
    st.subheader("Preencha os dados:")
    c1, c2 = st.columns(2)
    with c1: nr_ocorrencia = st.text_input("📕 OCORRÊNCIA Nº")
    with c2: hora_input = st.text_input("🕜 HORA")
    
    motivo = st.text_input("🦺 MOTIVO")
    sexo_idade_input = st.text_input("👨 SEXO/IDADE")
    localidade = st.text_input("📍 LOCALIDADE")
    morada = st.text_input("🏠 MORADA")
    meios_sel = st.multiselect("🚒 MEIOS", options=lista_meios)
    ops_sel_limpos = st.multiselect("👨🏻‍🚒 OPERACIONAIS", options=lista_para_selecao)
    outros_meios = st.text_input("🚨 OUTROS MEIOS", value="NENHUM")
    
    submit = st.form_submit_button("ENVIAR REGISTO", use_container_width=True)

if submit:
    if not (nr_ocorrencia and hora_input and motivo and localidade):
        st.error("⚠️ Preencha os campos obrigatórios!")
    else:
        # Processamento
        hora_c = hora_input.replace(".", ":")
        motivo_f = corretor_inteligente(motivo)
        localidade_f = corretor_inteligente(localidade)
        ops_txt = ", ".join([mapa_pessoal[nome] for nome in ops_sel_limpos]).upper()
        
        texto_discord = f"📕 **OCORRENCIA Nº** ▶️ {nr_ocorrencia.upper()}\n🕜 **HORA** ▶️ {hora_c}\n🦺 **MOTIVO** ▶️ {motivo_f}\n📍 **LOCALIDADE** ▶️ {localidade_f}\n🚒 **MEIOS** ▶️ {', '.join(meios_sel)}\n👨🏻‍🚒 **OPERACIONAIS** ▶️ {ops_txt}"

        dados_base = {
            "DATA REGISTO": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nº OCORRÊNCIA": nr_ocorrencia.upper(),
            "HORA": hora_c,
            "MOTIVO": motivo_f,
            "SEXO/IDADE": sexo_idade_input.upper(),
            "LOCALIDADE": localidade_f,
            "MORADA": corretor_inteligente(morada),
            "MEIOS": ", ".join(meios_sel).upper(),
            "OPERACIONAIS": ops_txt,
            "OUTROS MEIOS": outros_meios.upper()
        }

        try:
            # Enviar Discord
            requests.post(DISCORD_WEBHOOK_URL, json={"content": texto_discord})
            
            # Gravar na Google Sheet
            df_atual = conn.read()
            df_novo = pd.concat([df_atual, pd.DataFrame([dados_base])], ignore_index=True)
            conn.update(data=df_novo)
            
            st.success("✅ Sucesso! Enviado para Discord e Google Sheets.")
        except Exception as e:
            st.error(f"Erro: {e}")

# --- RODAPÉ ---
st.markdown(f'<div style="text-align: right; color: #808495; font-size: 0.85rem; margin-top: 50px;">BVI Izeda - © 2026</div>', unsafe_allow_html=True)

import streamlit as st
import requests
import unicodedata
import pandas as pd
import io
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE SEGURANÇA (Apenas Discord e Admin) ---
try:
    DISCORD_WEBHOOK_URL = st.secrets["DISCORD_WEBHOOK_URL"]
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception as e:
    st.error("⚠️ Verifica os Secrets no Streamlit Cloud (DISCORD_WEBHOOK_URL, ADMIN_USER, ADMIN_PASSWORD)!")
    st.stop()

# --- ESTADO DA SESSÃO PARA HISTÓRICO LOCAL ---
if "historico_ocorrencias" not in st.session_state:
    st.session_state.historico_ocorrencias = []

# --- FUNÇÕES AUXILIARES ---
def limpar_texto(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) 
                  if unicodedata.category(c) != 'Mn').upper()

def apenas_numeros(txt):
    nums = ''.join(filter(str.isdigit, txt))
    return nums if nums else "0"

def formatar_sexo(texto):
    if not texto or not texto.strip(): 
        return "Não Aplicável"
    
    t_upper = texto.strip().upper()
    idade = ''.join(filter(str.isdigit, t_upper))
    
    if t_upper.startswith("F"):
        genero = "Feminino"
    elif t_upper.startswith("M"):
        genero = "Masculino"
    else:
        return texto.capitalize()
    
    return f"{genero} de {idade} anos" if idade else genero

def formatar_hora(texto):
    t = texto.strip().replace(":", "").replace(".", "")
    if len(t) == 4 and t.isdigit(): 
        return f"{t[:2]}:{t[2:]}"
    return texto

def mes_extenso(dt_str):
    meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
             7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    try:
        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        return f"{meses[dt.month]} de {dt.year}"
    except: 
        return "Data Inválida"

def criar_excel_oficial(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ocorrencias', startrow=5)
        workbook, worksheet = writer.book, writer.sheets['Ocorrencias']
        fmt_header = workbook.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white', 'border': 1})
        worksheet.write('C2', 'RELATÓRIO OFICIAL BVI', workbook.add_format({'bold': True, 'font_size': 14}))
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(5, col_num, value, fmt_header)
            worksheet.set_column(col_num, col_num, 22)
    return output.getvalue()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BVI - Ocorrências", page_icon="logo.png", layout="centered")

if st.session_state.get("autenticado", False):
    st.sidebar.markdown(f"👤 **Utilizador:** {ADMIN_USER}")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("logo.png", width=90)
    except:
        st.write("🚒")
with col2:
    st.title("Registo de Ocorrências")

t1, t2 = st.tabs(["📝 Novo Registo", "🔐 Gestão"])

with t1:
    with st.form("f_novo", clear_on_submit=True):
        st.subheader("Nova Ocorrência:")
        nr = st.text_input("📕 OCORRÊNCIA Nº")
        hr = st.text_input("🕜 HORA")
        mot = st.text_input("🦺 MOTIVO - PRIORIDADE") 
        sex = st.text_input("👨 SEXO/IDADE") 
        loc = st.text_input("📍 LOCALIDADE")
        mor = st.text_input("🏠 MORADA")
        
        pessoal = sorted(["Luis Esmenio", "Denis Moreira","Francisco Oliveira", "Rafael Fernandes", "Marcia Mondego", "Rui Parada", "Francisco Ferreira", "Pedro Veiga", "Rui Dias", "Artur Lima", "Óscar Oliveira", "Carlos Mendes", "Eric Mauricio", "José Melgo", "Andreia Afonso", "Roney Menezes", "EIP1", "EIP2", "Daniel Fernandes", "Danitiele Menezes", "Diogo Costa", "David Choupina", "Manuel Pinto", "Paulo Veiga", "Ana Maria", "Artur Parada", "Jose Fernandes", "Emilia Melgo", "Alex Gralhos", "Ricardo Costa", "Óscar Esmenio", "D. Manuel Pinto", "Rui Domingues", "Sara Domingues"])
        mapa_nomes = {limpar_texto(n): n for n in pessoal}
        
        meios = st.multiselect("🚒 MEIOS", ["ABSC-03", "ABSC-04", "VFCI-04", "VFCI-05","VUCI-02", "VTTU-01", "VTTU-02", "VCOT-02","VLCI-01", "VLCI-03", "VETA-02", "ABTD-06"])
        ops = st.multiselect("👨🏻‍🚒 OPERACIONAIS", sorted(list(mapa_nomes.keys())))
        out = st.text_input("🚨 OUTROS MEIOS", value="Nenhum")
        
        if st.form_submit_button("SUBMETER", width='stretch'):
            if nr and hr and mot and loc and mor and meios and ops:
                nomes_completos = [mapa_nomes[n] for n in ops]
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                nr_upper = nr.upper()
                esconder_sexo = False
                
                if "CODU" in nr_upper:
                    nome_campo_nr = "📕 CODU Nº"
                elif "CDO'S" in nr_upper or "CSRTTM" in nr_upper:
                    nome_campo_nr = "📕 CSRTTM Nº"
                    esconder_sexo = True
                else:
                    nome_campo_nr = "📕 OCORRÊNCIA Nº"
                
                num_puro = apenas_numeros(nr)
                valor_sexo = formatar_sexo(sex)
                
                nova_linha = {
                    "numero": num_puro, 
                    "hora": formatar_hora(hr), 
                    "motivo": mot.title(),
                    "sexo": valor_sexo,
                    "localidade": loc.title(), 
                    "morada": mor.title(),
                    "meios": ", ".join(meios), 
                    "operacionais": ", ".join(nomes_completos),
                    "outros": out.title(), 
                    "data_envio": data_agora
                }
                
                # --- GUARDAR NO HISTÓRICO DA SESSÃO (Em vez do Supabase) ---
                st.session_state.historico_ocorrencias.append(nova_linha)
                
                # --- DISCORD ---
                try:
                    dados_discord = nova_linha.copy()
                    del dados_discord["data_envio"]
                    if dados_discord["numero"] == "0":
                        dados_discord["numero"] = nr_upper

                    mapa_labels = {
                        "numero": nome_campo_nr, "hora": "🕜 HORA", "motivo": "🦺 MOTIVO",
                        "sexo": "👨 SEXO/IDADE", "localidade": "📍 LOCALIDADE", "morada": "🏠 MORADA",
                        "meios": "🚒 MEIOS", "operacionais": "👨🏻‍🚒 OPERACIONAIS", "outros": "🚨 OUTROS MEIOS"
                    }
                    
                    linhas_msg = []
                    for k, v in dados_discord.items():
                        if k == "sexo" and esconder_sexo and v == "Não Aplicável":
                            continue
                        linhas_msg.append(f"**{mapa_labels[k]}** ▶️ {v}")
                    
                    msg_discord = "\n".join(linhas_msg)
                    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg_discord})
                    
                    st.success("✅ Ocorrência enviada com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro ao enviar para o Discord: {e}")
            else:
                st.error("⚠️ Preencha os campos obrigatórios!")

with t2:
    if not st.session_state.get("autenticado", False):
        u = st.text_input("Utilizador", key="u_log")
        s = st.text_input("Senha", type="password", key="s_log")
        if st.button("Entrar"):
            if u == ADMIN_USER and s == ADMIN_PASSWORD:
                st.session_state.autenticado = True
                st.rerun()
    else:
        # --- CARREGAR DADOS DA SESSÃO (Em vez do Supabase) ---
        if st.session_state.historico_ocorrencias:
            df = pd.DataFrame(st.session_state.historico_ocorrencias)
            
            mapa_colunas = {
                "numero": "📕 OCORRÊNCIA Nº", "hora": "🕜 HORA", "motivo": "🦺 MOTIVO",
                "sexo": "👨 SEXO/IDADE", "localidade": "📍 LOCALIDADE", "morada": "🏠 MORADA",
                "meios": "🚒 MEIOS", "operacionais": "👨🏻‍🚒 OPERACIONAIS", 
                "outros": "🚨 OUTROS MEIOS", "data_envio": "📅 DATA DO ENVIO"
            }
            df_v = df.rename(columns=mapa_colunas)
            
            st.subheader("📊 Totais")
            df_v['Mês'] = df_v['📅 DATA DO ENVIO'].apply(mes_extenso)
            st.table(df_v.groupby('Mês').size().reset_index(name='Total'))
            
            st.subheader("📋 Histórico (Sessão Atual)")
            st.dataframe(df_v, use_container_width=True)
            
            st.download_button("📥 Excel Oficial", criar_excel_oficial(df_v), f"BVI_{datetime.now().year}.xlsx")
        else:
            st.info("Nenhum dado registado nesta sessão.")

st.markdown(f'<div style="text-align: center; color: gray; font-size: 0.8rem; margin-top: 50px;">{datetime.now().year} © BVI</div>', unsafe_allow_html=True)

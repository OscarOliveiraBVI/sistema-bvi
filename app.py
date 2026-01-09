import streamlit as st
import requests
import unicodedata

# URL do teu Webhook do Discord
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1459146538235465850/0jdNsZWbwEFGTQmy-WuNVhVrWsDzk4nQDrwfJuGO_b2NORdDMZEB1sa6w_lW1X0sGRIB"


st.set_page_config(page_title="BVI - Ocorrências", page_icon="logo.png", layout="centered")

# --- DICIONÁRIO DE CORREÇÕES AUTOMÁTICAS ---
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

# --- LISTA DE OPERACIONAIS (Com acentos originais) ---
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

# --- FUNÇÕES DE APOIO ---
def normalizar_para_busca(txt):
    """Remove acentos e coloca em maiúsculas para facilitar a pesquisa."""
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                  if unicodedata.category(c) != 'Mn').upper()

def corretor_inteligente(texto):
    """Corrige palavras erradas baseando-se no dicionário CORRECOES."""
    palavras = texto.upper().split()
    texto_corrigido = []
    for p in palavras:
        limpa = p.replace(".", "").replace(",", "")
        if limpa in CORRECOES:
            texto_corrigido.append(CORRECOES[limpa])
        else:
            texto_corrigido.append(p)
    return " ".join(texto_corrigido)

# Preparar mapeamento para busca (Chave: OSCAR OLIVEIRA -> Valor: Óscar Oliveira)
mapa_pessoal = {normalizar_para_busca(n): n for n in pessoal_original}
lista_para_selecao = sorted(mapa_pessoal.keys())

# --- LISTA DE MEIOS ---
lista_meios = sorted([
    "ABSC-03", "ABSC-04", "VFCI-04", "VFCI-05","VUCI-02", "VTTU-01",
    "VTTU-02", "VCOT-02","VLCI-01", "VLCI-03", "VETA-02",
])

# --- INTERFACE ---
st.title("🚒 Registo de Ocorrências BVI")

with st.form("formulario_ocorrencia", clear_on_submit=True):
    st.subheader("Dados da Ocorrência")
    
    nr_ocorrencia = st.text_input("📕 OCORRÊNCIA Nº")
    hora_input = st.text_input("🕜 HORA")
    motivo = st.text_input("🦺 MOTIVO")
    sexo_idade_input = st.text_input("👨 SEXO/IDADE")
    localidade = st.text_input("📍 LOCALIDADE")
    morada = st.text_input("🏠 MORADA")
    # Multiselect com busca facilitada (sem acentos)
    meios_sel = st.multiselect("🚒 MEIOS", options=lista_meios)
    ops_sel_limpos = st.multiselect("👨🏻‍🚒 OPERACIONAIS (Escreva sem acentos)", options=lista_para_selecao)
    
    outros_meios = st.text_input("🚨 OUTROS MEIOS", value="NENHUM")
    
    submit = st.form_submit_button("ENVIAR", use_container_width=True)

if submit:
    # Validação simples
    if not (nr_ocorrencia and hora_input and motivo and localidade and ops_sel_limpos):
        st.error("⚠️ Por favor, preencha os campos obrigatórios!")
    else:
        # 1. Correção da Hora
        hora_corrigida = hora_input.replace(".", ":")
        
        # 2. Correção de Sexo/Idade automático
        val_sexo = sexo_idade_input.strip().upper()
        if val_sexo.startswith("F"):
            sexo_final = val_sexo.replace("F", "FEMININO", 1)
        elif val_sexo.startswith("M"):
            sexo_final = val_sexo.replace("M", "MASCULINO", 1)
        else:
            sexo_final = val_sexo

        # 3. Aplicar Corretor de Erros (Sedureze, etc.)
        motivo_f = corretor_inteligente(motivo)
        localidade_f = corretor_inteligente(localidade)
        morada_f = corretor_inteligente(morada)

        # 4. Recuperar nomes com acentos originais para o envio
        ops_com_acentos = [mapa_pessoal[nome_limpo] for nome_limpo in ops_sel_limpos]
        ops_txt = ", ".join(ops_com_acentos).upper()
        meios_txt = ", ".join(meios_sel).upper()

        # 5. Montagem da Mensagem Final
        texto_final = (
            f"📕 **OCORRENCIA Nº** ▶️ {nr_ocorrencia.upper()}\n"
            f"🕜 **HORA** ▶️ {hora_corrigida}\n"
            f"🦺 **MOTIVO** ▶️ {motivo_f}\n"
            f"👨 **SEXO/IDADE** ▶️ {sexo_final}\n"
            f"📍 **LOCALIDADE** ▶️ {localidade_f}\n"
            f"🏠 **MORADA** ▶️ {morada_f}\n"
            f"🚒 **MEIOS** ▶️ {meios_txt}\n"
            f"👨🏻‍🚒 **OPERACIONAIS** ▶️ {ops_txt}\n"
            f"🚨 **OUTROS MEIOS** ▶️ {outros_meios.upper()}"
        )

        # 6. Envio para Discord
        try:
            # Enviamos o dicionário JSON que preserva caracteres UTF-8
            response = requests.post(DISCORD_WEBHOOK_URL, json={"content": texto_final})
            if response.status_code == 204:
                st.success("✅ Ocorrência enviada com sucesso!")
            else:
                st.error(f"❌ Erro no Discord (Status: {response.status_code})")
        except Exception as e:
            st.error(f"❌ Erro de ligação: {e}")

st.caption("Sistema de Gestão de Ocorrências BVI - Janeiro-2026")


import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import re

# ================= LISTAS DE REFERÊNCIA =================
ESTADOS_BR = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", 
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

OPCOES_ESCOLARIDADE = [
    "Selecione...",
    "Ensino Fundamental incompleto",
    "Ensino Fundamental completo",
    "Ensino Médio incompleto",
    "Ensino Médio completo",
    "Ensino Superior incompleto",
    "Ensino Superior completo"
]

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("Controle_Tokens").worksheet("Formulario_Inicial")

try:
    planilha_triagem = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão com a planilha: {e}")
    st.stop()

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]

def enviar_email_triagem(dados):
    assunto = f"Novo Formulário Inicial - {dados['Nome']}"
    corpo = "Um novo formulário de triagem foi preenchido.\n\n"
    for chave, valor in dados.items():
        corpo += f"{chave}: {valor}\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# ================= FUNÇÕES DE APOIO =================
def buscar_cep(cep_input):
    cep_limpo = re.sub(r'\D', '', cep_input)
    if len(cep_limpo) == 8:
        try:
            r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
            if r.status_code == 200:
                dados = r.json()
                if "erro" not in dados:
                    return dados
        except:
            return None
    return None

def aplicar_mascaras():
    if "cpf_key" in st.session_state and st.session_state.cpf_key:
        nums = re.sub(r'\D', '', st.session_state.cpf_key)
        if len(nums) == 11:
            st.session_state.cpf_key = f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    
    if "tel_key" in st.session_state and st.session_state.tel_key:
        nums = re.sub(r'\D', '', st.session_state.tel_key)
        if len(nums) == 11:
            st.session_state.tel_key = f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
        elif len(nums) == 10:
            st.session_state.tel_key = f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"

    if "nasc_key" in st.session_state and st.session_state.nasc_key:
        nums = re.sub(r'\D', '', st.session_state.nasc_key)
        if len(nums) == 8:
            st.session_state.nasc_key = f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"

# ================= INTERFACE =================
st.set_page_config(page_title="Formulário Inicial", layout="centered")

st.markdown("""
    <style>
    .stButton > button {
        background-color: #0047AB !important;
        color: white !important;
        border: none !important;
        padding: 0.7rem 2rem !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

if "enviado" not in st.session_state:
    st.session_state.enviado = False

st.markdown("<h1 style='text-align: center;'>Clínica de Psicologia e Psicanálise Bruna Ligoski</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #555;'>Formulário Inicial - Avaliação Neuropsicológica Adulto</h4>", unsafe_allow_html=True)

if st.session_state.enviado:
    st.success("Formulário enviado com sucesso! Agradecemos o preenchimento.")
    st.stop()

st.divider()

# --- LGPD ---
st.markdown("<h3 style='text-align: center;'>Termo de Consentimento para Tratamento de Dados Pessoais</h3>", unsafe_allow_html=True)
termo_html = """
<div style="border: 1px solid white; border-radius: 10px; padding: 20px; margin-top: 10px; margin-bottom: 20px; text-align: justify;">
Em conformidade com a Lei nº 13.709/2018 – Lei Geral de Proteção de Dados Pessoais (LGPD), autorizo o uso dos meus dados pessoais informados neste formulário para as finalidades específicas de construção do laudo de Avaliação Neuropsicológica e em caso de certificação da atividade do conveniado junto ao seu convênio, se neste caso existir.<br><br>
Meus dados serão armazenados e utilizados de forma segura e sigilosa, exclusivamente pela Clínica de Psicologia e Psicanálise Bruna Ligoski, respeitando a legislação vigente.<br><br>
Estou ciente de que posso solicitar a qualquer momento o acesso, correção ou exclusão dos meus dados por meio do contato de e-mail psicologabrunaligoski@gmail.com.
</div>
"""
st.markdown(termo_html, unsafe_allow_html=True)

consentimento = st.radio("Marcando a opção 'Sim' a seguir, você autoriza o tratamento dos seus dados.", ["Não", "Sim"], index=0, horizontal=True)

if consentimento == "Não":
    st.warning("⚠️ É necessário aceitar os termos para prosseguir.")
    st.stop()

st.divider()

# --- DADOS PESSOAIS ---
st.subheader("Dados Pessoais")
nome = st.text_input("Nome Completo *")

col1, col2 = st.columns(2)
with col1:
    cpf = st.text_input("CPF *", key="cpf_key", on_change=aplicar_mascaras, max_chars=14, placeholder="000.000.000-00")
    email_paciente = st.text_input("E-mail *")
with col2:
    telefone = st.text_input("Telefone (WhatsApp) *", key="tel_key", on_change=aplicar_mascaras, max_chars=15, placeholder="(00) 00000-0000")
    nascimento = st.text_input("Data de Nascimento *", key="nasc_key", on_change=aplicar_mascaras, max_chars=10, placeholder="00/00/0000")

st.divider()

# --- ENDEREÇO ---
st.subheader("Endereço")
cep_input = st.text_input("CEP *", max_chars=10, placeholder="00000-000")

log_auto, bairro_auto, cid_auto, uf_auto = "", "", "", "SC" # SC padrão se nada for achado

if cep_input:
    dados_cep = buscar_cep(cep_input)
    if dados_cep:
        log_auto = dados_cep.get("logradouro", "")
        bairro_auto = dados_cep.get("bairro", "")
        cid_auto = dados_cep.get("localidade", "")
        uf_auto = dados_cep.get("uf", "")

rua = st.text_input("Logradouro (Rua/Avenida) *", value=log_auto)
comp = st.text_input("Número e Complemento *")

col3, col4 = st.columns(2)
with col3:
    bairro_f = st.text_input("Bairro *", value=bairro_auto)
    cidade_f = st.text_input("Cidade *", value=cid_auto)
with col4:
    # Busca automática do Estado com Selectbox
    idx_uf = ESTADOS_BR.index(uf_auto) if uf_auto in ESTADOS_BR else 0
    uf_f = st.selectbox("Estado (UF) *", ESTADOS_BR, index=idx_uf)

st.divider()

# --- COMPLEMENTARES ---
st.subheader("Informações Complementares")
escolaridade = st.selectbox("Escolaridade *", OPCOES_ESCOLARIDADE)
profissao = st.text_input("Profissão *")
encaminhamento = st.text_input("Possui encaminhamento? (Informe o solicitante) *")
demanda = st.text_area("Descreva sua demanda (motivo da avaliação) *", height=100)

if st.button("Enviar Formulário"):
    # Validação
    if escolaridade == "Selecione..." or any(not str(v).strip() for v in [nome, cpf, email_paciente, telefone, nascimento, cep_input, rua, comp, bairro_f, cidade_f, profissao, encaminhamento, demanda]):
        st.error("Por favor, preencha todos os campos obrigatórios (*).")
    else:
        dados_finais = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Consentimento": consentimento,
            "Nome": nome,
            "CPF": cpf,
            "E-mail": email_paciente,
            "Telefone": telefone,
            "Nascimento": nascimento,
            "CEP": cep_input,
            "Endereço": f"{rua}, {comp} - {bairro_f}. {cidade_f}/{uf_f}",
            "Escolaridade": escolaridade,
            "Profissão": profissao,
            "Encaminhamento": encaminhamento,
            "Demanda": demanda
        }
        
        if enviar_email_triagem(dados_finais):
            try:
                planilha_triagem.append_row(list(dados_finais.values()))
                st.session_state.enviado = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        else:
            st.error("Erro no envio do e-mail. Tente novamente.")

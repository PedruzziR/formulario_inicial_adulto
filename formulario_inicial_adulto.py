import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

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
    # Abre a planilha central e acessa a aba específica de triagem
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
    assunto = f"Novo Formulário Inicial - {dados['Nome Completo']}"
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

# ================= FUNÇÃO BUSCA CEP =================
def buscar_cep(cep):
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) == 8:
        try:
            r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
            if r.status_code == 200:
                return r.json()
        except:
            return None
    return None

# ================= INTERFACE STREAMLIT =================
st.set_page_config(page_title="Formulário Inicial", layout="centered")

# Estilização
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
st.subheader("Termo de Consentimento para Tratamento de Dados Pessoais")

termo_lgpd = """
Em conformidade com a Lei nº 13.709/2018 – Lei Geral de Proteção de Dados Pessoais (LGPD), autorizo o uso dos meus dados pessoais informados neste formulário para as finalidades específicas de construção do laudo de Avaliação Neuropsicológica e em caso de certificação da atividade do conveniado junto ao seu convênio, se neste caso existir.

Meus dados serão armazenados e utilizados de forma segura e sigilosa, exclusivamente pela Clínica de Psicologia e Psicanálise Bruna Ligoski, respeitando a legislação vigente. 

Estou ciente de que posso solicitar a qualquer momento o acesso, correção ou exclusão dos meus dados por meio do contato de e-mail psicologabrunaligoski@gmail.com.
"""

# st.info cria uma caixa azul de destaque. Se preferir texto normal, troque por st.write(termo_lgpd)
st.info(termo_lgpd)

consentimento = st.radio("Marcando a opção "Sim" a seguir, você autoriza o tratamento dos seusdados pessoais nos termos mencionados acima.", ["Não", "Sim"], index=0, horizontal=True)

if consentimento == "Não":
    st.warning("⚠️ É necessário aceitar os termos para prosseguir.")
    st.stop()

st.divider()

# --- DADOS PESSOAIS ---
nome = st.text_input("Nome Completo *")
col1, col2 = st.columns(2)
with col1:
    cpf = st.text_input("CPF *")
    email_paciente = st.text_input("E-mail *")
with col2:
    telefone = st.text_input("Telefone (WhatsApp) *")
    nascimento = st.text_input("Data de Nascimento *", placeholder="DD/MM/AAAA")

st.divider()

# --- ENDEREÇO ---
st.subheader("Endereço")
cep_input = st.text_input("CEP *", max_chars=9)

logradouro, bairro, cidade, uf = "", "", "", ""

if cep_input:
    dados_cep = buscar_cep(cep_input)
    if dados_cep and "erro" not in dados_cep:
        logradouro = dados_cep.get("logradouro", "")
        bairro = dados_cep.get("bairro", "")
        cidade = dados_cep.get("localidade", "")
        uf = dados_cep.get("uf", "")
        st.success("Endereço localizado!")

rua = st.text_input("Rua/Avenida *", value=logradouro)
complemento = st.text_input("Número e Complemento *")
col3, col4 = st.columns(2)
with col3:
    bairro_field = st.text_input("Bairro *", value=bairro)
    cidade_field = st.text_input("Cidade *", value=cidade)
with col4:
    uf_field = st.text_input("UF *", value=uf)

st.divider()

# --- PROFISSIONAL ---
escolaridade = st.text_input("Escolaridade *")
profissao = st.text_input("Profissão *")
encaminhamento = st.text_input("Possui encaminhamento? (Informe quem solicitou) *")
demanda = st.text_area("Descreva sua demanda (Motivo da avaliação) *")

if st.button("Enviar Informações"):
    campos = [nome, cpf, email_paciente, telefone, nascimento, cep_input, rua, complemento, demanda]
    if any(not c.strip() for c in campos):
        st.error("Por favor, preencha todos os campos obrigatórios.")
    else:
        dados_finais = {
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Nome Completo": nome,
            "CPF": cpf,
            "E-mail": email_paciente,
            "Telefone": telefone,
            "Nascimento": nascimento,
            "CEP": cep_input,
            "Endereço": f"{rua}, {complemento} - {bairro_field}. {cidade_field}/{uf_field}",
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

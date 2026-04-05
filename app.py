import streamlit as st
import pdfplumber
import pandas as pd
import re
import unicodedata
from io import BytesIO

# ==========================================
# CONFIGURAÇÃO DA PÁGINA DO SITE
# ==========================================
st.set_page_config(page_title="Monitoramento Lattes - PPEB", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# CSS EXTREMO: MASCARANDO O STREAMLIT PARA PARECER COM O HUB
# ==========================================
st.markdown("""
    <style>
    /* 1. Esconde os elementos nativos irritantes do Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 2. Tira o espaço gigante em branco que o Streamlit deixa no topo */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 1600px;
    }

    /* 3. Cor de fundo idêntica ao Hub */
    .stApp {
        background-color: #f4f7f6 !important;
    }

    /* 4. CABEÇALHO FALSO (Idêntico ao do HTML do nosso Hub) */
    .hub-header {
        background-color: #1c1f6b;
        color: white;
        padding: 15px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-left: -5rem;  /* Estica para as bordas da tela */
        margin-right: -5rem; /* Estica para as bordas da tela */
        margin-bottom: 30px;
    }
    .hub-header h2 {
        color: white !important;
        margin: 0;
        font-size: 20px;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    .btn-voltar {
        background: transparent;
        border: 1px solid white;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 13px;
        transition: 0.3s;
    }
    .btn-voltar:hover {
        background-color: white;
        color: #1c1f6b;
    }

    /* 5. Títulos internos em Azul PPEB */
    h1, h2, h3 {
        color: #2d3194 !important;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    /* 6. Botão Laranja (Excel e Ações) */
    .stDownloadButton>button, .stButton>button {
        background-color: #f57017 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 10px rgba(245, 112, 23, 0.3) !important;
        width: 100%;
        transition: 0.3s;
    }
    .stDownloadButton>button:hover, .stButton>button:hover {
        background-color: #d95e0f !important;
        transform: translateY(-2px);
    }

    /* 7. Caixas de Upload e Tabelas com estilo de Card */
    .stDataFrame {
        background-color: white;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .stFileUploader {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 4px solid #f57017;
    }
    .stFileUploader>div>div>div>button {
        background-color: #2d3194 !important;
        color: white !important;
        border-radius: 6px !important;
    }
    </style>

    <div class="hub-header">
        <h2>Monitoramento Analítico Lattes</h2>
        <a href="LINK_DO_SEU_HUB_AQUI.html" target="_self" class="btn-voltar">← Voltar ao Hub</a>
    </div>
    """, unsafe_allow_html=True)

st.write("Faça o upload dos currículos em formato **PDF** para gerar o relatório automatizado de produção discente e atualização de cadastro.")

# ==========================================
# FUNÇÕES DE LIMPEZA E CONTAGEM (O RESTO DO SEU CÓDIGO CONTINUA AQUI...)
# ==========================================
def limpar_texto(texto):
def limpar_texto(texto):
    if not texto: return ""
    texto = str(texto).upper()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return " ".join(texto.split())

def contar_producao(texto_base, titulo_secao, lista_freios, ano_ingresso):
    contagem = 0
    if titulo_secao in texto_base:
        bloco = texto_base.split(titulo_secao)[1]
        posicao_corte = len(bloco)
        for freio in lista_freios:
            pos = bloco.find(freio)
            if pos != -1 and pos < posicao_corte:
                posicao_corte = pos
        bloco_isolado = bloco[:posicao_corte]
        anos_encontrados = re.findall(r'\b(20\d{2})\b', bloco_isolado)
        for ano in anos_encontrados:
            if int(ano) >= ano_ingresso and ano_ingresso != 2099:
                contagem += 1
    return contagem

# ==========================================
# BASE DE DADOS COMPLETA PPEB (2024-2026) COM LINHAS DE PESQUISA
# ==========================================
banco_de_dados = {
    # ESTUDANTE INTERNACIONAL / ADICIONAIS
    "OLUWATOYOSI HELEN KUSHINA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},

    # MESTRADO 2025
    "ADRIANNY COSTA DA SILVA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "AMANDA XAVIER DA COSTA CAZARES": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "CARLA GABRIELLA MORAES DE MELO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "JESSICA SOUSA PEREIRA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "JHULLY CRISTY SILVA MORAES": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "LETICIA RAQUEL NOGUEIRA PALHETA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "LILIANE BARROS FIUZA DE MELLO CASSIANO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "LORENA TEIXEIRA DA SILVA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "PRISCILLA BRITO GUERRA SCHIOCHET": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "PRISCILA BRITO GUERRA SCHIOCHET": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Currículo da Educação Básica"}, 
    "ANTONIO EDENILSON ANJOS DAS NEVES": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "BILLY DE ALMEIDA ANDRADE FILHO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "CARLA BRENDA DIAS SOUZA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "CLARA LUCIA PINHEIRO DE ARAUJO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "ELIETE CRUZ SANTOS": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "JAMILLE MIRANDA DO NASCIMENTO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "JOAO VITOR DE JESUS RIBEIRO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "LUANA SANTOS NASCIMENTO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MARIA LUANNA LIMA OLIVEIRA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "SANDRA HELENA DA SILVA COUTINHO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "VANESSA SILVA DE MELO": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "ANA LUISA BAIA MAIA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "CYNTHIA LORENNA LOBATO DA SILVA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "DANIEL DE SOUZA SARAIVA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "JESSICA MARCELA PEDREIRA DA SILVA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "LORENA CRISTINA GONZAGA PEREIRA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "THAMYRES POLLYANA DA CRUZ TEIXEIRA": {"Nivel": "Mestrado", "Ano": 2025, "Linha": "História da Educação Básica"},

    # DOUTORADO 2024
    "ALINE BRANDAO DE MORAES DE AZEVEDO": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "ELANE CRISTINA PINHEIRO MONTEIRO": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "IRACEMA DOS SANTOS TELES": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "JULIAN KARLA DINIZ NERIS": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "LYANNY ARAUJO FRANCES": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "RAFAEL SILVA COSTA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Currículo da Educação Básica"},
    "ALINY CRISTINA SILVA ALVES": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "EDUARDA DE ASSUNCAO PACHECO": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "JAQUELINE DO NASCIMENTO RODRIGUES PINTO": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MARCELO WILSON FERREIRA PACHECO": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "REGINALDO CELIO ALMEIDA DE OLIVEIRA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "RODRIGO CARDOSO DA SILVA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "ROSILENE FERREIRA DE ALMEIDA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "SARA CORREA DIAS": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "VIVIAN DE LIMA CABRAL": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "ADRIAN SOUZA DOS SANTOS": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "História da Educação"},
    "DOUGLAS DE OLIVEIRA E OLIVEIRA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "História da Educação"},
    "NEIDE ANDRADE DA SILVA": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "História da Educação"},
    "THAIS PIMENTA PIMENTEL": {"Nivel": "Doutorado", "Ano": 2024, "Linha": "História da Educação"},

    # DOUTORADO 2025
    "AMANDA JESSICA COELHO MELO": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "BIANCA MORAIS CARNEIRO": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "CARLOS AFONSO FERREIRA DOS SANTOS": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "MARGARIDA MARIA DE ALMEIDA RODRIGUES DA SILVA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "SUELLEN FERREIRA BARBOSA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Currículo da Educação Básica"},
    "ADRIANA DE NAZARE RIBEIRO DIAS PINTO": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "DILCELIA RODRIGUES ALVES": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "FAHID DA COSTA KEMIL": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "JOELTON DA SILVA PASSINHO": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "LICIANE DE SOUZA E SOUZA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MAIRA JESSICA NOGUEIRA DA SILVA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MARCIO FERNANDO DUARTE PINHEIRO": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MARIA DO SOCORRO RODRIGUES ROCHA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "MICHELLE COSTA TAPAJOS": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "RAIMUNDO NONATO LEITE DE OLIVEIRA": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "Gestão e Organização do Trab. Pedagógico"},
    "CAMILA ANDREA DE JESUS SANTOS": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "CARLENE SIBELI SODRE DAMASCENO NAHUM": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "EDILENE DE ARAUJO NERES": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "LANNA KARINA ARAUJO DE LIMA RODRIGUES": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "MAIRA REGINA FARIAS MACIEL": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},
    "SUZAN DO SOCORRO BRITO DE LOPES": {"Nivel": "Doutorado", "Ano": 2025, "Linha": "História da Educação Básica"},

    # TURMAS 2026 (Linha a definir)
    "ALINE BAIA DOS SANTOS": {"Nivel": "Mestrado", "Ano": 2026}, "BIANCA PORTILHO GUIMARAES": {"Nivel": "Mestrado", "Ano": 2026}, "DENISE SENA DA SILVA": {"Nivel": "Mestrado", "Ano": 2026}, "GABRIEL DIAS FERNANDES": {"Nivel": "Mestrado", "Ano": 2026}, "GLENDA KELLY RIBEIRO DA SILVA DE AVILA": {"Nivel": "Mestrado", "Ano": 2026}, "JANE GARETE SARAIVA TEIXEIRA": {"Nivel": "Mestrado", "Ano": 2026}, "JULIANA REBELO ELESBAO": {"Nivel": "Mestrado", "Ano": 2026}, "THAIANE DOS SANTOS SILVA": {"Nivel": "Mestrado", "Ano": 2026}, "ADRIA JUNNYELLY MARIA SILVA CUNHA": {"Nivel": "Mestrado", "Ano": 2026}, "ALAN LIMA DE SIQUEIRA": {"Nivel": "Mestrado", "Ano": 2026}, "ALBERTO FERREIRA DE ANDRADE JUNIOR": {"Nivel": "Mestrado", "Ano": 2026}, "ELIZAMA SILVA PEREIRA": {"Nivel": "Mestrado", "Ano": 2026}, "IAGO QUINTO BRANDAO": {"Nivel": "Mestrado", "Ano": 2026}, "LUANA PATRICIA PAIXAO MACIEL": {"Nivel": "Mestrado", "Ano": 2026}, "RITA DE CASSIA SANTANA DE MATOS": {"Nivel": "Mestrado", "Ano": 2026}, "ANDRESSA RAFAELLA CRUZ DE MORAES": {"Nivel": "Mestrado", "Ano": 2026}, "ARIEL COSTA WANZELER": {"Nivel": "Mestrado", "Ano": 2026}, "JHANIELLY GONCALVES BARBOSA": {"Nivel": "Mestrado", "Ano": 2026}, "KEWIN JULYANA ROCHA LOPES": {"Nivel": "Mestrado", "Ano": 2026}, "LARISSA MEDEIROS BRAGANCA SANTOS": {"Nivel": "Mestrado", "Ano": 2026}, "MARCELIA PROTAZIO DOS SANTOS OLIVEIRA": {"Nivel": "Mestrado", "Ano": 2026}, "RODRIGO MIRA DO NASCIMENTO": {"Nivel": "Mestrado", "Ano": 2026}, "SANDRA HELENA RABELLO LEAO": {"Nivel": "Mestrado", "Ano": 2026}, "YARA ISRAELLE LOPES TORRES": {"Nivel": "Mestrado", "Ano": 2026},
    "ANTONIO MATHEUS DO ROSARIO CORREA": {"Nivel": "Doutorado", "Ano": 2026}, "ELANY CRISTINA BARROS DA SILVA": {"Nivel": "Doutorado", "Ano": 2026}, "LUISETE DO ESPIRITO SANTO SOUSA": {"Nivel": "Doutorado", "Ano": 2026}, "MILENA FARIAS E SILVA": {"Nivel": "Doutorado", "Ano": 2026}, "PEDRO CABRAL DA COSTA": {"Nivel": "Doutorado", "Ano": 2026}, "PEDRO VICTOR DA SILVA LEITE": {"Nivel": "Doutorado", "Ano": 2026}, "FRANCINEIDE DA COSTA SOUSA": {"Nivel": "Doutorado", "Ano": 2026}, "GISELE CRISTIANE ANDRADE ALMEIDA": {"Nivel": "Doutorado", "Ano": 2026}, "KELLE DO ROSARIO BRAGA SILVA": {"Nivel": "Doutorado", "Ano": 2026}, "KESIA SILVA DA COSTA": {"Nivel": "Doutorado", "Ano": 2026}, "MHIRLLA DE CASSIA GONCALVES DA COSTA": {"Nivel": "Doutorado", "Ano": 2026}, "NERIVALDO LOPES DE OLIVEIRA": {"Nivel": "Doutorado", "Ano": 2026}, "SHEILA DE NAZARE SILVA FERREIRA": {"Nivel": "Doutorado", "Ano": 2026}, "SIMONE JOSELLE XAVIER DA SILVA": {"Nivel": "Doutorado", "Ano": 2026}, "ADRIANE BARBOSA DE ALMEIDA": {"Nivel": "Doutorado", "Ano": 2026}, "CINTHIA MOTA MEDEIROS DA SILVA": {"Nivel": "Doutorado", "Ano": 2026}, "GISLAYNE CARVALHO PIRES": {"Nivel": "Doutorado", "Ano": 2026}, "JAMYLLE EMILLY PAZ MAIA": {"Nivel": "Doutorado", "Ano": 2026}, "MARCUS VINICIUS DA ROSA RIBEIRO": {"Nivel": "Doutorado", "Ano": 2026}
}

# ==========================================
# LISTAS DE CONTROLE
# ==========================================
orientadores_ppeb = ["AMELIA MARIA ARAUJO MESQUITA", "ANDRIO ALVES GATINHO", "CLARICE NASCIMENTO DE MELO", "DANIELE DOROTEIA ROCHA DE LIMA", "DINAIR LEAL DA HORA", "DORIEDSON DO SOCORRO RODRIGUES", "EMINA MARCIA NERY DOS SANTOS", "ERINALDO VICENTE CAVALCANTE", "FABRICIO AARAO FREIRE CARVALHO", "GENYLTON ODILON REGO DA ROCHA", "IRLANDA DO SOCORRO DE OLIVEIRA MILEO", "JOAO PAULO DA CONCEICAO ALVES", "JOSE BITTENCOURT DA SILVA", "LIVIA SOUSA DA SILVA", "MARCIO ANTONIO RAIOL DOS SANTOS", "MARIA DO SOCORRO DA COSTA COELHO", "MARIA DE FATIMA MATOS DE SOUZA", "MARIA JOSE AVIZ DO ROSARIO", "NEIDE MARIA FERNANDES RODRIGUES DE SOUSA", "NEY CRISTINA MONTEIRO DE OLIVEIRA", "RAIMUNDO ALBERTO DE FIGUEIREDO DAMASCENO", "RENATO PINHEIRO DA COSTA", "RONALDO MARCOS DE LIMA ARAUJO", "VIVIAN DA SILVA LOBATO", "WILLIAN LAZARETTI DA CONCEICAO", "WILMA DE NAZARE BAIA COELHO"]

termos_genericos = ["GRUPO DE PESQUISA", "NUCLEO DE PESQUISA", "GRUPO DE ESTUDOS", "NUCLEO DE ESTUDOS", "LABORATORIO", "MEMBRO", "INTEGRANTE", "PESQUISADOR"]
grupos_especificos = ["GEFOR", "DIFERE", "DIFERENCA E EDUCACAO", "GESTAMAZON", "ESTADO E EDUCACAO NA AMAZONIA", "GEPTE", "TRABALHO E EDUCACAO", "GEPEDA", "EDUCACAO E DESENVOLVIMENTO DA AMAZONIA", "GEPHE", "HISTORIA DA EDUCACAO", "TEIA AMAZONIDA", "TERRITORIOS, EDUCACAO INTEGRAL E CIDADANIA", "REPAMFEH", "REDE PANAMAZONICA PARA LA FORMACION Y ENSENANZA DE LA HISTORIA", "HISTEDBR", "HISTORIA, SOCIEDADE E EDUCACAO NO BRASIL", "GEPEBATO", "POLITICAS EDUCACIONAIS NO BAIXO TOCANTINS", "GEPPEB", "POLITICAS PUBLICAS PARA A EDUCACAO BASICA", "EDUJUS", "EDUCACAO E JUSTICA SOCIAL", "GPECCIP", "COMPLEXIDADE, CURRICULO POS-CRITICO", "INCLUDERE", "CURRICULO E FORMACAO DE PROFESSORES NA PERSPECTIVA DA INCLUSAO", "GPHELRA", "HISTORIA, EDUCACAO E LINGUAGEM NA REGIAO AMAZONICA", "GERA", "RELACAO ETNICO-RACIAIS", "LEPED", "EDUCACAO E DESIGUALDADES", "EDUCACAO E JUSTICA", "INTERPRETACAO DO TEMPO", "ENSINO, MEMORIA, NARRATIVA E POLITICA", "TRABALHO, EDUCACAO E FORMACAO HUMANA", "EDUCACAO E DIREITOS HUMANOS", "PRATICAS PEDAGOGICAS PARA O ENSINO NA EDUCACAO BASICA", "MEMORIA E HISTORIA DA EDUCACAO"]
palavras_chave_grupos = termos_genericos + grupos_especificos

freios_gerais = ["TEXTOS EM JORNAIS", "TRABALHOS COMPLETOS PUBLICADOS EM ANAIS", "RESUMOS EXPANDIDOS", "RESUMOS PUBLICADOS", "ARTIGOS ACEITOS", "APRESENTACOES DE TRABALHO", "OUTRAS PRODUCOES", "PRODUCAO TECNICA", "PARTICIPACAO EM BANCAS", "EVENTOS", "PATENTES", "OUTRAS PARTICIPACOES", "BANCA DE TRABALHOS"]

# ==========================================
# INTERFACE DO SITE E LÓGICA PRINCIPAL
# ==========================================
arquivos_upados = st.file_uploader("Arraste e solte os PDFs aqui", type=["pdf"], accept_multiple_files=True)

if arquivos_upados:
    st.info(f"⏳ Processando {len(arquivos_upados)} currículo(s). Por favor, aguarde...")
    barra_progresso = st.progress(0)
    resultados = []
    
    for i, arquivo in enumerate(arquivos_upados):
        try:
            texto_pdf = ""
            with pdfplumber.open(arquivo) as pdf:
                for pagina in pdf.pages:
                    texto_pdf += pagina.extract_text() + "\n"
            
            texto_upper = limpar_texto(texto_pdf)
            texto_linha_unica = " ".join(texto_upper.split()) 
            
            # --- DATA DE ATUALIZAÇÃO ---
            data_atualizacao = "Não informada"
            match_data = re.search(r"ULTIMA ATUALIZACAO DO CURRICULO EM\s*(\d{2}/\d{2}/\d{4})", texto_upper)
            if match_data: data_atualizacao = match_data.group(1)
            
            # --- LIMPEZA DE NOME DE ARQUIVO ---
            nome_limpo_arq = re.sub(r'(?i)curr[ií]culo do sistema de curr[ií]culos lattes[\s-]*\(?', '', arquivo.name)
            nome_limpo_arq = nome_limpo_arq.replace('.pdf', '').replace(')', '').strip()
            nome_lattes = limpar_texto(nome_limpo_arq)
            
            info = banco_de_dados.get(nome_lattes)
            if not info: 
                for k, v in banco_de_dados.items():
                    if k in nome_lattes or k in texto_linha_unica[:300]: 
                        info = v
                        nome_lattes = k
                        break
            
            nivel = info['Nivel'] if info else "Não cadastrado"
            ano_ref = info['Ano'] if info else 2099
            linha_pesquisa = info.get('Linha', 'Não informada') if info else "Não cadastrado" 

            # --- GRUPO DE PESQUISA ---
            status_grupo = "❌ Não"
            resumo_texto = texto_linha_unica[:3000] 
            for termo in palavras_chave_grupos:
                if limpar_texto(termo) in resumo_texto:
                    status_grupo = "✅ Sim"
                    break

            # --- FORMAÇÃO E ORIENTADOR ---
            status_form = "❌ Desatualizada"
            orientador = "Não informado"
            titulo = "Não informado"

            match_secao_formacao = re.search(r"FORMACAO ACADEMICA/TITULACAO(.*?)(?:FORMACAO COMPLEMENTAR|ATUACAO PROFISSIONAL|PROJETOS DE PESQUISA)", texto_upper, re.DOTALL)
            if match_secao_formacao:
                bloco_formacao = match_secao_formacao.group(1)
                if nivel.upper() in bloco_formacao:
                    status_form = "✅ Atualizada"
                    match_t = re.search(r"TITULO:\s*(.*?)(?=ORIENTADOR|BOLSISTA|\n\d{4})", bloco_formacao, re.DOTALL)
                    if match_t: titulo = match_t.group(1).replace('\n', ' ').strip(' .:,')
                    match_o = re.search(r"ORIENTADOR[A]?:\s*(.*?)(?=\n|\.|$)", bloco_formacao)
                    if match_o: orientador = match_o.group(1).replace('\n', ' ').strip(' .:,')

            # --- PROJETOS DE PESQUISA ---
            status_projeto = "❌ Sem projeto"
            match_secao_proj = re.search(r"PROJETOS DE PESQUISA(.*?)(?:AREAS DE ATUACAO|IDIOMAS|PREMIOS|PRODUCOES|ARTIGOS)", texto_upper, re.DOTALL)
            if match_secao_proj:
                bloco_proj = match_secao_proj.group(1)
                if "EM ANDAMENTO" in bloco_proj or "ATUAL" in bloco_proj:
                    status_projeto = "✅ Possui projeto"

            # --- CONTAGEM DE PRODUÇÃO ---
            freios_artigos = ["LIVROS PUBLICADOS", "LIVROS E CAPITULOS", "CAPITULOS DE LIVROS"] + freios_gerais
            artigos_cont = contar_producao(texto_linha_unica, "ARTIGOS COMPLETOS PUBLICADOS EM PERIODICOS", freios_artigos, ano_ref)
            
            freios_livros = ["CAPITULOS DE LIVROS PUBLICADOS", "CAPITULOS DE LIVROS"] + freios_gerais
            livros_cont = 0
            if "LIVROS PUBLICADOS/ORGANIZADOS OU EDICOES" in texto_linha_unica:
                livros_cont = contar_producao(texto_linha_unica, "LIVROS PUBLICADOS/ORGANIZADOS OU EDICOES", freios_livros, ano_ref)
            elif "LIVROS PUBLICADOS" in texto_linha_unica:
                livros_cont = contar_producao(texto_linha_unica, "LIVROS PUBLICADOS", freios_livros, ano_ref)
                
            freios_capitulos = freios_gerais
            capitulos_cont = contar_producao(texto_linha_unica, "CAPITULOS DE LIVROS PUBLICADOS", freios_capitulos, ano_ref)

            resultados.append({
                'Nome': nome_lattes.title(), 'Nível': nivel, 'Ano Ingresso': ano_ref, 'Linha de Pesquisa': linha_pesquisa,
                'Última Atualização': data_atualizacao, 'Formação': status_form, 'Projeto Atual?': status_projeto,
                'Grupo no Resumo?': status_grupo, 'Orientador(a)': orientador, 'Título da Pesquisa': titulo.title(), 
                'Artigos (No Curso)': artigos_cont, 'Livros (No Curso)': livros_cont, 'Capítulos (No Curso)': capitulos_cont
            })
            
            barra_progresso.progress((i + 1) / len(arquivos_upados))

        except Exception as e:
            st.error(f"Erro ao ler o arquivo {arquivo.name}: {e}")

    # ==========================================
    # GERAÇÃO DA TABELA E DOWNLOAD
    # ==========================================
    if resultados:
        df = pd.DataFrame(resultados)
        st.success("✅ Relatório gerado com sucesso!")
        st.dataframe(df)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório PPEB')
        
        st.download_button(
            label="📥 Descarregar Planilha Excel",
            data=output.getvalue(),
            file_name="Relatorio_Lattes_PPEB.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

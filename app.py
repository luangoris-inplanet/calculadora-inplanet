import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import math
import os
import plotly.express as px
import plotly.graph_objects as go
import requests
import re
from fpdf import FPDF
import tempfile

# ==========================================
# CONFIGURAÇÃO DA INTERFACE E FATORES ESG
# ==========================================
st.set_page_config(page_title="Simulador InPlanet ESG", page_icon="🌿", layout="wide")

# Fatores de Emissão Oficiais (kgCO2eq por L ou m³)
FATORES_EMISSAO = {
    'Diesel B15': 2.70831,
    'Biometano': 0.30620,
    'GNV': 2.83115
}

# Consumo Médio Homologado (km por L ou m³)
CONSUMO_MEDIO = {
    'Diesel B15': 2.02,
    'Biometano': 1.90,
    'GNV': 1.90
}

# ==========================================
# FUNÇÕES GERAIS (LEITOR DE LINKS E PDF)
# ==========================================
def extrair_coordenadas(entrada):
    if not entrada:
        return None, None
    entrada = entrada.strip()
    try:
        if "maps.app.goo.gl" in entrada or "goo.gl/maps" in entrada:
            r = requests.get(entrada, timeout=5)
            entrada = r.url
        match_url = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", entrada)
        if match_url:
            return float(match_url.group(1)), float(match_url.group(2))
        match_coord = re.search(r"(-?\d+\.\d+)[\s,]+(-?\d+\.\d+)", entrada)
        if match_coord:
            return float(match_coord.group(1)), float(match_coord.group(2))
    except:
        pass
    return None, None

def gerar_pdf(pedreira_nome, area, dose, toneladas, cap_caminhao, viagens, dist_ida_volta, dist_total, litros, frete_ton, custo_po, subsidio, custo_frete, custo_final, frete_ha, tipo_frete):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=80, y=10, w=50)
        pdf.ln(25)
    else:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Proposta Comercial - InPlanet", ln=True, align='C')
        pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 10, txt="1. Resumo da Operacao Agronomica", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 7, txt=f"Origem do Produto: {pedreira_nome}", ln=True)
    pdf.cell(200, 7, txt=f"Area de Aplicacao: {area} hectares", ln=True)
    pdf.cell(200, 7, txt=f"Dosagem: {dose} ton/ha", ln=True)
    pdf.cell(200, 7, txt=f"Volume Total Necessario: {toneladas:,.0f} toneladas de Remineralizador", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 10, txt="2. Logistica e Transporte Estimado", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 7, txt=f"Modalidade: {tipo_frete}", ln=True)
    pdf.cell(200, 7, txt=f"Capacidade por Caminhao: {cap_caminhao} toneladas", ln=True)
    pdf.cell(200, 7, txt=f"Viagens Necessarias: {viagens} viagens", ln=True)
    pdf.cell(200, 7, txt=f"Distancia por Viagem (Ida + Volta): {dist_ida_volta:,.0f} km", ln=True)
    pdf.cell(200, 7, txt=f"Distancia Total da Frota: {dist_total:,.0f} km rodados", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 10, txt="3. Proposta Financeira (Parceria)", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 7, txt=f"Investimento InPlanet (Remineralizador): R$ {custo_po:,.2f} [100% Custeado pela InPlanet]", ln=True)
    
    texto_frete = f"Custo Estimado do Frete: R$ {custo_frete:,.2f} (Aprox. R$ {frete_ton:,.2f} / ton)"
    if "Frota" in tipo_frete:
        texto_frete += " *Inclui Diesel, Manutencao e Motorista"
        
    pdf.cell(200, 7, txt=texto_frete, ln=True)
    pdf.cell(200, 7, txt=f"Subsidio InPlanet no Frete: - R$ {subsidio:,.2f}", ln=True)
    pdf.ln(3)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(46, 168, 74)
    pdf.cell(200, 8, txt=f"CUSTO FINAL DO PRODUTOR: R$ {custo_final:,.2f}", ln=True)
    pdf.cell(200, 8, txt=f"CUSTO DILUIDO POR HECTARE: R$ {frete_ha:,.2f} / ha", ln=True)
    
    try:
        df_graf = pd.DataFrame({
            'Categoria': ['Remineralizador (InPlanet)', 'Subsidio Frete (InPlanet)', 'Frete (Produtor)'],
            'Valor': [custo_po, subsidio, custo_final]
        })
        fig_pdf = px.pie(df_graf, values='Valor', names='Categoria', hole=0.4, color_discrete_sequence=['#2EA84A', '#82E0AA', '#E67E22'])
        fig_pdf.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
        fig_pdf.update_layout(margin=dict(t=10, b=10, l=10, r=10), width=600, height=400)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
            fig_pdf.write_image(tmp_img.name, engine="kaleido")
            pdf.image(tmp_img.name, x=25, w=160)
    except:
        pass 

    pdf.ln(5)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 4, txt="Documento gerado automaticamente pelo Simulador Comercial InPlanet.", ln=True, align='C')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
    return pdf_bytes

# ==========================================
# 1. BASE DE DADOS COMPLETA (PEDREIRAS E ANTT)
# ==========================================
dados_pedreiras = pd.DataFrame({
    'Mine Name': [
        'Siqueira', 'Esteio (Tozzi-Junqueira)', 'Conquista', 'Pedreira São Franciso', 'Baú Mineração', 
        'Consbrita', 'Quimassa', 'Ecobrix', 'Mineração Barbarense', 'Conquista (Prudente)', 'Constroeste', 
        'Carrascoza', 'Coplan', 'Mandaguari', 'Ekosolos', 'Quibrita', 'Mineração Campo Grande', 
        'Bandeirantes', 'Sozo Britas', 'Fortaleza Caçu', 'Goyaz Britas', 'Expressa', 'Diabásio', 
        'Simoso', 'Pardo', 'Noroeste', 'W&W Britagem', 'Ica', 'Polimix', 'Grupo Autem', 'Piraju', 
        'Noroeste Paulista', 'Minerpal', 'Compensa', 'Gemelli', 'Construbrás I', 'Construbrás II', 
        'Britaminas Fortaleza', 'Ingá', 'Fortaleza Rio Verde', 'Rio Claro'
    ],
    'City': [
        'Paraguaçu Paulista', 'Itaporã', 'Narandiba', 'Porto Franco', 'Caxias', 'Curitibanos', 
        'Limeira', 'Uberlândia', 'Santa Bárbara D\'oeste', 'Presidente Prudente', 'Icém', 'Cravinhos', 
        'Embaúba', 'Mandaguari', 'Paula Freitas', 'Piracicaba', 'Terenos', 'São Carlos', 'Ponte Alta', 
        'Cachoeira Alta', 'Panamá', 'Londrina', 'Lençóis Paulista', 'Mogi-Mirim', 'Santa Cruz do Rio Pardo', 
        'Votuporanga', 'Ituiutaba', 'Ibiporã', 'Campo Grande', 'Jaboticabal', 'Assis', 'Monções', 
        'Palotina', 'Paula Freitas', 'Chiapetta', 'São Luiz Gonzaga', 'Sarandi', 'Portelândia', 
        'Maringá', 'Rio Verde', 'Jataí'
    ],
    'State': [
        'SP', 'MS', 'SP', 'MA', 'MA', 'SC', 'SP', 'MG', 'SP', 'SP', 'SP', 'SP', 'SP', 'PR', 'PR', 
        'SP', 'MS', 'SP', 'SC', 'GO', 'GO', 'PR', 'SP', 'SP', 'SP', 'SP', 'MG', 'PR', 'MS', 'SP', 
        'SP', 'SP', 'PR', 'PR', 'RS', 'RS', 'RS', 'GO', 'PR', 'GO', 'GO'
    ],
    'Lat': [
        -22.41299, -22.08048, -22.40692, -6.34189, -4.86545, -27.28285, -22.56652, -18.91460, 
        -22.72123, -22.12111, -20.34199, -21.33842, -20.98006, -23.54505, -26.21098, -22.73427, 
        -20.43829, -22.01786, -27.48397, -18.76228, -18.17699, -23.30444, -22.60316, -22.43320, 
        -22.89921, -20.42412, -18.97764, -23.26640, -20.44278, -21.25250, -22.66042, -20.84999, 
        -24.28724, -26.21098, -27.92348, -28.40798, -23.44458, -17.43526, -23.47396, -17.87944, -17.93636
    ],
    'Long': [
        -50.57594, -54.79382, -51.52387, -47.39656, -43.36209, -50.58207, -47.39738, -48.27533, 
        -47.43294, -51.39295, -49.19494, -47.73282, -48.83285, -51.67145, -50.93141, -47.64801, 
        -54.86518, -47.88637, -50.37684, -50.94365, -49.35394, -51.16952, -48.80409, -46.95920, 
        -49.63586, -49.97852, -49.46435, -51.05267, -54.64639, -48.32562, -50.41872, -50.09194, 
        -53.84086, -50.93141, -53.94233, -54.96093, -51.87644, -52.61257, -51.95518, -50.70477, -51.65943
    ],
    'Price/ton': [
        50.0, 58.0, 100.0, 70.0, 70.0, 70.0, 70.0, 120.0, 60.0, 90.0, 63.0, 50.0, 52.0, 50.0, 
        50.0, 50.0, 59.76, 60.0, 57.5, 80.0, 80.0, 40.0, 62.5, 90.0, 50.0, 70.0, 70.0, 80.0, 
        50.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 60.0, 45.0, 60.0, 45.0
    ]
})

dados_antt = pd.DataFrame({
    'Modelo': ['LS (6 eixos) - 33t', 'Bi-trem (7 eixos) - 38t', 'Bi-trem (9 eixos) - 50t'],
    'Capacidade_t': [33, 38, 50],
    'Consumo_km_l': [2.5, 2.2, 1.8],
    'Ate_50km': [0.37, 0.35, 0.35],
    'Ate_100km': [0.27, 0.25, 0.26],
    'Acima_100km': [0.24, 0.22, 0.23]
})

dados_pedreiras['Exibicao'] = dados_pedreiras['Mine Name'] + " (" + dados_pedreiras['City'] + " - " + dados_pedreiras['State'] + ")"

if 'pedreira_key' not in st.session_state:
    st.session_state.pedreira_key = dados_pedreiras['Exibicao'].iloc[0]

def auto_selecionar_pedreira(lat, lon):
    distancias = dados_pedreiras.apply(lambda row: geodesic((row['Lat'], row['Long']), (lat, lon)).km, axis=1)
    idx_mais_proxima = distancias.idxmin()
    st.session_state.pedreira_key = dados_pedreiras.loc[idx_mais_proxima, 'Exibicao']

# ==========================================
# INTERFACE E ENTRADAS PRINCIPAIS
# ==========================================
st.title("🌿 Simulador Comercial InPlanet: Logística & Ativos ESG")

# Barra Lateral ESG Global
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("Variáveis Mercado Carbono")
preco_credito_usd = st.sidebar.number_input("Preço do Crédito de Carbono ($/tCDR)", value=300.0)
cotacao_dolar = st.sidebar.number_input("Cotação do Dólar (R$)", value=5.00, step=0.10)
valor_credito_brl = preco_credito_usd * cotacao_dolar
st.sidebar.info(f"**Retorno Carbono:** R$ {valor_credito_brl:,.2f} / tCO2 evitada")

st.markdown("### 📍 Configuração do Destino (Fazenda)")
col_origem, col_destino = st.columns(2)

with col_origem:
    pedreira_selecionada = st.selectbox("Selecione a Pedreira (Origem)", dados_pedreiras['Exibicao'], key='pedreira_key')
    pedreira = dados_pedreiras[dados_pedreiras['Exibicao'] == pedreira_selecionada].iloc[0]
    st.info(f"**Preço do Remineralizador:** R$ {pedreira['Price/ton']:,.2f} / tonelada")

with col_destino:
    input_local = st.text_input("Cole aqui o Link do Google Maps ou as Coordenadas:")
    fazenda_lat, fazenda_lon = -15.7942, -49.2536 
    distancia_ida_km = 150.0
    
    if input_local:
        lat_extraida, lon_extraida = extrair_coordenadas(input_local)
        if lat_extraida and lon_extraida:
            fazenda_lat, fazenda_lon = lat_extraida, lon_extraida
            st.success(f"📍 Fazenda Localizada!")
            st.button("🪄 Auto-Selecionar Pedreira Mais Próxima", on_click=auto_selecionar_pedreira, args=(fazenda_lat, fazenda_lon))
            
            coord_origem = (pedreira['Lat'], pedreira['Long'])
            coord_destino = (fazenda_lat, fazenda_lon)
            distancia_ida_km = geodesic(coord_origem, coord_destino).km * 1.2
            st.success(f"✅ Distância Estimada (Rota + 20%): **{distancia_ida_km:,.1f} km**")

st.markdown("### 🚜 Volume da Operação Agronômica")
col_area, col_dose = st.columns(2)
area_ha = col_area.number_input("Área de Aplicação na Fazenda (Hectares)", value=500.0, step=50.0, min_value=1.0)
dose_t_ha = col_dose.number_input("Dosagem Recomendada (toneladas/hectare)", value=20.0, step=1.0)
toneladas_totais = area_ha * dose_t_ha
st.success(f"**Carga Total Necessária:** {toneladas_totais:,.0f} toneladas de remineralizador.")

distancia_viagem_completa_km = distancia_ida_km * 2

# ==========================================
# DEFINIÇÃO DAS ABAS (MÓDULOS)
# ==========================================
aba_tradicional, aba_esg = st.tabs(["🚚 1. Logística Tradicional", "🌿 2. Módulo Avançado ESG (Biometano)"])

# ------------------------------------------
# ABA 1: LOGÍSTICA TRADICIONAL
# ------------------------------------------
with aba_tradicional:
    st.subheader("Simulação de Frete Comum (Diesel)")
    col_t1, col_t2 = st.columns([1, 2])
    
    with col_t1:
        tipo_frete = st.radio("Responsabilidade do Transporte:", ("Frete Terceirizado (ANTT)", "Frota Própria (Fazendeiro)"), key="tipo_frete_aba1")
        subsidio_frete = st.number_input("Subsídio InPlanet no Frete (R$/ton)", value=0.0, step=5.0, key="subsidio_aba1")
        
        if tipo_frete == "Frete Terceirizado (ANTT)":
            modelo_caminhao = st.selectbox("Modelo do Caminhão (ANTT)", dados_antt['Modelo'])
            caminhao_selecionado = dados_antt[dados_antt['Modelo'] == modelo_caminhao].iloc[0]
            capacidade_caminhao = caminhao_selecionado['Capacidade_t']
            consumo_km_l = caminhao_selecionado['Consumo_km_l']
            tarifa_ton_km = caminhao_selecionado['Ate_50km'] if distancia_ida_km <= 50 else (caminhao_selecionado['Ate_100km'] if distancia_ida_km <= 100 else caminhao_selecionado['Acima_100km'])
            custo_total_frete = toneladas_totais * distancia_viagem_completa_km * tarifa_ton_km
        else:
            preco_diesel = st.number_input("Preço do Diesel (R$/L)", value=6.00)
            capacidade_caminhao = st.number_input("Capacidade do Caminhão (t)", value=35)
            consumo_km_l = st.number_input("Consumo (km/L)", value=2.5)
            custo_manutencao_km = st.number_input("Manutenção/Pneus (R$/km)", value=2.00)
            custo_motorista_viagem = st.number_input("Diária Motorista (R$/Viagem)", value=200.00)
            custo_pedagio_viagem = st.number_input("Pedágio (R$/Viagem)", value=0.00)
            
            viagens_est = math.ceil(toneladas_totais / capacidade_caminhao)
            km_est = viagens_est * distancia_viagem_completa_km
            custo_total_frete = (km_est / consumo_km_l * preco_diesel) + (km_est * custo_manutencao_km) + (viagens_est * (custo_motorista_viagem + custo_pedagio_viagem))

    viagens_necessarias = math.ceil(toneladas_totais / capacidade_caminhao)
    distancia_total_frotas = viagens_necessarias * distancia_viagem_completa_km 
    total_litros_diesel = distancia_total_frotas / consumo_km_l
    custo_total_po = toneladas_totais * pedreira['Price/ton']
    custo_subsidio_total = subsidio_frete * toneladas_totais
    custo_final_fazendeiro_total = max(0, custo_total_frete - custo_subsidio_total)
    custo_frete_ha = custo_final_fazendeiro_total / area_ha
    frete_por_tonelada = custo_total_frete / toneladas_totais if toneladas_totais > 0 else 0

    with col_t2:
        st.markdown("##### 📊 Resumo de Custos Tradicionais")
        m1, m2, m3 = st.columns(3)
        m1.metric("Viagens", f"{viagens_necessarias}")
        m2.metric("Km Total Frota", f"{distancia_total_frotas:,.0f} km")
        m3.metric("Frete por Tonelada", f"R$ {frete_por_tonelada:,.2f}")
        
        st.warning(f"**Custo Final do Produtor Rural:** R$ {custo_final_fazendeiro_total:,.2f} *(R$ {custo_frete_ha:,.2f} / ha)*")
        
        pdf_bytes = gerar_pdf(pedreira['Exibicao'], area_ha, dose_t_ha, toneladas_totais, capacidade_caminhao, viagens_necessarias, distancia_viagem_completa_km, distancia_total_frotas, total_litros_diesel, frete_por_tonelada, custo_total_po, custo_subsidio_total, custo_total_frete, custo_final_fazendeiro_total, custo_frete_ha, tipo_frete)
        st.download_button(label="📄 Baixar Proposta Tradicional em PDF", data=pdf_bytes, file_name="Proposta_InPlanet.pdf", mime="application/pdf", use_container_width=True)

# ------------------------------------------
# ABA 2: MÓDULO AVANÇADO ESG (BIOMETANO)
# ------------------------------------------
with aba_esg:
    st.subheader("🤖 Modelo de Negócio do Operador de Biometano (Carreta 40t)")
    st.markdown("Este módulo calcula dinamicamente a estrutura de custos do operador e gera o ganho real de médio prazo em créditos de carbono.")
    
    # Função matemática para simular os 3 cenários da planilha do operador
    def calcular_cenario_operador(viagens_dia, tons, dist_iv):
        cap_caminhao = 40.0
        vgs = math.ceil(tons / cap_caminhao)
        mat_dia = viagens_dia * cap_caminhao
        km_dia = viagens_dia * dist_iv
        dias_uts = math.ceil(vgs / viagens_dia)
        meses = dias_uts / 22.0
        
        custo_fixo_acum = meses * 61750.00
        franquia_total = meses * 4000.0
        km_total_proj = vgs * dist_iv
        km_excedente = max(0, km_total_proj - franquia_total)
        custo_km_adic = km_excedente * 4.44
        
        custo_he_dia = 240.0 if viagens_dia == 3 else (480.0 if viagens_dia == 4 else 0.0)
        custo_he_tot = custo_he_dia * dias_uts
        
        custo_tot_proj = custo_fixo_acum + custo_km_adic + custo_he_tot
        preco_ton = custo_tot_proj / tons if tons > 0 else 0
        
        return vgs, km_total_proj, dias_uts, meses, custo_fixo_acum, franquia_total, km_excedente, custo_km_adic, custo_he_tot, custo_tot_proj, preco_ton

    # Gera os dados dos 3 cenários side-by-side igual ao Excel
    res_2 = calcular_cenario_operador(2, toneladas_totais, distancia_viagem_completa_km)
    res_3 = calcular_cenario_operador(3, toneladas_totais, distancia_viagem_completa_km)
    res_4 = calcular_cenario_operador(4, toneladas_totais, distancia_viagem_completa_km)
    
    df_comparativo = pd.DataFrame({
        'Métrica Operacional': [
            'Viagens por Dia', 'Material Entregue por Dia', 'Km Total por Dia', 
            'Duração em Dias Úteis', 'Duração em Meses (Base 22d)', 'Custo Fixo Total Acumulado',
            'Franquia Total de KM', 'KM Excedente Total do Projeto', 'Custo de KM Adicional (R$ 4,44)',
            'Custo de Horas Extras (Total)', 'Custo Total do Projeto', 'Preço por Tonelada'
        ],
        'Limite 8 Horas Diárias (2 Vgs)': [
            2, f"{res_2[1]/res_2[2] if res_2[2]>0 else 0:,.0f} t", f"{res_2[1]/res_2[2] if res_2[2]>0 else 0:,.0f} km", res_2[2], f"{res_2[3]:,.2f} meses", f"R$ {res_2[4]:,.2f}", f"{res_2[5]:,.0f} km", f"{res_2[6]:,.0f} km", f"R$ {res_2[7]:,.2f}", f"R$ {res_2[8]:,.2f}", f"R$ {res_2[9]:,.2f}", f"R$ {res_2[10]:,.2f}"
        ],
        '3 Viagens (Eficiente)': [
            3, f"{res_3[1]/res_3[2] if res_3[2]>0 else 0:,.0f} t", f"{res_3[1]/res_3[2] if res_3[2]>0 else 0:,.0f} km", res_3[2], f"{res_3[3]:,.2f} meses", f"R$ {res_3[4]:,.2f}", f"{res_3[5]:,.0f} km", f"{res_3[6]:,.0f} km", f"R$ {res_3[7]:,.2f}", f"R$ {res_3[8]:,.2f}", f"R$ {res_3[9]:,.2f}", f"R$ {res_3[10]:,.2f}"
        ],
        'Alta Produtividade (4 Vgs com HE)': [
            4, f"{res_4[1]/res_4[2] if res_4[2]>0 else 0:,.0f} t", f"{res_4[1]/res_4[2] if res_4[2]>0 else 0:,.0f} km", res_4[2], f"{res_4[3]:,.2f} meses", f"R$ {res_4[4]:,.2f}", f"{res_4[5]:,.0f} km", f"{res_4[6]:,.0f} km", f"R$ {res_4[7]:,.2f}", f"R$ {res_4[8]:,.2f}", f"R$ {res_4[9]:,.2f}", f"R$ {res_4[10]:,.2f}"
        ]
    })
    
    st.dataframe(df_comparativo, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 📊 Análise de Viabilidade Econômica-Ambiental")
    
    # Seletor do cenário escolhido para o gráfico em cascata
    opcao_cenario = st.selectbox("Escolha a produtividade estimada para a análise de Carbono:", ["Limite 8 Horas Diárias (2 Vgs)", "3 Viagens (Eficiente)", "Alta Produtividade (4 Vgs com HE)"])
    if opcao_cenario == "Limite 8 Horas Diárias (2 Vgs)": res_escolhido = res_2
    elif opcao_cenario == "3 Viagens (Eficiente)": res_escolhido = res_3
    else: res_escolhido = res_4
    
    km_total_esg = res_escolhido[1]
    custo_logistica_esg = res_escolhido[9]
    
    # Cálculo exato das toneladas de CO2 emitidas (Fórmulas IPCC/ spreadsheet)
    emis_diesel = (km_total_esg / CONSUMO_MEDIO['Diesel B15']) * FATORES_EMISSAO['Diesel B15'] / 1000
    emis_gnv = (km_total_esg / CONSUMO_MEDIO['GNV']) * FATORES_EMISSAO['GNV'] / 1000
    emis_biometano = (km_total_esg / CONSUMO_MEDIO['Biometano']) * FATORES_EMISSAO['Biometano'] / 1000
    
    carbono_evitado_esg = emis_diesel - emis_biometano
    ganho_financeiro_carbono = carbono_evitado_esg * valor_credito_brl
    custo_liquido_real_esg = custo_logistica_esg - ganho_financeiro_carbono
    
    col_esg1, col_esg2 = st.columns([1, 1.2])
    
    with col_esg1:
        st.markdown("##### 💼 Conta Fechada: Do Imediato ao Médio Prazo")
        st.info(f"**Custo Logístico Imediato:** R$ {custo_logistica_esg:,.2f}")
        st.success(f"**🌱 Créditos de Carbono Gerados (Ativo):** R$ {ganho_financeiro_carbono:,.2f}\n\n*(Evitou {carbono_evitado_esg:,.1f} toneladas de CO2eq)*")
        st.warning(f"**🎯 CUSTO LÍQUIDO REAL (InPlanet ESG):** R$ {custo_liquido_real_esg:,.2f}\n\n*(Preço final real de R$ {(custo_liquido_real_esg/toneladas_totais):,.2f} / ton)*")
        
    with col_esg2:
        # Gráfico Waterfall
        fig_waterfall = go.Figure(go.Waterfall(
            orientation = "v", measure = ["absolute", "relative", "total"],
            x = ["Custo Logística", "Retorno Carbono", "Custo Líquido"],
            textposition = "outside",
            text = [f"R$ {custo_logistica_esg/1000:,.0f}k", f"-R$ {ganho_financeiro_carbono/1000:,.0f}k", f"R$ {custo_liquido_real_esg/1000:,.0f}k"],
            y = [custo_logistica_esg, -ganho_financeiro_carbono, custo_liquido_real_esg],
            decreasing = {"marker":{"color":"#2EA84A"}},
            increasing = {"marker":{"color":"#E67E22"}},
            totals = {"marker":{"color":"#2C3E50"}}
        ))
        fig_waterfall.update_layout(title="Demonstrativo de Abatimento ESG", margin=dict(t=40, b=0, l=0, r=0), height=320)
        st.plotly_chart(fig_waterfall, use_container_width=True)

    # Gráfico de Barras de Emissões
    df_bar_esg = pd.DataFrame({
        'Combustível': ['Diesel B15', 'GNV', 'Biometano'],
        'Pegada de Carbono (tCO2eq)': [emis_diesel, emis_gnv, emis_biometano]
    })
    fig_bar = px.bar(df_bar_esg, x='Pegada de Carbono (tCO2eq)', y='Combustível', orientation='h',
                     color='Combustível', color_discrete_sequence=['#E67E22', '#F1C40F', '#2EA84A'], text_auto='.1f')
    fig_bar.update_layout(title="Pegada Ecológica Total do Projeto (Ciclo de Vida - Poço ao Roda)", height=250, margin=dict(t=40, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 5. MAPA INTERATIVO (VISUALIZAÇÃO GLOBAL)
# ==========================================
st.markdown("---")
st.subheader("🗺️ Visualização Geográfica do Fluxo")

if input_local and lat_extraida and lon_extraida:
    centro_lat = (pedreira['Lat'] + fazenda_lat) / 2
    centro_lon = (pedreira['Long'] + fazenda_lon) / 2
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=6)
    folium.Marker((pedreira['Lat'], pedreira['Long']), popup=f"Pedreira: {pedreira['Mine Name']}", icon=folium.Icon(color='gray', icon='industry', prefix='fa')).add_to(m)
    folium.Marker((fazenda_lat, fazenda_lon), popup="Fazenda Destino", icon=folium.Icon(color='green', icon='leaf', prefix='fa')).add_to(m)
    folium.PolyLine([(pedreira['Lat'], pedreira['Long']), (fazenda_lat, fazenda_lon)], color="blue", weight=2.5, dash_array='5, 5').add_to(m)
else:
    m = folium.Map(location=[-22.41299, -50.57594], zoom_start=7)
    folium.Marker((-22.41299, -50.57594), popup="Pedreira Siqueira", icon=folium.Icon(color='gray', icon='industry', prefix='fa')).add_to(m)

st_folium(m, width=1200, height=400)

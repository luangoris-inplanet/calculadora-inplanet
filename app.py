import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import math
import os
import plotly.express as px
import requests
import re
from fpdf import FPDF
import tempfile

# ==========================================
# CONFIGURAÇÃO DA INTERFACE (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Simulador InPlanet", page_icon="🌿", layout="wide")

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
    
    # 1. ADICIONANDO A LOGO (Se existir)
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
    
    # 2. ADICIONANDO O GRÁFICO DE ROSCA
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
    except Exception as e:
        pass 

    pdf.ln(5)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 4, txt="Documento gerado automaticamente pelo Simulador Comercial InPlanet.", ln=True, align='C')
    pdf.cell(200, 4, txt="Valores de frete sao estimativas sujeitas a variacao de mercado e pedagios.", ln=True, align='C')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
    return pdf_bytes

# ==========================================
# 1. BASE DE DADOS DAS PEDREIRAS
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

st.title("🌿 Simulador Comercial: Logística InPlanet")

# Barra Lateral
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.markdown("### [Espaço para Logo InPlanet]")

st.sidebar.markdown("---")
st.sidebar.header("Parâmetros do Frete")
tipo_frete = st.sidebar.radio("Responsabilidade do Transporte:", ("Frete Terceirizado (ANTT)", "Frota Própria (Fazendeiro)"))
st.sidebar.markdown("---")

# NOVOS CAMPOS PARA FROTA PRÓPRIA
if tipo_frete == "Frete Terceirizado (ANTT)":
    modelo_caminhao = st.sidebar.selectbox("Modelo do Caminhão (ANTT)", dados_antt['Modelo'])
else:
    preco_diesel = st.sidebar.number_input("Preço do Diesel na Região (R$/L)", value=6.00, step=0.10)
    capacidade_propria = st.sidebar.number_input("Capacidade do Caminhão (toneladas)", value=35)
    consumo_proprio = st.sidebar.number_input("Consumo do Caminhão (km/L)", value=2.5, step=0.1)
    
    st.sidebar.markdown("##### ⚙️ Custos Operacionais")
    custo_manutencao_km = st.sidebar.number_input("Pneus e Manutenção (R$/km)", value=2.00, step=0.10, help="Média BR: R$ 1,50 a R$ 2,50/km.")
    custo_motorista_viagem = st.sidebar.number_input("Diária do Motorista (R$/Viagem)", value=200.00, step=10.0)
    custo_pedagio_viagem = st.sidebar.number_input("Pedágio (R$/Viagem)", value=0.00, step=10.0)

st.sidebar.markdown("---")
st.sidebar.header("Negociação")
subsidio_frete = st.sidebar.number_input("Subsídio da InPlanet no Frete (R$/ton)", value=0.0, step=5.0)

# Seletores Principais
st.markdown("### 📍 Origem e Destino")
col1, col2 = st.columns(2)

with col1:
    pedreira_selecionada = st.selectbox("Selecione a Pedreira (Origem)", dados_pedreiras['Exibicao'], key='pedreira_key')
    pedreira = dados_pedreiras[dados_pedreiras['Exibicao'] == pedreira_selecionada].iloc[0]
    st.info(f"**Preço do Remineralizador:** R$ {pedreira['Price/ton']:,.2f} / tonelada")

with col2:
    tipo_destino = st.radio("Como deseja calcular a distância?", ("Colar Link do Google Maps / Coordenadas", "Digitar Quilometragem (Manual)"))
    
    fazenda_lat, fazenda_lon = -15.7942, -49.2536 
    distancia_ida_km = 150.0
    
    if tipo_destino == "Colar Link do Google Maps / Coordenadas":
        input_local = st.text_input("Cole aqui o Link do Google Maps ou as Coordenadas:")
        
        if input_local:
            lat_extraida, lon_extraida = extrair_coordenadas(input_local)
            
            if lat_extraida and lon_extraida:
                fazenda_lat, fazenda_lon = lat_extraida, lon_extraida
                st.success(f"📍 Destino encontrado! (Lat: {fazenda_lat}, Lon: {fazenda_lon})")
                
                st.button("🪄 Auto-Selecionar Pedreira Mais Próxima", on_click=auto_selecionar_pedreira, args=(fazenda_lat, fazenda_lon))
                
                coord_origem = (pedreira['Lat'], pedreira['Long'])
                coord_destino = (fazenda_lat, fazenda_lon)
                
                distancia_ida_km = geodesic(coord_origem, coord_destino).km * 1.2
                st.success(f"✅ Distância estimada (Linha Reta + 20% margem): **{distancia_ida_km:,.1f} km**.")

            else:
                st.error("❌ Não consegui encontrar as coordenadas neste texto. Cole um link válido do Google Maps.")
    else:
        distancia_ida_km = st.number_input("Distância de Ida (km)", value=150.0, step=10.0, min_value=1.0)

st.markdown("### 🚜 Volume da Operação Agronômica")
col_area, col_dose = st.columns(2)
area_ha = col_area.number_input("Área de Aplicação na Fazenda (Hectares)", value=100.0, step=50.0, min_value=1.0)
dose_t_ha = col_dose.slider("Dosagem Recomendada (toneladas/hectare)", min_value=1.0, max_value=50.0, value=20.0, step=1.0)

toneladas_totais = area_ha * dose_t_ha
st.success(f"**Carga Total Necessária:** {toneladas_totais:,.0f} toneladas de remineralizador.")

# ==========================================
# 3. LÓGICA DE CÁLCULO
# ==========================================
distancia_viagem_completa_km = distancia_ida_km * 2
custo_total_po = toneladas_totais * pedreira['Price/ton']
custo_subsidio_total = subsidio_frete * toneladas_totais
custo_inplanet_total = custo_total_po + custo_subsidio_total

if tipo_frete == "Frete Terceirizado (ANTT)":
    caminhao_selecionado = dados_antt[dados_antt['Modelo'] == modelo_caminhao].iloc[0]
    capacidade_caminhao = caminhao_selecionado['Capacidade_t']
    consumo_km_l = caminhao_selecionado['Consumo_km_l']
    
    if distancia_ida_km <= 50:
        tarifa_ton_km = caminhao_selecionado['Ate_50km']
    elif distancia_ida_km <= 100:
        tarifa_ton_km = caminhao_selecionado['Ate_100km']
    else:
        tarifa_ton_km = caminhao_selecionado['Acima_100km']
        
    custo_total_frete = toneladas_totais * distancia_viagem_completa_km * tarifa_ton_km
    custo_combustivel = 0
    custo_manut_total = 0
    custo_motor_total = 0
    custo_pedagio_total = 0
else: 
    capacidade_caminhao = capacidade_propria
    consumo_km_l = consumo_proprio
    tarifa_ton_km = 0 
    
    viagens_necessarias = math.ceil(toneladas_totais / capacidade_caminhao)
    distancia_total_percorrida = viagens_necessarias * distancia_viagem_completa_km 
    litros_consumidos = distancia_total_percorrida / consumo_km_l
    
    custo_combustivel = litros_consumidos * preco_diesel
    custo_manut_total = distancia_total_percorrida * custo_manutencao_km
    custo_motor_total = viagens_necessarias * custo_motorista_viagem
    custo_pedagio_total = viagens_necessarias * custo_pedagio_viagem
    
    custo_total_frete = custo_combustivel + custo_manut_total + custo_motor_total + custo_pedagio_total

viagens_necessarias = math.ceil(toneladas_totais / capacidade_caminhao)
distancia_total_frotas = viagens_necessarias * distancia_viagem_completa_km 
total_litros_diesel = distancia_total_frotas / consumo_km_l
custo_final_fazendeiro_total = max(0, custo_total_frete - custo_subsidio_total)
custo_frete_ha = custo_final_fazendeiro_total / area_ha
frete_por_tonelada = custo_total_frete / toneladas_totais if toneladas_totais > 0 else 0

# ==========================================
# 4. EXIBIÇÃO DE RESULTADOS & GRÁFICOS
# ==========================================
st.markdown("---")
st.subheader("📊 Resumo da Frota e Custos")

metric1, metric2, metric3, metric4, metric5 = st.columns(5)
metric1.metric("Viagens Necessárias", f"{viagens_necessarias} viagens", f"Caminhão de {capacidade_caminhao}t")
metric2.metric("Distância (Ida + Volta)", f"{distancia_viagem_completa_km:,.0f} km")
metric3.metric("Km Total Rodado", f"{distancia_total_frotas:,.0f} km")
metric4.metric("Consumo Est. Diesel", f"{total_litros_diesel:,.0f} L")
metric5.metric("Frete Cheio (por Ton)", f"R$ {frete_por_tonelada:,.2f}")

st.markdown("---")
col_metricas, col_grafico = st.columns([1.2, 1])

with col_metricas:
    st.markdown("##### 🤝 Resumo Financeiro da Parceria")
    st.info(f"**🟢 Investimento InPlanet:**\nRemineralizador: R$ {custo_total_po:,.2f}\nSubsídio Frete: R$ {custo_subsidio_total:,.2f}\n**Total InPlanet: R$ {custo_inplanet_total:,.2f}**")
    st.warning(f"**🚜 Custo do Agricultor:**\nFrete Cheio: R$ {custo_total_frete:,.2f}\nSubsídio InPlanet: - R$ {custo_subsidio_total:,.2f}\n**Frete Final: R$ {custo_final_fazendeiro_total:,.2f}**")
    st.success(f"**🎯 Custo para o Produtor (por Hectare):**\nFrete/ha: **R$ {custo_frete_ha:,.2f} / ha**\n*(O remineralizador é 100% custeado pela InPlanet)*")
    
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_bytes = gerar_pdf(
        pedreira['Exibicao'], area_ha, dose_t_ha, toneladas_totais, capacidade_caminhao, 
        viagens_necessarias, distancia_viagem_completa_km, distancia_total_frotas, 
        total_litros_diesel, frete_por_tonelada, custo_total_po, custo_subsidio_total, 
        custo_total_frete, custo_final_fazendeiro_total, custo_frete_ha, tipo_frete
    )
    st.download_button(
        label="📄 Baixar Proposta em PDF",
        data=pdf_bytes,
        file_name="Proposta_InPlanet.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with col_grafico:
    df_grafico = pd.DataFrame({
        'Categoria': ['Remineralizador (Invest. InPlanet)', 'Subsídio Frete (Invest. InPlanet)', 'Frete (Custo Produtor)'],
        'Valor (R$)': [custo_total_po, custo_subsidio_total, custo_final_fazendeiro_total]
    })
    cores = ['#2EA84A', '#82E0AA', '#E67E22']
    fig = px.pie(df_grafico, values='Valor (R$)', names='Categoria', hole=0.4, 
                 title="Distribuição Financeira Total",
                 color_discrete_sequence=cores)
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# MEMÓRIA DE CÁLCULO (PASSO A PASSO)
# ------------------------------------------
with st.expander("🧮 Ver Memória de Cálculo (Passo a Passo para o Produtor)"):
    st.markdown("Mostre esta seção ao produtor rural para total transparência na formação de preços.")
    
    st.write(f"**1. Necessidade de Produto:**")
    st.write(f"{area_ha} hectares × {dose_t_ha} toneladas/ha = **{toneladas_totais:,.0f} toneladas** de Remineralizador.")
    
    st.write(f"**2. Logística e Transporte:**")
    st.write(f"Capacidade do Caminhão: **{capacidade_caminhao} toneladas** por viagem.")
    st.write(f"{toneladas_totais:,.0f} tons ÷ {capacidade_caminhao} tons = **{viagens_necessarias} viagens** completas.")
    st.write(f"Distância do Trajeto (Ida + Volta): **{distancia_viagem_completa_km:,.0f} km**.")
    st.write(f"Quilometragem Total da Frota: {viagens_necessarias} viagens × {distancia_viagem_completa_km:,.0f} km = **{distancia_total_frotas:,.0f} km rodados**.")
    
    st.write(f"**3. Formação do Preço do Frete:**")
    if tipo_frete == "Frete Terceirizado (ANTT)":
        st.write(f"Cálculo ANTT: {toneladas_totais:,.0f} tons × {distancia_viagem_completa_km:,.0f} km × R$ {tarifa_ton_km:.2f} (Tarifa por ton/km) = **R$ {custo_total_frete:,.2f}**.")
    else:
        st.write(f"A) Combustível: {total_litros_diesel:,.0f} Litros × R$ {preco_diesel:.2f} = **R$ {custo_combustivel:,.2f}**")
        st.write(f"B) Pneus e Manutenção: {distancia_total_frotas:,.0f} km × R$ {custo_manutencao_km:.2f}/km = **R$ {custo_manut_total:,.2f}**")
        st.write(f"C) Motorista e Pedágio: {viagens_necessarias} viagens × (R$ {custo_motorista_viagem:.2f} + R$ {custo_pedagio_viagem:.2f}) = **R$ {(custo_motor_total + custo_pedagio_total):,.2f}**")
        st.write(f"Custo Total da Frota (A+B+C) = **R$ {custo_total_frete:,.2f}**")
        
    st.write(f"Custo Original do Frete por Tonelada: **R$ {frete_por_tonelada:,.2f} / ton**.")
    
    st.write(f"**4. Abatimento InPlanet:**")
    st.write(f"A InPlanet custeará R$ {subsidio_frete:.2f} por tonelada transportada.")
    st.write(f"{toneladas_totais:,.0f} tons × R$ {subsidio_frete:.2f} = **R$ {custo_subsidio_total:,.2f} de desconto no frete**.")
    
    st.write(f"**5. Custo Final na Fazenda:**")
    st.write(f"R$ {custo_total_frete:,.2f} (Frete Cheio) - R$ {custo_subsidio_total:,.2f} (Desconto) = **R$ {custo_final_fazendeiro_total:,.2f}**.")
    st.write(f"Diluindo pela área: R$ {custo_final_fazendeiro_total:,.2f} ÷ {area_ha} ha = **R$ {custo_frete_ha:,.2f} por hectare**.")

# ==========================================
# 5. MAPA INTERATIVO
# ==========================================
st.markdown("---")
st.subheader("🗺️ Visualização no Mapa")

if tipo_destino == "Colar Link do Google Maps / Coordenadas" and input_local:
    centro_lat = (pedreira['Lat'] + fazenda_lat) / 2
    centro_lon = (pedreira['Long'] + fazenda_lon) / 2
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=6)
    
    folium.Marker(coord_origem, popup=f"Origem: {pedreira['Mine Name']}", icon=folium.Icon(color='gray', icon='industry', prefix='fa')).add_to(m)
    folium.Marker(coord_destino, popup="Destino", icon=folium.Icon(color='green', icon='leaf', prefix='fa')).add_to(m)
    folium.PolyLine([coord_origem, coord_destino], color="blue", weight=2.5, opacity=0.8, dash_array='5, 5').add_to(m)
else:
    m = folium.Map(location=[pedreira['Lat'], pedreira['Long']], zoom_start=8)
    folium.Marker((pedreira['Lat'], pedreira['Long']), popup=f"Origem: {pedreira['Mine Name']}", icon=folium.Icon(color='gray', icon='industry', prefix='fa')).add_to(m)

st_folium(m, width=1200, height=500)
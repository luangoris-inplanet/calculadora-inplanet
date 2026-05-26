import streamlit as st
import pandas as pd
import math
import os
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import tempfile

# ==========================================
# CONFIGURAÇÃO DA INTERFACE E FATORES ESG
# ==========================================
st.set_page_config(page_title="Simulador Analítico InPlanet", page_icon="🌿", layout="wide")

# Fatores de Emissão Oficiais (kgCO2eq por L ou m³)
FATORES_EMISSAO = {
    'Diesel B15': 2.70831,
    'Biometano': 0.30620
}
CONSUMO_MEDIO = {
    'Diesel B15': 2.02,
    'Biometano': 1.90
}

# ==========================================
# BASE DE DADOS
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
    'Price/ton': [
        50.0, 58.0, 100.0, 70.0, 70.0, 70.0, 70.0, 120.0, 60.0, 90.0, 63.0, 50.0, 52.0, 50.0, 
        50.0, 50.0, 59.76, 60.0, 57.5, 80.0, 80.0, 40.0, 62.5, 90.0, 50.0, 70.0, 70.0, 80.0, 
        50.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 60.0, 45.0, 60.0, 45.0
    ]
})
dados_pedreiras['Exibicao'] = dados_pedreiras['Mine Name'] + " (" + dados_pedreiras['City'] + " - " + dados_pedreiras['State'] + ")"

dados_antt = pd.DataFrame({
    'Modelo': ['LS (6 eixos) - 33t', 'Bi-trem (7 eixos) - 38t', 'Bi-trem (9 eixos) - 50t'],
    'Capacidade_t': [33, 38, 50],
    'Consumo_km_l': [2.5, 2.2, 1.8],
    'Ate_50km': [0.37, 0.35, 0.35],
    'Ate_100km': [0.27, 0.25, 0.26],
    'Acima_100km': [0.24, 0.22, 0.23]
})

# ==========================================
# INTERFACE LATERAL (SIDEBAR)
# ==========================================
st.title("📊 Painel Analítico: Decisão Logística & ESG")

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.header("⚙️ Variáveis de Mercado")
preco_credito_usd = st.sidebar.number_input("Preço Estratégico do Crédito ($/tCDR)", value=300.0)
cotacao_dolar = st.sidebar.number_input("Cotação Cambial (R$/USD)", value=5.00, step=0.10)
valor_credito_brl = preco_credito_usd * cotacao_dolar
st.sidebar.info(f"**Retorno Estimado:** R$ {valor_credito_brl:,.2f} / tCO2evitada")

st.sidebar.markdown("---")
st.sidebar.header("📋 Modalidades de Análise")
opcoes_ativas = st.sidebar.multiselect(
    "Quais fretes deseja comparar?",
    ["Preço ANTT (Terceirizado)", "Frete Próprio (Fazenda)", "Frete Retorno (Diesel)", "Operação Biometano (InPlanet)"],
    default=["Preço ANTT (Terceirizado)", "Frete Retorno (Diesel)", "Operação Biometano (InPlanet)"]
)

# ==========================================
# INPUTS UNIFICADOS DA OPERAÇÃO
# ==========================================
st.markdown("### 📍 Escopo da Operação Agronômica")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    pedreira_selecionada = st.selectbox("Pedreira de Origem:", dados_pedreiras['Exibicao'])
    pedreira_dados = dados_pedreiras[dados_pedreiras['Exibicao'] == pedreira_selecionada].iloc[0]

with col_input2:
    distancia_ida_km = st.number_input("Distância de Ida até a Fazenda (km):", value=150.0, step=10.0, min_value=1.0)
    dist_completa_ida_volta = distancia_ida_km * 2

with col_input3:
    area_ha = st.number_input("Área de Aplicação (Hectares):", value=500.0, step=50.0)
    dose_t_ha = st.number_input("Dosagem (t/ha):", value=20.0, step=1.0)
    toneladas_totais = area_ha * dose_t_ha

st.markdown("---")

# ==========================================
# PARÂMETROS ESPECÍFICOS OCULTOS NO EXPANDER
# ==========================================
with st.expander("🛠️ Ajustar Parâmetros Internos dos Custos de Frete", expanded=False):
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        if "Preço ANTT (Terceirizado)" in opcoes_ativas:
            st.markdown("**🚛 Frete ANTT**")
            modelo_antt = st.selectbox("Modelo Caminhão:", dados_antt['Modelo'])
            antt_dados = dados_antt[dados_antt['Modelo'] == modelo_antt].iloc[0]
    with col_c2:
        if "Frete Próprio (Fazenda)" in opcoes_ativas:
            st.markdown("**🚜 Frete Próprio**")
            preco_diesel = st.number_input("Diesel (R$/L):", value=6.00)
            cap_propria = st.number_input("Capacidade (t):", value=35)
            cons_proprio = st.number_input("Consumo (km/L):", value=2.5)
            manut_km_proprio = st.number_input("Manut/Pneu (R$/km):", value=2.00)
            fixos_viagem_proprio = st.number_input("Motorista/Pedágio (R$/Vgo):", value=200.0)
    with col_c3:
        if "Frete Retorno (Diesel)" in opcoes_ativas:
            st.markdown("**🔄 Frete Retorno**")
            valor_ton_retorno = st.number_input("Custo Fechado (R$/ton):", value=35.0)
            cap_retorno = st.number_input("Capacidade (t):", value=40)
            cons_retorno = st.number_input("Consumo (km/L):", value=2.02)
    with col_c4:
        if "Operação Biometano (InPlanet)" in opcoes_ativas:
            st.markdown("**🌱 Biometano**")
            trips_dia_biometano = st.number_input("Viagens por Dia:", value=3, min_value=1)

# ==========================================
# LÓGICA DE CÁLCULO DAS MODALIDADES
# ==========================================
resumo_modalidades = {}

if "Preço ANTT (Terceirizado)" in opcoes_ativas:
    cap_antt = antt_dados['Capacidade_t']
    vgs_antt = math.ceil(toneladas_totais / cap_antt)
    km_antt = vgs_antt * dist_completa_ida_volta
    tarifa_antt = antt_dados['Ate_50km'] if distancia_ida_km <= 50 else (antt_dados['Ate_100km'] if distancia_ida_km <= 100 else antt_dados['Acima_100km'])
    custo_antt = toneladas_totais * dist_completa_ida_volta * tarifa_antt
    emis_antt = (km_antt / antt_dados['Consumo_km_l']) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Preço ANTT (Terceirizado)"] = {"Custo Total": custo_antt, "R$/t": custo_antt / toneladas_totais, "Viagens": vgs_antt, "Km Total": km_antt, "Emissoes": emis_antt}

if "Frete Próprio (Fazenda)" in opcoes_ativas:
    vgs_proprio = math.ceil(toneladas_totais / cap_propria)
    km_proprio = vgs_proprio * dist_completa_ida_volta
    custo_proprio_tot = (km_proprio / cons_proprio * preco_diesel) + (km_proprio * manut_km_proprio) + (vgs_proprio * fixos_viagem_proprio)
    emis_proprio = (km_proprio / cons_proprio) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Frete Próprio (Fazenda)"] = {"Custo Total": custo_proprio_tot, "R$/t": custo_proprio_tot / toneladas_totais, "Viagens": vgs_proprio, "Km Total": km_proprio, "Emissoes": emis_proprio}

if "Frete Retorno (Diesel)" in opcoes_ativas:
    custo_retorno_tot = toneladas_totais * valor_ton_retorno
    vgs_retorno = math.ceil(toneladas_totais / cap_retorno)
    km_retorno = vgs_retorno * distancia_ida_km # Só conta Ida
    emis_retorno = (km_retorno / cons_retorno) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Frete Retorno (Diesel)"] = {"Custo Total": custo_retorno_tot, "R$/t": valor_ton_retorno, "Viagens": vgs_retorno, "Km Total": km_retorno, "Emissoes": emis_retorno}

if "Operação Biometano (InPlanet)" in opcoes_ativas:
    cap_bio = 40.0
    vgs_bio = math.ceil(toneladas_totais / cap_bio)
    km_bio = vgs_bio * dist_completa_ida_volta
    dias_uts_bio = math.ceil(vgs_bio / trips_dia_biometano)
    meses_bio = dias_uts_bio / 22.0
    custo_fixo_bio = meses_bio * 61750.00
    km_excedente_bio = max(0, (km_bio / meses_bio if meses_bio > 0 else 0) - 4000.0) * meses_bio
    custo_km_bio = km_excedente_bio * 4.44
    custo_he_bio = (240.0 if trips_dia_biometano == 3 else (480.0 if trips_dia_biometano >= 4 else 0.0)) * dias_uts_bio
    custo_bio_bruto = custo_fixo_bio + custo_km_bio + custo_he_bio
    emis_bio = (km_bio / CONSUMO_MEDIO['Biometano']) * FATORES_EMISSAO['Biometano'] / 1000
    resumo_modalidades["Operação Biometano (InPlanet)"] = {"Custo Total": custo_bio_bruto, "R$/t": custo_bio_bruto / toneladas_totais, "Viagens": vgs_bio, "Km Total": km_bio, "Emissoes": emis_bio}


# ==========================================
# 1. CARDS DINÂMICOS (DECISÃO IMEDIATA)
# ==========================================
if resumo_modalidades:
    st.subheader("💳 Custo Logístico Imediato (R$ por Tonelada)")
    
    # Encontra o menor valor por tonelada para dar o destaque
    menor_custo_ton = min([d['R$/t'] for d in resumo_modalidades.values()])
    
    cols_cards = st.columns(len(resumo_modalidades))
    
    for col, (modalidade, dados) in zip(cols_cards, resumo_modalidades.items()):
        com_trofeu = dados['R$/t'] == menor_custo_ton
        
        # Define as cores do Card (Verde se for o melhor, Cinza se não for)
        bg_color = "#E8F5E9" if com_trofeu else "#F8F9FA"
        border_color = "#2EA84A" if com_trofeu else "#DEE2E6"
        text_color = "#1E8449" if com_trofeu else "#2C3E50"
        trofeu_html = "🏆 <b>Mais Econômico</b><br>" if com_trofeu else "<br>"
        
        card_html = f"""
        <div style="background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 10px; padding: 15px; text-align: center; height: 100%;">
            <p style="color: #7F8C8D; font-size: 14px; margin-bottom: 5px;">{modalidade}</p>
            <h2 style="color: {text_color}; margin: 0px;">R$ {dados['R$/t']:,.2f} <span style="font-size: 16px;">/t</span></h2>
            <p style="color: {text_color}; font-size: 12px; margin-top: 5px;">{trofeu_html}</p>
        </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)

    # ==========================================
    # 2. INTELIGÊNCIA ESG (BIOMETANO VS DIESEL)
    # ==========================================
    if "Operação Biometano (InPlanet)" in opcoes_ativas:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌱 Inteligência de Carbono: Rentabilidade do Biometano")
        
        # Calcula um "Diesel Baseline" para comparação de mesma rota (Assumindo 40t e consumo médio de 2.02)
        vgs_baseline = math.ceil(toneladas_totais / 40.0)
        km_baseline = vgs_baseline * dist_completa_ida_volta
        emis_baseline_diesel = (km_baseline / CONSUMO_MEDIO['Diesel B15']) * FATORES_EMISSAO['Diesel B15'] / 1000
        
        emissoes_bio = resumo_modalidades["Operação Biometano (InPlanet)"]['Emissoes']
        carbono_evitado = emis_baseline_diesel - emissoes_bio
        
        valor_total_gerado = carbono_evitado * valor_credito_brl
        valor_por_tonelada_gerado = valor_total_gerado / toneladas_totais if toneladas_totais > 0 else 0
        
        st.info(f"""
        **A Mágica da Descarbonização na Prática:** Ao escolher a operação InPlanet a Biometano em vez de uma carreta Diesel padrão, essa operação de {toneladas_totais:,.0f} toneladas evita a emissão de **{carbono_evitado:,.1f} tCO2eq**. 
        """)
        
        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.metric("💰 Ativo Financeiro Gerado (Total)", f"R$ {valor_total_gerado:,.2f}", f"Créditos Convertidos")
        col_b2.metric("♻️ Retorno por Tonelada", f"R$ {valor_por_tonelada_gerado:,.2f}", f"Abatimento por Ton")
        
        # Custo Líquido Real do Biometano
        custo_bruto_bio = resumo_modalidades["Operação Biometano (InPlanet)"]["Custo Total"]
        custo_liquido_bio = custo_bruto_bio - valor_total_gerado
        preco_liquido_ton_bio = custo_liquido_bio / toneladas_totais
        col_b3.metric("🎯 Preço LÍQUIDO Biometano", f"R$ {preco_liquido_ton_bio:,.2f} / t", f"Após compensação ESG", delta_color="inverse")

    # ==========================================
    # 3. GRÁFICOS ANALÍTICOS GERAIS
    # ==========================================
    st.markdown("---")
    st.subheader("📈 Visão Consolidada: Custos x Pegada Ambiental")
    
    col_g1, col_g2 = st.columns(2)
    
    df_graficos = pd.DataFrame([
        {
            "Modalidade": k, 
            "Custo Total (R$)": v['Custo Total'], 
            "Pegada Ecológica (tCO2eq)": v['Emissoes'],
        } for k, v in resumo_modalidades.items()
    ])
    
    with col_g1:
        fig_custos = px.bar(df_graficos, x='Modalidade', y='Custo Total (R$)', 
                            title="Desembolso Operacional Total (R$)",
                            color='Modalidade', text_auto='.2s')
        fig_custos.update_layout(showlegend=False)
        st.plotly_chart(fig_custos, use_container_width=True)
        
    with col_g2:
        fig_sustentabilidade = px.bar(df_graficos, x='Modalidade', y='Pegada Ecológica (tCO2eq)', 
                                      title="Impacto Ambiental (Ton. de Carbono)",
                                      color='Modalidade', text_auto='.1f')
        fig_sustentabilidade.update_layout(showlegend=False)
        st.plotly_chart(fig_sustentabilidade, use_container_width=True)

else:
    st.warning("⚠️ Por favor, selecione pelo menos uma modalidade de frete na barra lateral esquerda.")

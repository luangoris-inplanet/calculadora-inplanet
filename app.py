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

FATORES_EMISSAO = {'Diesel B15': 2.70831, 'Biometano': 0.30620}
CONSUMO_MEDIO = {'Diesel B15': 2.02, 'Biometano': 1.90}

CORES_MODALIDADES = {
    'Operação Biometano (InPlanet)': '#2EA84A',
    'Frete Retorno (Diesel)': '#E67E22',
    'Preço ANTT (Terceirizado)': '#34495E',
    'Frete Próprio (Fazenda)': '#95A5A6'
}

# ==========================================
# BASE DE DADOS
# ==========================================
dados_pedreiras = pd.DataFrame({
    'Mine Name': ['Siqueira', 'Esteio (Tozzi-Junqueira)', 'Conquista', 'Pedreira São Franciso', 'Baú Mineração', 'Consbrita', 'Quimassa', 'Ecobrix', 'Mineração Barbarense', 'Conquista (Prudente)', 'Constroeste', 'Carrascoza', 'Coplan', 'Mandaguari', 'Ekosolos', 'Quibrita', 'Mineração Campo Grande', 'Bandeirantes', 'Sozo Britas', 'Fortaleza Caçu', 'Goyaz Britas', 'Expressa', 'Diabásio', 'Simoso', 'Pardo', 'Noroeste', 'W&W Britagem', 'Ica', 'Polimix', 'Grupo Autem', 'Piraju', 'Noroeste Paulista', 'Minerpal', 'Compensa', 'Gemelli', 'Construbrás I', 'Construbrás II', 'Britaminas Fortaleza', 'Ingá', 'Fortaleza Rio Verde', 'Rio Claro'],
    'City': ['Paraguaçu Paulista', 'Itaporã', 'Narandiba', 'Porto Franco', 'Caxias', 'Curitibanos', 'Limeira', 'Uberlândia', 'Santa Bárbara D\'oeste', 'Presidente Prudente', 'Icém', 'Cravinhos', 'Embaúba', 'Mandaguari', 'Paula Freitas', 'Piracicaba', 'Terenos', 'São Carlos', 'Ponte Alta', 'Cachoeira Alta', 'Panamá', 'Londrina', 'Lençóis Paulista', 'Mogi-Mirim', 'Santa Cruz do Rio Pardo', 'Votuporanga', 'Ituiutaba', 'Ibiporã', 'Campo Grande', 'Jaboticabal', 'Assis', 'Monções', 'Palotina', 'Paula Freitas', 'Chiapetta', 'São Luiz Gonzaga', 'Sarandi', 'Portelândia', 'Maringá', 'Rio Verde', 'Jataí'],
    'State': ['SP', 'MS', 'SP', 'MA', 'MA', 'SC', 'SP', 'MG', 'SP', 'SP', 'SP', 'SP', 'SP', 'PR', 'PR', 'SP', 'MS', 'SP', 'SC', 'GO', 'GO', 'PR', 'SP', 'SP', 'SP', 'SP', 'MG', 'PR', 'MS', 'SP', 'SP', 'SP', 'PR', 'PR', 'RS', 'RS', 'RS', 'GO', 'PR', 'GO', 'GO'],
    'Price/ton': [50.0, 58.0, 100.0, 70.0, 70.0, 70.0, 70.0, 120.0, 60.0, 90.0, 63.0, 50.0, 52.0, 50.0, 50.0, 50.0, 59.76, 60.0, 57.5, 80.0, 80.0, 40.0, 62.5, 90.0, 50.0, 70.0, 70.0, 80.0, 50.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 70.0, 60.0, 45.0, 60.0, 45.0]
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
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.header("⚙️ Variáveis de Mercado")
preco_credito_usd = st.sidebar.number_input("Preço Estratégico do Crédito ($/tCDR)", value=300.0)
cotacao_dolar = st.sidebar.number_input("Cotação Cambial (R$/USD)", value=5.00, step=0.10)
valor_credito_brl = preco_credito_usd * cotacao_dolar

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
# PARÂMETROS ESPECÍFICOS OCULTOS
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
            custo_fixo_bio = st.number_input("Custo Fixo Mensal (R$):", value=61750.00, step=1000.0)
            franquia_km_bio = st.number_input("Franquia Inclusa (km/mês):", value=4000.0, step=100.0)
            custo_km_exc_bio = st.number_input("Taxa Km Excedente (R$/km):", value=4.44, step=0.10)
            he_3vgs = st.number_input("Hora Extra p/ 3 Vgs (R$/dia):", value=240.0, step=10.0)
            he_4vgs = st.number_input("Hora Extra p/ 4+ Vgs (R$/dia):", value=480.0, step=10.0)

# ==========================================
# LÓGICA DE BASELINE GLOBAL (DIESEL 40T IDA+VOLTA)
# ==========================================
vgs_baseline = math.ceil(toneladas_totais / 40.0)
km_baseline = vgs_baseline * dist_completa_ida_volta
emis_baseline_diesel = (km_baseline / CONSUMO_MEDIO['Diesel B15']) * FATORES_EMISSAO['Diesel B15'] / 1000
custo_baseline_diesel = toneladas_totais * dist_completa_ida_volta * 0.26 # Custo genérico ANTT 50t para o produtor não ficar sem base

# ==========================================
# LÓGICA DE CÁLCULO
# ==========================================
resumo_modalidades = {}

if "Preço ANTT (Terceirizado)" in opcoes_ativas:
    cap_antt = antt_dados['Capacidade_t']
    vgs_antt = math.ceil(toneladas_totais / cap_antt)
    km_antt = vgs_antt * dist_completa_ida_volta
    tarifa_antt = antt_dados['Ate_50km'] if distancia_ida_km <= 50 else (antt_dados['Ate_100km'] if distancia_ida_km <= 100 else antt_dados['Acima_100km'])
    custo_antt = toneladas_totais * dist_completa_ida_volta * tarifa_antt
    emis_antt = (km_antt / antt_dados['Consumo_km_l']) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Preço ANTT (Terceirizado)"] = {"Custo Total": custo_antt, "R$/t": custo_antt / toneladas_totais, "Viagens": vgs_antt, "Emissoes": emis_antt}
    custo_baseline_diesel = custo_antt 
    emis_baseline_diesel = emis_antt

if "Frete Próprio (Fazenda)" in opcoes_ativas:
    vgs_proprio = math.ceil(toneladas_totais / cap_propria)
    km_proprio = vgs_proprio * dist_completa_ida_volta
    custo_proprio_tot = (km_proprio / cons_proprio * preco_diesel) + (km_proprio * manut_km_proprio) + (vgs_proprio * fixos_viagem_proprio)
    emis_proprio = (km_proprio / cons_proprio) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Frete Próprio (Fazenda)"] = {"Custo Total": custo_proprio_tot, "R$/t": custo_proprio_tot / toneladas_totais, "Viagens": vgs_proprio, "Emissoes": emis_proprio}

if "Frete Retorno (Diesel)" in opcoes_ativas:
    custo_retorno_tot = toneladas_totais * valor_ton_retorno
    vgs_retorno = math.ceil(toneladas_totais / cap_retorno)
    km_retorno = vgs_retorno * distancia_ida_km
    emis_retorno = (km_retorno / cons_retorno) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Frete Retorno (Diesel)"] = {"Custo Total": custo_retorno_tot, "R$/t": valor_ton_retorno, "Viagens": vgs_retorno, "Emissoes": emis_retorno}

if "Operação Biometano (InPlanet)" in opcoes_ativas:
    cap_bio_calc = 40.0
    vgs_bio_calc = math.ceil(toneladas_totais / cap_bio_calc)
    km_bio_calc = vgs_bio_calc * dist_completa_ida_volta
    dias_uts_bio = math.ceil(vgs_bio_calc / trips_dia_biometano)
    meses_bio = dias_uts_bio / 22.0
    custo_fixo_bio_tot = meses_bio * custo_fixo_bio
    km_excedente_bio = max(0, (km_bio_calc / meses_bio if meses_bio > 0 else 0) - franquia_km_bio) * meses_bio
    custo_km_bio_tot = km_excedente_bio * custo_km_exc_bio
    custo_he_bio_tot = (he_3vgs if trips_dia_biometano == 3 else (he_4vgs if trips_dia_biometano >= 4 else 0.0)) * dias_uts_bio
    custo_bio_bruto = custo_fixo_bio_tot + custo_km_bio_tot + custo_he_bio_tot
    emis_bio = (km_bio_calc / CONSUMO_MEDIO['Biometano']) * FATORES_EMISSAO['Biometano'] / 1000
    resumo_modalidades["Operação Biometano (InPlanet)"] = {"Custo Total": custo_bio_bruto, "R$/t": custo_bio_bruto / toneladas_totais, "Viagens": vgs_bio_calc, "Emissoes": emis_bio}

# ==========================================
# PAINEL DE NEGOCIAÇÃO (INTELIGÊNCIA COMERCIAL)
# ==========================================
if resumo_modalidades:
    st.subheader("🤝 Painel de Negociação B2B (Margem InPlanet)")
    st.markdown("Análise de subsídio baseada na geração excedente de ativos de carbono frente ao frete tradicional a Diesel.")

    # Filtra apenas as modalidades verdes ativadas para negociação
    opcoes_verdes = [m for m in ["Frete Retorno (Diesel)", "Operação Biometano (InPlanet)"] if m in resumo_modalidades]
    
    if not opcoes_verdes:
        st.warning("Ative o Frete Retorno ou Biometano para visualizar as margens de negociação ESG.")
    else:
        abas_negociacao = st.tabs(opcoes_verdes)
        
        for i, nome_modalidade in enumerate(opcoes_verdes):
            with abas_negociacao[i]:
                dados = resumo_modalidades[nome_modalidade]
                
                # Matemática da Negociação
                diferenca_custo_produtor = dados['Custo Total'] - custo_baseline_diesel
                emissoes_evitadas = max(0, emis_baseline_diesel - dados['Emissoes'])
                receita_extra_inplanet = emissoes_evitadas * valor_credito_brl
                
                # Margem de negociação (Breakeven)
                margem_livre_inplanet = receita_extra_inplanet
                
                # Se o produtor estiver pagando mais caro pelo frete verde, a InPlanet pode cobrir
                subsídio_necessario = max(0, diferenca_custo_produtor) 
                
                # O que sobra para dar de bônus real por hectare
                saldo_para_bonus = margem_livre_inplanet - subsídio_necessario
                bonus_maximo_ha = saldo_para_bonus / area_ha if saldo_para_bonus > 0 else 0
                
                col_n1, col_n2, col_n3 = st.columns(3)
                
                # CARD 1: O bolso do produtor
                if diferenca_custo_produtor > 0:
                    status_produtor = f"Produtor paga **R$ {diferenca_custo_produtor:,.2f} a mais**"
                    cor_produtor = "#E74C3C"
                else:
                    status_produtor = f"Produtor **economiza R$ {abs(diferenca_custo_produtor):,.2f}**"
                    cor_produtor = "#2EA84A"
                    
                col_n1.markdown(f"""
                <div style="border-left: 5px solid {cor_produtor}; padding-left: 10px;">
                    <p style="margin:0; font-size:14px; color:#7F8C8D;">Impacto no Frete do Cliente</p>
                    <h4 style="margin:0; color:{cor_produtor};">{status_produtor}</h4>
                    <p style="margin:0; font-size:12px;">Comparado ao Baseline a Diesel</p>
                </div>
                """, unsafe_allow_html=True)
                
                # CARD 2: Faturamento Extra InPlanet
                col_n2.markdown(f"""
                <div style="border-left: 5px solid #F1C40F; padding-left: 10px;">
                    <p style="margin:0; font-size:14px; color:#7F8C8D;">Receita Extra (Créditos de Carbono)</p>
                    <h4 style="margin:0; color:#D4AC0D;">+ R$ {receita_extra_inplanet:,.2f}</h4>
                    <p style="margin:0; font-size:12px;">Faturamento bruto gerado com a redução logística</p>
                </div>
                """, unsafe_allow_html=True)

                # CARD 3: Bônus Máximo por Hectare
                if bonus_maximo_ha > 0:
                    texto_bonus = f"Até R$ {bonus_maximo_ha:,.2f} / ha"
                    cor_bonus = "#2980B9"
                    sub_bonus = "Margem máxima sem prejuízo"
                else:
                    texto_bonus = "Sem Margem Restante"
                    cor_bonus = "#95A5A6"
                    sub_bonus = "A receita não cobre o frete mais caro"

                col_n3.markdown(f"""
                <div style="border-left: 5px solid {cor_bonus}; padding-left: 10px;">
                    <p style="margin:0; font-size:14px; color:#7F8C8D;">Limite de Bonificação ao Produtor</p>
                    <h4 style="margin:0; color:{cor_bonus};">{texto_bonus}</h4>
                    <p style="margin:0; font-size:12px;">{sub_bonus}</p>
                </div>
                """, unsafe_allow_html=True)

    # Gráficos e visualizações padrão mantidos no código final
    st.markdown("---")
    st.subheader("📈 Custos Brutos e Emissões")
    col_g1, col_g2 = st.columns(2)
    df_graficos = pd.DataFrame([
        {"Modalidade": k, "Custo Total (R$)": v['Custo Total'], "Pegada Ecológica (tCO2eq)": v['Emissoes']} 
        for k, v in resumo_modalidades.items()
    ])
    
    with col_g1:
        fig_custos = px.bar(df_graficos, x='Modalidade', y='Custo Total (R$)', color='Modalidade', color_discrete_map=CORES_MODALIDADES, text_auto='.2s')
        fig_custos.update_layout(template="plotly_white", showlegend=False, xaxis_title="")
        st.plotly_chart(fig_custos, use_container_width=True)
        
    with col_g2:
        fig_sustentabilidade = px.bar(df_graficos, x='Modalidade', y='Pegada Ecológica (tCO2eq)', color='Modalidade', color_discrete_map=CORES_MODALIDADES, text_auto='.1f')
        fig_sustentabilidade.update_layout(template="plotly_white", showlegend=False, xaxis_title="")
        st.plotly_chart(fig_sustentabilidade, use_container_width=True)

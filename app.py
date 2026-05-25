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
st.set_page_config(page_title="Simulador InPlanet ESG v2", page_icon="🌿", layout="wide")

# Fatores de Emissão Oficiais (kgCO2eq por L ou m³)
FATORES_EMISSAO = {
    'Diesel B15': 2.70831,
    'Biometano': 0.30620
}

# Consumo Médio Homologado (km por L ou m³)
CONSUMO_MEDIO = {
    'Diesel B15': 2.02,
    'Biometano': 1.90
}

# ==========================================
# BASE DE DADOS COMPLETA (41 PEDREIRAS E ANTT)
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

dados_antt = pd.DataFrame({
    'Modelo': ['LS (6 eixos) - 33t', 'Bi-trem (7 eixos) - 38t', 'Bi-trem (9 eixos) - 50t'],
    'Capacidade_t': [33, 38, 50],
    'Consumo_km_l': [2.5, 2.2, 1.8],
    'Ate_50km': [0.37, 0.35, 0.35],
    'Ate_100km': [0.27, 0.25, 0.26],
    'Acima_100km': [0.24, 0.22, 0.23]
})

dados_pedreiras['Exibicao'] = dados_pedreiras['Mine Name'] + " (" + dados_pedreiras['City'] + " - " + dados_pedreiras['State'] + ")"

# ==========================================
# FUNÇÃO DE EXPORTAÇÃO DE PROPOSTA EM PDF
# ==========================================
def gerar_pdf_comparativo(pedreira, area, dose, toneladas, dist_ida, tabela_resumos):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=80, y=10, w=50)
        pdf.ln(25)
    else:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Proposta Comercial Logistica & ESG - InPlanet", ln=True, align='C')
        pdf.ln(5)
        
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 8, txt="1. Resumo Estrategico da Operacao", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 6, txt=f"Origem do Remineralizador: {pedreira}", ln=True)
    pdf.cell(200, 6, txt=f"Volume Total do Projeto: {toneladas:,.0f} toneladas aplicadas em {area:,.0f} hectares ({dose} t/ha)", ln=True)
    pdf.cell(200, 6, txt=f"Distancia Unidirecional de Ida: {dist_ida:,.1f} km", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 8, txt="2. Quadro Comparativo das Modalidades Selecionadas", ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(45, 7, "Modalidade", 1, 0, 'C')
    pdf.cell(35, 7, "Custo Frete", 1, 0, 'C')
    pdf.cell(25, 7, "R$/Tonelada", 1, 0, 'C')
    pdf.cell(25, 7, "Viagens", 1, 0, 'C')
    pdf.cell(30, 7, "Km Rodados", 1, 0, 'C')
    pdf.cell(30, 7, "Pegada (tCO2)", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 9)
    for k, v in tabela_resumos.items():
        pdf.cell(45, 7, str(k), 1, 0, 'L')
        pdf.cell(35, 7, f"R$ {v['Custo Total']:,.2f}", 1, 0, 'R')
        pdf.cell(25, 7, f"R$ {v['R$/t']:,.2f}", 1, 0, 'R')
        pdf.cell(25, 7, f"{v['Viagens']}", 1, 0, 'C')
        pdf.cell(30, 7, f"{v['Km Total']:,.0f} km", 1, 0, 'R')
        pdf.cell(30, 7, f"{v['Emissoes']:,.2f}", 1, 1, 'R')
        
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(200, 5, txt="Documento confidencial gerado automaticamente pelo Simulador InPlanet ESG.", ln=True, align='C')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
    return pdf_bytes

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
st.title("🌿 Simulador Comercial InPlanet: Otimização de Frete & Ativos ESG")

# CONFIGURAÇÕES DE MERCADO (SIDEBAR)
st.sidebar.header("⚙️ Variáveis Globais de Mercado")
preco_credito_usd = st.sidebar.number_input("Preço Estratégico do Crédito ($/tCDR)", value=300.0)
cotacao_dolar = st.sidebar.number_input("Cotação Cambial (R$/USD)", value=5.00, step=0.10)
valor_credito_brl = preco_credito_usd * cotacao_dolar

st.sidebar.markdown("---")
st.sidebar.header("📋 Seleção de Modalidades para Comparação")
opcoes_ativas = st.sidebar.multiselect(
    "Quais fretes deseja incluir na análise comparativa?",
    ["Preço ANTT (Terceirizado)", "Frete Próprio (Fazenda)", "Frete Retorno (Diesel)", "Operação Biometano (InPlanet)"],
    default=["Preço ANTT (Terceirizado)", "Frete Retorno (Diesel)", "Operação Biometano (InPlanet)"]
)

# SEÇÃO DE INPUTS UNIFICADOS
st.markdown("### 📍 Parâmetros Unificados da Operação")
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    pedreira_selecionada = st.selectbox("Selecione a Pedreira de Origem:", dados_pedreiras['Exibicao'])
    pedreira_dados = dados_pedreiras[dados_pedreiras['Exibicao'] == pedreira_selecionada].iloc[0]
    st.info(f"**Preço de Balança:** R$ {pedreira_dados['Price/ton']:,.2f} / t")

with col_input2:
    distancia_ida_km = st.number_input("Distância de Ida até a Fazenda (km):", value=150.0, step=10.0, min_value=1.0)
    dist_completa_ida_volta = distancia_ida_km * 2

with col_input3:
    area_ha = st.number_input("Área de Aplicação na Fazenda (Hectares):", value=500.0, step=50.0)
    dose_t_ha = st.number_input("Dosagem Recomendada (t/ha):", value=20.0, step=1.0)
    toneladas_totais = area_ha * dose_t_ha
    st.success(f"**Demanda Total:** {toneladas_totais:,.0f} toneladas")

# CONFIGURAÇÕES INTERNAS DE CADA MODALIDADE SELECIONADA
st.markdown("---")
st.markdown("### 🛠️ Especificidades Operacionais por Canal")

config_abas = st.expander("Clique aqui para ajustar os custos internos das modalidades ativas", expanded=True)
with config_abas:
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    
    # 1. Parâmetros ANTT
    with col_c1:
        if "Preço ANTT (Terceirizado)" in opcoes_ativas:
            st.markdown("**🚛 Frete ANTT**")
            modelo_antt = st.selectbox("Modelo do Caminhão:", dados_antt['Modelo'])
            antt_dados = dados_antt[dados_antt['Modelo'] == modelo_antt].iloc[0]
        else:
            st.write("🔒 ANTT Inativa")
            
    # 2. Parâmetros Frete Próprio
    with col_c2:
        if "Frete Próprio (Fazenda)" in opcoes_ativas:
            st.markdown("**🚜 Frete Próprio**")
            preco_diesel = st.number_input("Diesel na Fazenda (R$/L):", value=6.00)
            cap_propria = st.number_input("Capacidade Carga (t):", value=35, key="cap_p")
            cons_proprio = st.number_input("Consumo Médio (km/L):", value=2.5, key="cons_p")
            manut_km_proprio = st.number_input("Manutenção (R$/km):", value=2.00)
            fixos_viagem_proprio = st.number_input("Pedágio + Motorista (R$/Vgo):", value=200.0)
        else:
            st.write("🔒 Frete Próprio Inativo")

    # 3. Parâmetros Frete Retorno
    with col_c3:
        if "Frete Retorno (Diesel)" in opcoes_ativas:
            st.markdown("**🔄 Frete Retorno**")
            valor_ton_retorno = st.number_input("Custo Fechado do Frete (R$/ton):", value=35.0)
            cap_retorno = st.number_input("Capacidade do Caminhão (t):", value=40, key="cap_r")
            cons_retorno = st.number_input("Consumo Médio (km/L):", value=2.02, key="cons_r")
        else:
            st.write("🔒 Frete Retorno Inativo")

    # 4. Parâmetros Biometano
    with col_c4:
        if "Operação Biometano (InPlanet)" in opcoes_ativas:
            st.markdown("**🌱 Operação Biometano**")
            trips_dia_biometano = st.number_input("Meta de Viagens por Dia:", value=3, min_value=1, max_value=10)
        else:
            st.write("🔒 Biometano Inativo")

# ==========================================
# CÁLCULOS MATEMÁTICOS INDIVIDUAIS
# ==========================================
resumo_modalidades = {}

# Cálculo 1: ANTT
if "Preço ANTT (Terceirizado)" in opcoes_ativas:
    cap_antt = antt_dados['Capacidade_t']
    vgs_antt = math.ceil(toneladas_totais / cap_antt)
    km_antt = vgs_antt * dist_completa_ida_volta
    tarifa_antt = antt_dados['Ate_50km'] if distancia_ida_km <= 50 else (antt_dados['Ate_100km'] if distancia_ida_km <= 100 else antt_dados['Acima_100km'])
    custo_antt = toneladas_totais * dist_completa_ida_volta * tarifa_antt
    emis_antt = (km_antt / antt_dados['Consumo_km_l']) * FATORES_EMISSAO['Diesel B15'] / 1000
    
    resumo_modalidades["Preço ANTT (Terceirizado)"] = {
        "Custo Total": custo_antt, "R$/t": custo_antt / toneladas_totais, "Viagens": vgs_antt, "Km Total": km_antt, "Emissoes": emis_antt
    }

# Cálculo 2: Frete Próprio
if "Frete Próprio (Fazenda)" in opcoes_ativas:
    vgs_proprio = math.ceil(toneladas_totais / cap_propria)
    km_proprio = vgs_proprio * dist_completa_ida_volta
    custo_proprio_tot = (km_proprio / cons_proprio * preco_diesel) + (km_proprio * manut_km_proprio) + (vgs_proprio * fixos_viagem_proprio)
    emis_proprio = (km_proprio / cons_proprio) * FATORES_EMISSAO['Diesel B15'] / 1000
    
    resumo_modalidades["Frete Próprio (Fazenda)"] = {
        "Custo Total": custo_proprio_tot, "R$/t": custo_proprio_tot / toneladas_totais, "Viagens": vgs_proprio, "Km Total": km_proprio, "Emissoes": emis_proprio
    }

# Cálculo 3: Frete Retorno (REGRAS EXCLUSIVAS SOLICITADAS)
if "Frete Retorno (Diesel)" in opcoes_ativas:
    custo_retorno_tot = toneladas_totais * valor_ton_retorno
    vgs_retorno = math.ceil(toneladas_totais / cap_retorno)
    # Considerar metade de tudo conforme solicitado (Apenas a distância de ida por viagem)
    km_retorno = vgs_retorno * distancia_ida_km
    emis_retorno = (km_retorno / cons_retorno) * FATORES_EMISSAO['Diesel B15'] / 1000
    
    resumo_modalidades["Frete Retorno (Diesel)"] = {
        "Custo Total": custo_retorno_tot, "R$/t": valor_ton_retorno, "Viagens": vgs_retorno, "Km Total": km_retorno, "Emissoes": emis_retorno
    }

# Cálculo 4: Biometano
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
    
    resumo_modalidades["Operação Biometano (InPlanet)"] = {
        "Custo Total": custo_bio_bruto, "R$/t": custo_bio_bruto / toneladas_totais, "Viagens": vgs_bio, "Km Total": km_bio, "Emissoes": emis_bio
    }

# ==========================================
# PAINEL COMPARATIVO GLOBAL
# ==========================================
if resumo_modalidades:
    st.markdown("---")
    st.subheader("📊 Painel Geral de Comparativos Estratégicos")
    
    # Monta Tabela Consolidada
    dados_tabela_mestre = []
    baseline_emissoes = resumo_modalidades[list(resumo_modalidades.keys())[0]]['Emissoes']
    
    # Procura se ANTT está disponível para ser a base de comparação, se não pega a primeira ativa
    if "Preço ANTT (Terceirizado)" in resumo_modalidades:
        baseline_emissoes = resumo_modalidades["Preço ANTT (Terceirizado)"]['Emissoes']

    for canal, dados in resumo_modalidades.items():
        carbono_salvo = max(0, baseline_emissoes - dados['Emissoes'])
        ativo_financeiro_carbono = carbono_salvo * valor_credito_brl
        custo_liquido_real = dados['Custo Total'] - ativo_financeiro_carbono
        
        dados_tabela_mestre.append({
            "Canal Logístico": canal,
            "Custo Bruto (Frete)": f"R$ {dados['Custo Total']:,.2f}",
            "R$ / Tonelada": f"R$ {dados['R$/t']:,.2f}",
            "Custo / Hectare": f"R$ {dados['Custo Total']/area_ha:,.2f}",
            "Frota (Viagens)": dados['Viagens'],
            "Kilometragem Total": f"{dados['Km Total']:,.0f} km",
            "Pegada de Carbono": f"{dados['Emissoes']:,.1f} tCO2eq",
            "Ativo Carbono Gerado": f"R$ {ativo_financeiro_carbono:,.2f}",
            "Custo Líquido Real (Médio Prazo)": f"R$ {custo_liquido_real:,.2f}"
        })
        
    df_mestre = pd.DataFrame(dados_tabela_mestre)
    st.dataframe(df_mestre, use_container_width=True, hide_index=True)
    
    # GRÁFICOS COMPARATIVOS SIDE-BY-SIDE
    st.markdown("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)
    
    df_graficos = pd.DataFrame([
        {
            "Modalidade": k, 
            "Custo Bruto (R$)": v['Custo Total'], 
            "Pegada Ecológica (tCO2eq)": v['Emissoes'],
            "Ativo Carbono (R$)": max(0, baseline_emissoes - v['Emissoes']) * valor_credito_brl
        } for k, v in resumo_modalidades.items()
    ])
    
    with col_g1:
        fig_custos = px.bar(df_graficos, x='Modalidade', y='Custo Bruto (R$)', 
                            title="Comparativo Financeiro: Desembolso Imediato de Frete",
                            color='Modalidade', color_discrete_sequence=px.colors.qualitative.Dark2)
        st.plotly_chart(fig_custos, use_container_width=True)
        
    with col_g2:
        fig_sustentabilidade = px.bar(df_graficos, x='Modalidade', y='Pegada Ecológica (tCO2eq)', 
                                      title="Comparativo de Sustentabilidade: Pegada de Carbono da Operação",
                                      color='Modalidade', color_discrete_sequence=px.colors.qualitative.Dark2)
        st.plotly_chart(fig_sustentabilidade, use_container_width=True)

    # BOTÃO GERAL DE DOWNLOAD DA PROPOSTA
    st.markdown("---")
    pdf_bytes_comp = gerar_pdf_comparativo(pedreira_selecionada, area_ha, dose_t_ha, toneladas_totais, distancia_ida_km, resumo_modalidades)
    st.download_button(
        label="📄 Baixar Relatório Comparativo de Prateleira (PDF)",
        data=pdf_bytes_comp,
        file_name="Comparativo_Logistica_InPlanet.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.warning("⚠️ Selecione pelo menos uma modalidade logística na barra lateral para exibir a inteligência do dashboard.")

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
# FUNÇÃO DE PDF ATUALIZADA
# ==========================================
def gerar_pdf_analitico(pedreira, area, dose, toneladas, dist_ida, tabela_resumos, fig_custos, fig_sustentabilidade, valor_credito_brl):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=80, y=10, w=50)
        pdf.ln(25)
    else:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Relatorio Analitico: Logistica & ESG", ln=True, align='C')
        pdf.ln(5)
        
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 8, txt="1. Parametros da Operacao", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 6, txt=f"Origem do Produto: {pedreira}", ln=True)
    pdf.cell(200, 6, txt=f"Volume Movimentado: {toneladas:,.0f} toneladas ({dose} t/ha em {area:,.0f} ha)", ln=True)
    pdf.cell(200, 6, txt=f"Distancia do Trajeto (Ida): {dist_ida:,.1f} km", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 8, txt="2. Analise Grafica: Custos x Impacto Ambiental", ln=True)
    pdf.ln(2)
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_c:
            fig_custos.write_image(tmp_c.name, engine="kaleido", width=500, height=350)
            pdf.image(tmp_c.name, x=10, w=90)
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_s:
            fig_sustentabilidade.write_image(tmp_s.name, engine="kaleido", width=500, height=350)
            pdf.image(tmp_s.name, x=105, y=pdf.get_y() - 63, w=90)
    except:
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(200, 10, txt="(Nao foi possivel carregar as imagens neste dispositivo)", ln=True)
    
    pdf.ln(70)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(200, 8, txt="3. Parecer Estrategico dos Resultados e Ativos ESG", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    
    modalidade_mais_barata = min(tabela_resumos, key=lambda k: tabela_resumos[k]['Liquido R$/t'])
    modalidade_mais_limpa = min(tabela_resumos, key=lambda k: tabela_resumos[k]['Emissoes'])
    
    texto_analise = f"Analisando o Custo Liquido (Custo Bruto abatido pela geracao de ativos ambientais), a modalidade mais "
    texto_analise += f"competitiva e a '{modalidade_mais_barata}', com o valor final de R$ {tabela_resumos[modalidade_mais_barata]['Liquido R$/t']:,.2f} por tonelada. "
    texto_analise += f"Ambientalmente, a operacao '{modalidade_mais_limpa}' lidera a descarbonizacao, emitindo apenas {tabela_resumos[modalidade_mais_limpa]['Emissoes']:,.1f} tCO2eq."
    pdf.multi_cell(190, 6, txt=texto_analise)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(50, 7, "Modalidade", 1, 0, 'C')
    pdf.cell(35, 7, "Custo Bruto (R$/t)", 1, 0, 'C')
    pdf.cell(35, 7, "Ativo Gerado (R$/t)", 1, 0, 'C')
    pdf.cell(35, 7, "Custo Liquido (R$/t)", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 9)
    for k, v in tabela_resumos.items():
        pdf.cell(50, 7, str(k), 1, 0, 'L')
        pdf.cell(35, 7, f"R$ {v['R$/t']:,.2f}", 1, 0, 'R')
        pdf.cell(35, 7, f"R$ {v['Retorno R$/t']:,.2f}", 1, 0, 'R')
        pdf.cell(35, 7, f"R$ {v['Liquido R$/t']:,.2f}", 1, 1, 'R')
        
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 5, txt="Documento gerado automaticamente pelo Simulador InPlanet ESG. Baseline: Diesel Ida+Volta (40t).", ln=True, align='C')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
    return pdf_bytes

# ==========================================
# INTERFACE LATERAL (SIDEBAR)
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.header("⚙️ Variáveis de Mercado")
preco_credito_usd = st.sidebar.number_input("Preço Estratégico do Crédito ($/tCDR)", value=300.0)
cotacao_dolar = st.sidebar.number_input("Cotação Cambial (R$/USD)", value=5.00, step=0.10)
valor_credito_brl = preco_credito_usd * cotacao_dolar
st.sidebar.info(f"**Retorno Estimado:** R$ {valor_credito_brl:,.2f} / tCO2 evitada")

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
    km_retorno = vgs_retorno * distancia_ida_km
    emis_retorno = (km_retorno / cons_retorno) * FATORES_EMISSAO['Diesel B15'] / 1000
    resumo_modalidades["Frete Retorno (Diesel)"] = {"Custo Total": custo_retorno_tot, "R$/t": valor_ton_retorno, "Viagens": vgs_retorno, "Km Total": km_retorno, "Emissoes": emis_retorno}

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
    resumo_modalidades["Operação Biometano (InPlanet)"] = {"Custo Total": custo_bio_bruto, "R$/t": custo_bio_bruto / toneladas_totais, "Viagens": vgs_bio_calc, "Km Total": km_bio_calc, "Emissoes": emis_bio}

# APLICAR CÁLCULO DE CRÉDITOS E CUSTO LÍQUIDO GERAL
for mod, dados in resumo_modalidades.items():
    evitado = max(0, emis_baseline_diesel - dados['Emissoes'])
    retorno_reais = evitado * valor_credito_brl
    retorno_ton = retorno_reais / toneladas_totais if toneladas_totais > 0 else 0
    liquido_ton = dados['R$/t'] - retorno_ton
    
    dados['Carbono Evitado'] = evitado
    dados['Retorno R$'] = retorno_reais
    dados['Retorno R$/t'] = retorno_ton
    dados['Liquido R$/t'] = liquido_ton

# ==========================================
# EXIBIÇÃO: CARDS E GRÁFICOS
# ==========================================
if resumo_modalidades:
    st.subheader("💳 Custo Logístico (Bruto vs Líquido com ESG)")
    st.markdown("Comparativo do preço por tonelada antes e depois da geração dos ativos financeiros ambientais.")
    
    menor_custo_liquido_ton = min([d['Liquido R$/t'] for d in resumo_modalidades.values()])
    cols_cards = st.columns(len(resumo_modalidades))
    
    for col, (modalidade, dados) in zip(cols_cards, resumo_modalidades.items()):
        com_trofeu = dados['Liquido R$/t'] == menor_custo_liquido_ton
        bg_color = "#E8F5E9" if com_trofeu else "#F8F9FA"
        border_color = "#2EA84A" if com_trofeu else "#DEE2E6"
        text_color = "#1E8449" if com_trofeu else "#2C3E50"
        trofeu_html = "🏆 <b>Melhor Custo Líquido</b>" if com_trofeu else ""
        
        card_html = f"""
        <div style="background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 10px; padding: 15px; text-align: center; height: 100%;">
            <p style="color: #7F8C8D; font-size: 14px; margin-bottom: 5px;">{modalidade}</p>
            <p style="color: #7F8C8D; font-size: 12px; margin: 0px; text-decoration: line-through;">Bruto: R$ {dados['R$/t']:,.2f}</p>
            <p style="color: #2EA84A; font-size: 12px; margin: 0px;">Ativo ESG: - R$ {dados['Retorno R$/t']:,.2f}</p>
            <h2 style="color: {text_color}; margin-top: 10px; margin-bottom: 5px;">R$ {dados['Liquido R$/t']:,.2f} <span style="font-size: 16px;">/t</span></h2>
            <p style="color: {text_color}; font-size: 12px; margin: 0px;">{trofeu_html}</p>
        </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)

    # Info especial para o Frete Retorno se estiver ativo
    if "Frete Retorno (Diesel)" in opcoes_ativas:
        st.info("💡 **Inteligência Logística:** A modalidade de *Frete Retorno* apresenta alto abatimento de emissões porque aproveita o trajeto ocioso de um caminhão, eliminando a pegada de carbono da viagem de volta. Na prática, a operação corta o impacto e os custos em 50% frente ao frete dedicado comum.")

    st.markdown("---")
    st.subheader("📈 Visão Consolidada: Custos x Pegada Ambiental")
    
    col_g1, col_g2 = st.columns(2)
    df_graficos = pd.DataFrame([
        {"Modalidade": k, "Custo Líquido (R$)": v['Liquido R$/t'] * toneladas_totais, "Pegada Ecológica (tCO2eq)": v['Emissoes']} 
        for k, v in resumo_modalidades.items()
    ])
    
    with col_g1:
        fig_custos = px.bar(df_graficos, x='Modalidade', y='Custo Líquido (R$)', 
                            title="Desembolso Final (Abatido por ESG)",
                            color='Modalidade', color_discrete_map=CORES_MODALIDADES, text_auto='.2s')
        fig_custos.update_layout(template="plotly_white", showlegend=False, xaxis_title="", yaxis_title="Custo Final (R$)", font=dict(family="Arial", size=14))
        fig_custos.update_traces(textposition='outside')
        st.plotly_chart(fig_custos, use_container_width=True)
        
    with col_g2:
        fig_sustentabilidade = px.bar(df_graficos, x='Modalidade', y='Pegada Ecológica (tCO2eq)', 
                                      title="Impacto Ambiental (Ton. de Carbono)",
                                      color='Modalidade', color_discrete_map=CORES_MODALIDADES, text_auto='.1f')
        fig_sustentabilidade.update_layout(template="plotly_white", showlegend=False, xaxis_title="", yaxis_title="Pegada (tCO2eq)", font=dict(family="Arial", size=14))
        fig_sustentabilidade.update_traces(textposition='outside')
        st.plotly_chart(fig_sustentabilidade, use_container_width=True)

    st.markdown("---")
    pdf_bytes_comp = gerar_pdf_analitico(pedreira_selecionada, area_ha, dose_t_ha, toneladas_totais, distancia_ida_km, resumo_modalidades, fig_custos, fig_sustentabilidade, valor_credito_brl)
    st.download_button(
        label="📄 Baixar Relatório Executivo (PDF)",
        data=pdf_bytes_comp,
        file_name="Relatorio_Logistica_ESG_InPlanet.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.warning("⚠️ Selecione pelo menos uma modalidade de frete na barra lateral.")

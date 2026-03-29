"""
Fase 6 — Dashboard Interativo de Sinistralidade (SUSEP)
Disciplina: Manipulação e Análise de Dados Financeiros e Atuariais (MDAF)
Grupo 3
"""

import os
import sqlite3

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Dashboard Sinistralidade SUSEP — MDAF Grupo 3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════
# CSS CUSTOMIZADO — PALETA CLARA E LEGÍVEL
# ════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1565C0 0%, #1E88E5 50%, #42A5F5 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(21, 101, 192, 0.25);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #212840 100%);
        border: 1px solid rgba(100, 181, 246, 0.2);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .kpi-card:hover {
        border-color: rgba(100, 181, 246, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #64B5F6;
        margin: 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.75);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.55);
        margin-top: 0.3rem;
    }

    /* Narrative blocks */
    .narrative-box {
        background: linear-gradient(135deg, #1A2332 0%, #1E2A3A 100%);
        border-left: 4px solid #42A5F5;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
        font-size: 0.92rem;
        line-height: 1.75;
        color: rgba(255,255,255,0.9);
    }
    .narrative-box strong {
        color: #90CAF9;
    }

    /* Section dividers */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(100,181,246,0.3), transparent);
        margin: 2rem 0;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# CARREGAMENTO DOS DADOS (com cache)
# ════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(__file__), "dados", "db", "susep_mdaf.db")


@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega todas as tabelas do banco SQLite."""
    conn = sqlite3.connect(DB_PATH)

    df_mensal = pd.read_sql("SELECT * FROM trusted_susep_sinistralidade_mensal", conn)
    df_resumo_uf = pd.read_sql("SELECT * FROM analytical_resumo_por_uf", conn)
    df_outliers = pd.read_sql("SELECT * FROM analytical_outliers_iqr", conn)
    df_resumo_outliers = pd.read_sql("SELECT * FROM analytical_resumo_outliers", conn)
    df_anual = pd.read_sql("SELECT * FROM analytical_sinistralidade_anual", conn)

    conn.close()

    df_mensal["Data"] = pd.to_datetime(df_mensal["Data"], errors="coerce")
    df_outliers["Data"] = pd.to_datetime(df_outliers["Data"], errors="coerce")

    return df_mensal, df_resumo_uf, df_outliers, df_resumo_outliers, df_anual


df_mensal, df_resumo_uf, df_outliers, df_resumo_outliers, df_anual = carregar_dados()

# ════════════════════════════════════════════════════════════════
# PALETA DE CORES PARA GRÁFICOS
# ════════════════════════════════════════════════════════════════

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E0E0E0", size=13),
)

COR_AZUL = "#42A5F5"         # principal
COR_VERMELHO = "#FF7043"     # alerta (mais quente e legível)
COR_VERDE = "#66BB6A"        # positivo
COR_AMARELO = "#FFA726"      # intermediário
COR_AZUL_CLARO = "#90CAF9"   # preenchimento

# ════════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS GLOBAIS
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    st.markdown("---")

    todas_ufs = sorted(df_mensal["UF"].unique().tolist())
    ufs_selecionadas = st.multiselect(
        "**Unidades Federativas**",
        options=todas_ufs,
        default=todas_ufs,
        help="Selecione as UFs para análise",
    )

    anos_disponiveis = sorted(df_mensal["Ano"].unique().tolist())
    ano_min, ano_max = st.select_slider(
        "**Período (Anos)**",
        options=anos_disponiveis,
        value=(anos_disponiveis[0], anos_disponiveis[-1]),
        help="Escolha o intervalo de anos",
    )

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align:center; opacity:0.6; font-size:0.75rem;'>
            <p><strong>MDAF — Grupo 3</strong></p>
            <p>Fase 6 — Dashboard Interativo</p>
            <p>Dados: SUSEP (Prêmios e Sinistros)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Aplicar filtros
mask = (df_mensal["UF"].isin(ufs_selecionadas)) & (
    df_mensal["Ano"].between(ano_min, ano_max)
)
df_filtrado = df_mensal[mask].copy()

mask_anual = (df_anual["UF"].isin(ufs_selecionadas)) & (
    df_anual["Ano"].between(ano_min, ano_max)
)
df_anual_filtrado = df_anual[mask_anual].copy()

mask_outliers = (df_outliers["UF"].isin(ufs_selecionadas)) & (
    df_outliers["Ano"].between(ano_min, ano_max)
)
df_outliers_filtrado = df_outliers[mask_outliers].copy()

# ════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════

st.markdown(
    """
    <div class="main-header">
        <h1>📊 Dashboard de Sinistralidade — SUSEP</h1>
        <p>Análise interativa de prêmios e sinistros do mercado segurador brasileiro &nbsp;|&nbsp; MDAF — Grupo 3</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ════════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS
# ════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Visão Geral",
        "📈 Série Temporal",
        "🏛️ Análise por UF",
        "⚠️ Outliers",
        "📅 Visão Anual",
    ]
)

# ────────────────────────────────────────────────────────────────
# TAB 1 — VISÃO GERAL (KPIs + Rankings)
# ────────────────────────────────────────────────────────────────
with tab1:
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # Introdução
        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Sobre esta seção:</strong> A Visão Geral apresenta os indicadores-chave de
            desempenho (KPIs) do mercado segurador brasileiro com base nos dados da SUSEP. A
            <em>sinistralidade</em> — razão entre sinistros pagos e prêmios arrecadados — é o principal
            indicador de desempenho técnico utilizado no setor. Valores acima de 100% indicam prejuízo
            operacional. Os filtros na barra lateral permitem selecionar UFs e períodos específicos.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # KPIs
        sinistralidade_media = df_filtrado["Sinistralidade"].mean()
        premio_total = df_filtrado["Prêmio Direto (R$)"].sum()
        sinistro_total = df_filtrado["Sinistro Direto (R$)"].sum()
        total_registros = len(df_filtrado)
        n_outliers = len(df_outliers_filtrado)

        ranking = (
            df_filtrado.groupby("UF", as_index=False)["Sinistralidade"]
            .mean()
            .sort_values("Sinistralidade", ascending=False)
            .reset_index(drop=True)
        )
        uf_maior = ranking.iloc[0]
        uf_menor = ranking.iloc[-1]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Sinistralidade Média</div>
                    <div class="kpi-value">{sinistralidade_media:.2%}</div>
                    <div class="kpi-sub">{total_registros:,} registros</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Prêmio Total</div>
                    <div class="kpi-value">R$ {premio_total/1e9:.2f}B</div>
                    <div class="kpi-sub">{len(ufs_selecionadas)} UFs selecionadas</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Sinistro Total</div>
                    <div class="kpi-value">R$ {sinistro_total/1e9:.2f}B</div>
                    <div class="kpi-sub">{'⚠️ Excede prêmio' if sinistro_total > premio_total else '✅ Dentro do prêmio'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Outliers Detectados</div>
                    <div class="kpi-value">{n_outliers}</div>
                    <div class="kpi-sub">Método IQR</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Cards UF maior e menor
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid {COR_VERMELHO};">
                    <div class="kpi-label">🔴 Maior Sinistralidade Média</div>
                    <div class="kpi-value" style="color:{COR_VERMELHO};">{uf_maior['UF']} — {uf_maior['Sinistralidade']:.2%}</div>
                    <div class="kpi-sub">Estado com maior razão sinistro/prêmio no período</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid {COR_VERDE};">
                    <div class="kpi-label">🟢 Menor Sinistralidade Média</div>
                    <div class="kpi-value" style="color:{COR_VERDE};">{uf_menor['UF']} — {uf_menor['Sinistralidade']:.2%}</div>
                    <div class="kpi-sub">Estado com melhor equilíbrio atuarial no período</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Ranking horizontal
        st.subheader("Ranking de Sinistralidade Média por UF")

        cores = [
            COR_VERMELHO if v > 1 else COR_AMARELO if v > 0.7 else COR_VERDE
            for v in ranking["Sinistralidade"]
        ]

        fig_ranking = go.Figure(
            go.Bar(
                x=ranking["Sinistralidade"],
                y=ranking["UF"],
                orientation="h",
                marker_color=cores,
                text=[f"{v:.1%}" for v in ranking["Sinistralidade"]],
                textposition="outside",
                textfont=dict(size=12, color="#E0E0E0"),
            )
        )
        fig_ranking.add_vline(
            x=1.0,
            line_dash="dash",
            line_color=COR_VERMELHO,
            annotation_text="100% (equilíbrio)",
            annotation_position="top",
            annotation_font=dict(color="#E0E0E0", size=12),
        )
        fig_ranking.update_layout(
            yaxis=dict(autorange="reversed"),
            height=max(550, len(ranking) * 24),
            margin=dict(l=10, r=80, t=20, b=20),
            xaxis=dict(title="Sinistralidade Média"),
            yaxis_title=None,
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

        st.markdown(
            f"""
            <div class="narrative-box">
            <strong>📌 Interpretação do Ranking:</strong> O gráfico acima ordena as {len(ranking)} UFs pela
            sinistralidade média no período de {ano_min} a {ano_max}. As barras em
            <span style="color:{COR_VERMELHO};font-weight:600;">laranja-avermelhado</span> indicam UFs com
            sinistralidade acima de 100%, ou seja, estados onde os sinistros pagos superaram os prêmios
            arrecadados — configurando <strong>desequilíbrio atuarial</strong>. Barras em
            <span style="color:{COR_AMARELO};font-weight:600;">amarelo</span> representam sinistralidade
            entre 70% e 100% (zona de atenção), e barras em
            <span style="color:{COR_VERDE};font-weight:600;">verde</span> indicam sinistralidade abaixo
            de 70% (mercado mais estável). A linha tracejada marca o ponto de equilíbrio (100%), onde
            prêmios e sinistros se igualam. Do ponto de vista da gestão atuarial, UFs com sinistralidade
            persistentemente alta sinalizam necessidade de <strong>reprecificação</strong>,
            <strong>adequação de reservas técnicas</strong> e investigação de fatores de risco regionais.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ────────────────────────────────────────────────────────────────
# TAB 2 — SÉRIE TEMPORAL
# ────────────────────────────────────────────────────────────────
with tab2:
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Sobre esta seção:</strong> A análise temporal permite acompanhar a evolução
            da sinistralidade ao longo do tempo, identificando tendências, sazonalidades e eventos
            atípicos. A série mensal agregada do Brasil oferece uma visão macro do comportamento do
            mercado segurador, enquanto a comparação entre UFs revela dinâmicas regionais distintas.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Sinistralidade Mensal Média — Brasil")

        serie_brasil = (
            df_filtrado.groupby("Data", as_index=False)["Sinistralidade"]
            .mean()
            .sort_values("Data")
        )

        fig_serie = go.Figure()
        fig_serie.add_trace(
            go.Scatter(
                x=serie_brasil["Data"],
                y=serie_brasil["Sinistralidade"],
                mode="lines",
                name="Sinistralidade Média",
                line=dict(color=COR_AZUL, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(66,165,245,0.1)",
                hovertemplate="<b>%{x|%b %Y}</b><br>Sinistralidade: %{y:.2%}<extra></extra>",
            )
        )
        fig_serie.add_hline(
            y=1.0,
            line_dash="dash",
            line_color=COR_VERMELHO,
            annotation_text="100% — Ponto de equilíbrio",
            annotation_position="top left",
            annotation_font=dict(color="#E0E0E0", size=12),
        )
        fig_serie.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(title="Data"),
            yaxis=dict(title="Sinistralidade", tickformat=".0%"),
            showlegend=False,
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig_serie, use_container_width=True)

        # Estatísticas complementares da série
        media_periodo = serie_brasil["Sinistralidade"].mean()
        meses_acima = (serie_brasil["Sinistralidade"] > 1.0).sum()
        total_meses = len(serie_brasil)

        st.markdown(
            f"""
            <div class="narrative-box">
            <strong>📌 Interpretação da Série Temporal:</strong> No período analisado ({ano_min}–{ano_max}),
            a sinistralidade mensal média do Brasil foi de <strong>{media_periodo:.2%}</strong>.
            Dos {total_meses} meses observados, <strong>{meses_acima} meses</strong> apresentaram sinistralidade
            acima de 100%, indicando desequilíbrio técnico. Picos na série podem estar relacionados a
            eventos climáticos extremos, sazonalidade de sinistros (ex.: períodos chuvosos aumentam acidentes
            de trânsito), ou choques econômicos que afetam a frequência e severidade dos sinistros. Para o
            atuário, compreender esses padrões é fundamental para o <strong>dimensionamento de reservas técnicas</strong>,
            a <strong>precificação prospectiva</strong> e a <strong>gestão de solvência</strong> das seguradoras.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Série por UF individual
        st.subheader("Comparação da Sinistralidade Mensal por UF")

        ufs_para_comparar = st.multiselect(
            "Selecione UFs para comparar:",
            options=sorted(df_filtrado["UF"].unique()),
            default=sorted(df_filtrado["UF"].unique())[:3],
            key="serie_uf_select",
        )

        if ufs_para_comparar:
            df_serie_uf = df_filtrado[df_filtrado["UF"].isin(ufs_para_comparar)]

            fig_uf = px.line(
                df_serie_uf,
                x="Data",
                y="Sinistralidade",
                color="UF",
                labels={"Sinistralidade": "Sinistralidade", "Data": "Data"},
                hover_data={"Sinistralidade": ":.2%"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_uf.add_hline(
                y=1.0,
                line_dash="dash",
                line_color=COR_VERMELHO,
                annotation_text="100%",
                annotation_font=dict(color="#E0E0E0"),
            )
            fig_uf.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=30, b=10),
                yaxis=dict(tickformat=".0%"),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12),
                ),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_uf, use_container_width=True)

            st.markdown(
                """
                <div class="narrative-box">
                <strong>📌 Comparativo Regional:</strong> Este gráfico permite identificar diferenças
                no comportamento temporal da sinistralidade entre estados. UFs com trajetórias mais voláteis
                possuem maior incerteza atuarial, enquanto UFs com séries mais suaves oferecem maior
                previsibilidade para a projeção de reservas. Convergências ou divergências entre curvas
                podem indicar fatores regulatórios ou econômicos comuns vs. especificidades regionais.
                </div>
                """,
                unsafe_allow_html=True,
            )

# ────────────────────────────────────────────────────────────────
# TAB 3 — ANÁLISE POR UF
# ────────────────────────────────────────────────────────────────
with tab3:
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Sobre esta seção:</strong> Esta aba apresenta o perfil estatístico detalhado de cada
            UF: medidas de tendência central (média, mediana), dispersão (desvio padrão, IQR, coeficiente
            de variação) e limites para detecção de outliers. A análise por UF é fundamental para a
            segmentação de risco, permitindo ao atuário identificar mercados homogêneos vs. heterogêneos.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Estatísticas descritivas
        st.subheader("Estatísticas Descritivas por UF")

        resumo_display = df_resumo_uf[df_resumo_uf["UF"].isin(ufs_selecionadas)].copy()
        resumo_display = resumo_display.sort_values(
            "Sinistralidade_Media", ascending=False
        )

        cols_pct = [
            "Sinistralidade_Media", "Sinistralidade_Mediana",
            "Sinistralidade_Min", "Sinistralidade_Max",
            "Q1", "Q3", "Limite_Inferior", "Limite_Superior",
        ]
        cols_dec = ["Desvio_Padrao", "IQR", "CV"]

        resumo_fmt = resumo_display.copy()
        for c in cols_pct:
            if c in resumo_fmt.columns:
                resumo_fmt[c] = resumo_fmt[c].apply(lambda x: f"{x:.2%}")
        for c in cols_dec:
            if c in resumo_fmt.columns:
                resumo_fmt[c] = resumo_fmt[c].apply(lambda x: f"{x:.4f}")

        st.dataframe(resumo_fmt, use_container_width=True, hide_index=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Como ler esta tabela:</strong>
            • <strong>Sinistralidade Média/Mediana:</strong> Indicam o nível típico de sinistralidade. Grandes diferenças
            entre média e mediana sugerem assimetria (influência de valores extremos).<br>
            • <strong>Desvio Padrão e CV:</strong> Medem a variabilidade. Um CV alto (> 0.5) indica risco heterogêneo, mais difícil de precificar.<br>
            • <strong>Q1, Q3, IQR:</strong> Quartis e amplitude interquartil — base para detecção de outliers pelo método IQR.<br>
            • <strong>Limites Inf./Sup.:</strong> Q1 - 1.5×IQR e Q3 + 1.5×IQR. Valores fora desses limites são considerados outliers.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Boxplot
        st.subheader("Distribuição da Sinistralidade por UF")

        fig_box = px.box(
            df_filtrado,
            x="UF",
            y="Sinistralidade",
            color="UF",
            labels={"Sinistralidade": "Sinistralidade", "UF": "UF"},
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig_box.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO)
        fig_box.update_layout(
            height=520,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False,
            xaxis=dict(title="UF", categoryorder="total descending"),
            yaxis=dict(title="Sinistralidade", tickformat=".0%"),
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig_box, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Interpretação do Boxplot:</strong> Cada caixa representa a faixa interquartil (Q1–Q3)
            da sinistralidade mensal de cada UF. A linha central é a mediana. Os "bigodes" se estendem
            até 1,5×IQR e os pontos além são outliers. UFs com caixas mais largas possuem maior dispersão
            (risco heterogêneo). Caixas posicionadas acima da linha de 100% indicam UFs com desequilíbrio.
            UFs com muitos pontos acima dos bigodes são propensas a eventos extremos — um elemento crucial
            para o <strong>carregamento de segurança nas tarifas</strong> e <strong>constituição de reservas</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Dispersão Prêmio vs Sinistro
        col_disp, col_corr = st.columns(2)

        with col_disp:
            st.subheader("Prêmio vs Sinistro")

            fig_scatter = px.scatter(
                df_filtrado,
                x="Prêmio Direto (R$)",
                y="Sinistro Direto (R$)",
                color="UF",
                opacity=0.55,
                hover_data={"Sinistralidade": ":.2%"},
                trendline="ols",
                labels={
                    "Prêmio Direto (R$)": "Prêmio Direto (R$)",
                    "Sinistro Direto (R$)": "Sinistro Direto (R$)",
                },
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_scatter.update_layout(
                height=480,
                margin=dict(l=10, r=10, t=30, b=10),
                showlegend=False,
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_corr:
            st.subheader("Correlação de Spearman")

            corr_cols = ["Prêmio Direto (R$)", "Sinistro Direto (R$)", "Sinistralidade"]
            corr_matrix = df_filtrado[corr_cols].corr(method="spearman")

            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".3f",
                color_continuous_scale="Blues",
                labels=dict(color="Correlação"),
                aspect="equal",
            )
            fig_corr.update_traces(textfont=dict(size=14, color="white"))
            fig_corr.update_layout(
                height=480,
                margin=dict(l=10, r=10, t=30, b=10),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        corr_premio_sinistro = corr_matrix.loc["Prêmio Direto (R$)", "Sinistro Direto (R$)"]
        corr_premio_ratio = corr_matrix.loc["Prêmio Direto (R$)", "Sinistralidade"]

        st.markdown(
            f"""
            <div class="narrative-box">
            <strong>📌 Análise da Dispersão e Correlação:</strong><br>
            • <strong>Gráfico de Dispersão:</strong> Cada ponto representa uma observação mensal (UF × mês).
            Pontos acima da linha de tendência linear possuem sinistros proporcionalmente maiores que o esperado.
            A reta de regressão OLS indica a relação média — sua inclinação reflete o percentual médio de sinistro
            por real de prêmio.<br><br>
            • <strong>Matriz de Correlação (Spearman):</strong> A correlação entre Prêmio e Sinistro é de
            <strong>{corr_premio_sinistro:.3f}</strong>, confirmando que mercados maiores geram mais sinistros
            (relação esperada). Já a correlação entre Prêmio e Sinistralidade (razão) é de
            <strong>{corr_premio_ratio:.3f}</strong> — valores próximos de zero sugerem que o tamanho do mercado
            <em>não determina</em> a eficiência na gestão de risco. Escolhemos Spearman (ao invés de Pearson)
            por ser mais robusta a outliers e relações não-lineares.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ────────────────────────────────────────────────────────────────
# TAB 4 — OUTLIERS
# ────────────────────────────────────────────────────────────────
with tab4:
    if df_outliers_filtrado.empty:
        st.info("Nenhum outlier encontrado para os filtros selecionados.")
    else:
        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Sobre esta seção:</strong> Outliers são observações que se desviam significativamente
            do comportamento esperado. Neste projeto, utilizamos o <strong>método IQR</strong> (amplitude
            interquartil) para detectá-los: valores acima de Q3 + 1.5×IQR são classificados como outliers
            superiores e abaixo de Q1 − 1.5×IQR como inferiores. A identificação de outliers é essencial
            na modelagem atuarial, pois eventos extremos impactam diretamente as reservas técnicas.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Outliers Identificados — Método IQR")

        # Contagem por UF
        resumo_o = df_resumo_outliers[
            df_resumo_outliers["UF"].isin(ufs_selecionadas)
        ].copy()

        n_sup = len(
            df_outliers_filtrado[df_outliers_filtrado["Tipo_Outlier"] == "Superior"]
        )
        n_inf = len(
            df_outliers_filtrado[df_outliers_filtrado["Tipo_Outlier"] == "Inferior"]
        )

        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total de Outliers</div>
                    <div class="kpi-value">{len(df_outliers_filtrado)}</div>
                    <div class="kpi-sub">{len(df_outliers_filtrado)/len(df_filtrado)*100:.1f}% dos registros</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_o2:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid {COR_VERMELHO};">
                    <div class="kpi-label">Outliers Superiores</div>
                    <div class="kpi-value" style="color:{COR_VERMELHO};">{n_sup}</div>
                    <div class="kpi-sub">Sinistralidade acima do esperado</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_o3:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid {COR_VERDE};">
                    <div class="kpi-label">Outliers Inferiores</div>
                    <div class="kpi-value" style="color:{COR_VERDE};">{n_inf}</div>
                    <div class="kpi-sub">Sinistralidade abaixo do esperado</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Gráfico de outliers por UF
        st.subheader("Distribuição de Outliers por UF")

        outlier_count = (
            df_outliers_filtrado.groupby(["UF", "Tipo_Outlier"])
            .size()
            .reset_index(name="Quantidade")
        )

        color_map = {"Superior": COR_VERMELHO, "Inferior": COR_VERDE}

        fig_outliers = px.bar(
            outlier_count,
            x="UF",
            y="Quantidade",
            color="Tipo_Outlier",
            barmode="group",
            color_discrete_map=color_map,
            labels={"Quantidade": "Nº de Outliers", "Tipo_Outlier": "Tipo"},
        )
        fig_outliers.update_layout(
            height=440,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(title="UF", categoryorder="total descending"),
            yaxis=dict(title="Quantidade"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=12),
            ),
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig_outliers, use_container_width=True)

        # UF com mais outliers
        uf_mais_outliers = outlier_count.groupby("UF")["Quantidade"].sum().idxmax()
        qtd_mais = outlier_count.groupby("UF")["Quantidade"].sum().max()

        st.markdown(
            f"""
            <div class="narrative-box">
            <strong>📌 Interpretação dos Outliers por UF:</strong> A UF com maior número de outliers é
            <strong>{uf_mais_outliers}</strong> ({qtd_mais} ocorrências), indicando que este estado apresenta
            maior frequência de meses com comportamento atípico. Outliers superiores (barras em
            <span style="color:{COR_VERMELHO};font-weight:600;">laranja</span>) são os mais preocupantes
            do ponto de vista atuarial, pois representam meses em que a sinistralidade excedeu
            significativamente o padrão — podendo indicar fraudes, eventos catastróficos ou concentração
            de sinistros de grande severidade. Os outliers inferiores (barras em
            <span style="color:{COR_VERDE};font-weight:600;">verde</span>) indicam meses onde houve
            menos sinistralidade do que o esperado, o que pode ser positivo, mas também deve ser
            investigado para assegurar que não reflitam sub-registro de sinistros.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Tabela detalhada de outliers
        st.subheader("Detalhamento dos Outliers")

        tipo_filtro = st.selectbox(
            "Filtrar por tipo:",
            options=["Todos", "Superior", "Inferior"],
            key="outlier_tipo",
        )

        df_out_show = df_outliers_filtrado.copy()
        if tipo_filtro != "Todos":
            df_out_show = df_out_show[df_out_show["Tipo_Outlier"] == tipo_filtro]

        df_out_show_fmt = df_out_show[
            [
                "UF", "Competência",
                "Prêmio Direto (R$)", "Sinistro Direto (R$)",
                "Sinistralidade", "Tipo_Outlier", "Desvio_Limite",
            ]
        ].copy()
        df_out_show_fmt["Sinistralidade"] = df_out_show_fmt["Sinistralidade"].apply(
            lambda x: f"{x:.2%}"
        )
        df_out_show_fmt["Desvio_Limite"] = df_out_show_fmt["Desvio_Limite"].apply(
            lambda x: f"{x:.4f}"
        )

        st.dataframe(df_out_show_fmt, use_container_width=True, hide_index=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Leitura da tabela:</strong> A coluna <em>Desvio_Limite</em> mostra o quanto cada
            observação se afasta do limite IQR. Quanto maior o desvio, mais extremo é o evento. Na
            prática atuarial, esses registros são candidatos a tratamento especial: podem ser excluídos
            da base de precificação (se forem eventos não-recorrentes) ou modelados separadamente
            (se forem riscos catastróficos que exigem provisão específica). A decisão depende da
            natureza do outlier e do contexto de cada UF.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ────────────────────────────────────────────────────────────────
# TAB 5 — VISÃO ANUAL
# ────────────────────────────────────────────────────────────────
with tab5:
    if df_anual_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Sobre esta seção:</strong> A visão anual agrega os dados mensais em base anual,
            suavizando oscilações de curto prazo e revelando tendências estruturais do mercado segurador.
            Essa perspectiva é fundamental para a projeção de reservas, adequação de prêmios futuros e
            avaliação da sustentabilidade financeira do setor em cada UF.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Sinistralidade Anual Média — Brasil")

        anual_media = (
            df_anual_filtrado.groupby("Ano", as_index=False)["Sinistralidade_Anual"]
            .mean()
            .sort_values("Ano")
        )

        fig_anual = go.Figure()
        fig_anual.add_trace(
            go.Scatter(
                x=anual_media["Ano"],
                y=anual_media["Sinistralidade_Anual"],
                mode="lines+markers",
                name="Sinistralidade Anual Média",
                line=dict(color=COR_AZUL, width=3),
                marker=dict(size=10, color=COR_AZUL, line=dict(width=2, color="#1565C0")),
                hovertemplate="<b>%{x}</b><br>Sinistralidade: %{y:.2%}<extra></extra>",
            )
        )
        fig_anual.add_hline(
            y=1.0,
            line_dash="dash",
            line_color=COR_VERMELHO,
            annotation_text="100%",
            annotation_font=dict(color="#E0E0E0", size=12),
        )
        fig_anual.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(title="Ano", dtick=1),
            yaxis=dict(title="Sinistralidade Anual", tickformat=".0%"),
            showlegend=False,
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig_anual, use_container_width=True)

        # Tendência
        melhor_ano = anual_media.loc[anual_media["Sinistralidade_Anual"].idxmin()]
        pior_ano = anual_media.loc[anual_media["Sinistralidade_Anual"].idxmax()]

        st.markdown(
            f"""
            <div class="narrative-box">
            <strong>📌 Interpretação da Evolução Anual:</strong> O gráfico mostra a média da sinistralidade
            anual agregada das UFs selecionadas. O <strong>melhor ano</strong> foi
            <strong>{int(melhor_ano['Ano'])}</strong> (sinistralidade de {melhor_ano['Sinistralidade_Anual']:.2%}),
            enquanto o <strong>pior ano</strong> foi <strong>{int(pior_ano['Ano'])}</strong>
            ({pior_ano['Sinistralidade_Anual']:.2%}). Variações interanuais podem refletir: mudanças
            regulatórias que alteraram a composição dos prêmios; eventos climáticos ou econômicos que
            elevaram os sinistros; ou ajustes de precificação implementados pelas seguradoras. Para a
            gestão atuarial, a tendência de longo prazo é mais relevante que oscilações pontuais, pois
            permite antecipar necessidades de recapitalização e ajuste de produtos.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Tabela anual detalhada
        st.subheader("Detalhamento Anual por UF")

        uf_anual_select = st.multiselect(
            "Selecione UFs:",
            options=sorted(df_anual_filtrado["UF"].unique()),
            default=sorted(df_anual_filtrado["UF"].unique())[:5],
            key="anual_uf_select",
        )

        if uf_anual_select:
            df_anual_show = df_anual_filtrado[
                df_anual_filtrado["UF"].isin(uf_anual_select)
            ].copy()
            df_anual_show = df_anual_show.sort_values(["UF", "Ano"])

            df_anual_fmt = df_anual_show.copy()
            df_anual_fmt["Premio_Total"] = df_anual_fmt["Premio_Total"].apply(
                lambda x: f"R$ {x:,.2f}"
            )
            df_anual_fmt["Sinistro_Total"] = df_anual_fmt["Sinistro_Total"].apply(
                lambda x: f"R$ {x:,.2f}"
            )
            df_anual_fmt["Sinistralidade_Anual"] = df_anual_fmt[
                "Sinistralidade_Anual"
            ].apply(lambda x: f"{x:.2%}")

            st.dataframe(df_anual_fmt, use_container_width=True, hide_index=True)

            # Gráfico de linhas por UF
            st.subheader("Evolução Anual por UF")

            fig_anual_uf = px.line(
                df_anual_show,
                x="Ano",
                y="Sinistralidade_Anual",
                color="UF",
                markers=True,
                labels={
                    "Sinistralidade_Anual": "Sinistralidade Anual",
                    "Ano": "Ano",
                },
                hover_data={"Sinistralidade_Anual": ":.2%"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_anual_uf.add_hline(y=1.0, line_dash="dash", line_color=COR_VERMELHO)
            fig_anual_uf.update_layout(
                height=460,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(dtick=1),
                yaxis=dict(tickformat=".0%"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12),
                ),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_anual_uf, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Perspectiva de Longo Prazo:</strong> A análise anual por UF permite identificar
            estados com trajetórias de melhoria (sinistralidade decrescente) vs. estados em deterioração.
            Cruzando com a tabela detalhada dos valores absolutos de prêmios e sinistros, é possível
            distinguir se mudanças na sinistralidade decorrem de aumento de sinistros ou de queda nos
            prêmios — diagnósticos que levam a estratégias atuariais distintas. UFs com sinistralidade
            anual sistematicamente acima de 100% podem estar em espiral negativa: prêmios aumentam
            (para cobrir perdas), segurados migram, e o pool de risco se deteriora — um fenômeno
            conhecido como <strong>seleção adversa</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

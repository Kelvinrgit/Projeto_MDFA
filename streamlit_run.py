"""
Fase 5 — Dashboard Interativo de Sinistralidade (SUSEP)
Disciplina: Manipulação e Análise de Dados Financeiros e Atuariais (MDAF)
Grupo 3
"""

import os
import sqlite3

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# CSS CUSTOMIZADO
# ════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0D47A1 0%, #1565C0 50%, #42A5F5 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(13, 71, 161, 0.3);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #1E2538 100%);
        border: 1px solid rgba(79, 195, 247, 0.15);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }
    .kpi-card:hover {
        border-color: rgba(79, 195, 247, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #4FC3F7;
        margin: 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: rgba(250,250,250,0.6);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 500;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: rgba(250,250,250,0.45);
        margin-top: 0.3rem;
    }

    /* Narrative blocks */
    .narrative-box {
        background: linear-gradient(135deg, #1A1F2E 0%, #1E2538 100%);
        border-left: 4px solid #4FC3F7;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        line-height: 1.7;
        color: rgba(250,250,250,0.85);
    }

    /* Section dividers */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(79,195,247,0.3), transparent);
        margin: 2rem 0;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0E1117 0%, #151A28 100%);
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

    # Converter coluna Data
    df_mensal["Data"] = pd.to_datetime(df_mensal["Data"], errors="coerce")
    df_outliers["Data"] = pd.to_datetime(df_outliers["Data"], errors="coerce")

    return df_mensal, df_resumo_uf, df_outliers, df_resumo_outliers, df_anual


df_mensal, df_resumo_uf, df_outliers, df_resumo_outliers, df_anual = carregar_dados()

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
        <div style='text-align:center; opacity:0.5; font-size:0.75rem;'>
            <p><strong>MDAF — Grupo 3</strong></p>
            <p>Fase 5 — Dashboard Interativo</p>
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
                <div class="kpi-card" style="border-left: 4px solid #EF5350;">
                    <div class="kpi-label">🔴 Maior Sinistralidade Média</div>
                    <div class="kpi-value">{uf_maior['UF']} — {uf_maior['Sinistralidade']:.2%}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid #66BB6A;">
                    <div class="kpi-label">🟢 Menor Sinistralidade Média</div>
                    <div class="kpi-value">{uf_menor['UF']} — {uf_menor['Sinistralidade']:.2%}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Ranking horizontal
        st.subheader("Ranking de Sinistralidade Média por UF")

        cores = [
            "#EF5350" if v > 1 else "#FFA726" if v > 0.7 else "#66BB6A"
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
                textfont=dict(size=11),
            )
        )
        fig_ranking.add_vline(
            x=1.0,
            line_dash="dash",
            line_color="#EF5350",
            annotation_text="100% (equilíbrio)",
            annotation_position="top",
        )
        fig_ranking.update_layout(
            yaxis=dict(autorange="reversed"),
            height=max(500, len(ranking) * 22),
            margin=dict(l=10, r=60, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            xaxis=dict(
                title="Sinistralidade Média",
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis_title=None,
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Contexto Atuarial:</strong> A sinistralidade (razão sinistro/prêmio) é o principal indicador
            de desempenho técnico do mercado segurador. Valores acima de 100% indicam que os sinistros pagos
            superam os prêmios arrecadados, sinalizando <strong>desequilíbrio atuarial</strong> e potencial
            necessidade de reprecificação de riscos. UFs com sinistralidade persistentemente alta podem refletir
            concentração de riscos, preços inadequados ou eventos catastróficos.
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
                line=dict(color="#4FC3F7", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(79,195,247,0.08)",
                hovertemplate="<b>%{x|%b %Y}</b><br>Sinistralidade: %{y:.2%}<extra></extra>",
            )
        )
        fig_serie.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#EF5350",
            annotation_text="100% — Ponto de equilíbrio",
            annotation_position="top left",
        )
        fig_serie.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            xaxis=dict(title="Data", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(
                title="Sinistralidade",
                tickformat=".0%",
                gridcolor="rgba(255,255,255,0.05)",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_serie, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Interpretação:</strong> A série temporal do Brasil revela a dinâmica agregada da sinistralidade
            ao longo do tempo. Picos acima de 100% indicam períodos em que o mercado esteve deficitário.
            Oscilações sazonais podem refletir concentração de sinistros em determinados meses (ex.: aumento
            de acidentes de trânsito ou eventos climáticos). A tendência de longo prazo é crucial para
            a <strong>precificação atuarial</strong> e o <strong>dimensionamento de reservas técnicas</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Série por UF individual
        st.subheader("Sinistralidade Mensal por UF")

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
            )
            fig_uf.add_hline(
                y=1.0,
                line_dash="dash",
                line_color="#EF5350",
                annotation_text="100%",
            )
            fig_uf.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(
                    tickformat=".0%", gridcolor="rgba(255,255,255,0.05)"
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig_uf, use_container_width=True)

# ────────────────────────────────────────────────────────────────
# TAB 3 — ANÁLISE POR UF
# ────────────────────────────────────────────────────────────────
with tab3:
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # Estatísticas descritivas
        st.subheader("Estatísticas Descritivas por UF")

        resumo_display = df_resumo_uf[df_resumo_uf["UF"].isin(ufs_selecionadas)].copy()
        resumo_display = resumo_display.sort_values(
            "Sinistralidade_Media", ascending=False
        )

        # Formatação para exibição
        cols_pct = [
            "Sinistralidade_Media",
            "Sinistralidade_Mediana",
            "Sinistralidade_Min",
            "Sinistralidade_Max",
            "Q1",
            "Q3",
            "Limite_Inferior",
            "Limite_Superior",
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

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Boxplot
        st.subheader("Distribuição da Sinistralidade por UF")

        fig_box = px.box(
            df_filtrado,
            x="UF",
            y="Sinistralidade",
            color="UF",
            labels={"Sinistralidade": "Sinistralidade", "UF": "UF"},
        )
        fig_box.add_hline(y=1.0, line_dash="dash", line_color="#EF5350")
        fig_box.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            showlegend=False,
            xaxis=dict(
                title="UF",
                categoryorder="total descending",
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis=dict(
                title="Sinistralidade",
                tickformat=".0%",
                gridcolor="rgba(255,255,255,0.05)",
            ),
        )
        st.plotly_chart(fig_box, use_container_width=True)

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
                opacity=0.6,
                hover_data={"Sinistralidade": ":.2%"},
                trendline="ols",
                labels={
                    "Prêmio Direto (R$)": "Prêmio Direto (R$)",
                    "Sinistro Direto (R$)": "Sinistro Direto (R$)",
                },
            )
            fig_scatter.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                showlegend=False,
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
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
            fig_corr.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Análise Estatística:</strong> O boxplot evidencia a dispersão e assimetria da
            sinistralidade por UF, permitindo identificar estados com alta variabilidade de risco.
            A correlação de Spearman entre prêmio e sinistro deve ser alta (próxima de 1), pois mercados
            maiores naturalmente geram mais sinistros. Porém, a correlação com a sinistralidade (razão)
            pode revelar se mercados maiores são mais ou menos eficientes na gestão de risco.
            O coeficiente de variação (CV) é um indicador útil de <strong>homogeneidade do risco</strong>
            dentro de cada UF.
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
        st.subheader("Outliers Identificados — Método IQR")

        # Contagem por UF
        resumo_o = df_resumo_outliers[
            df_resumo_outliers["UF"].isin(ufs_selecionadas)
        ].copy()

        col_o1, col_o2, col_o3 = st.columns(3)
        with col_o1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total de Outliers</div>
                    <div class="kpi-value">{len(df_outliers_filtrado)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_o2:
            n_sup = len(
                df_outliers_filtrado[df_outliers_filtrado["Tipo_Outlier"] == "Superior"]
            )
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid #EF5350;">
                    <div class="kpi-label">Outliers Superiores</div>
                    <div class="kpi-value" style="color:#EF5350;">{n_sup}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_o3:
            n_inf = len(
                df_outliers_filtrado[df_outliers_filtrado["Tipo_Outlier"] == "Inferior"]
            )
            st.markdown(
                f"""
                <div class="kpi-card" style="border-left: 4px solid #66BB6A;">
                    <div class="kpi-label">Outliers Inferiores</div>
                    <div class="kpi-value" style="color:#66BB6A;">{n_inf}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # Gráfico de outliers por UF
        st.subheader("Outliers por UF")

        outlier_count = (
            df_outliers_filtrado.groupby(["UF", "Tipo_Outlier"])
            .size()
            .reset_index(name="Quantidade")
        )

        color_map = {"Superior": "#EF5350", "Inferior": "#66BB6A"}

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
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            xaxis=dict(
                title="UF",
                categoryorder="total descending",
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis=dict(title="Quantidade", gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig_outliers, use_container_width=True)

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
                "UF",
                "Competência",
                "Prêmio Direto (R$)",
                "Sinistro Direto (R$)",
                "Sinistralidade",
                "Tipo_Outlier",
                "Desvio_Limite",
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
            <strong>📌 Relevância Atuarial dos Outliers:</strong> Outliers superiores (sinistralidade muito acima
            do esperado) podem indicar eventos extremos, fraudes ou concentração de grandes sinistros.
            Outliers inferiores podem sugerir períodos atípicos de baixa sinistralidade. A identificação
            e tratamento de outliers é fundamental na <strong>modelagem de risco</strong>, pois eventos
            extremos impactam diretamente as <strong>reservas técnicas</strong> e a
            <strong>solvência das seguradoras</strong>. O método IQR (amplitude interquartil) é robusto
            e amplamente utilizado em análises exploratórias.
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
                line=dict(color="#4FC3F7", width=3),
                marker=dict(size=10, color="#4FC3F7", line=dict(width=2, color="#0D47A1")),
                hovertemplate="<b>%{x}</b><br>Sinistralidade: %{y:.2%}<extra></extra>",
            )
        )
        fig_anual.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#EF5350",
            annotation_text="100%",
        )
        fig_anual.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            xaxis=dict(
                title="Ano",
                dtick=1,
                gridcolor="rgba(255,255,255,0.05)",
            ),
            yaxis=dict(
                title="Sinistralidade Anual",
                tickformat=".0%",
                gridcolor="rgba(255,255,255,0.05)",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_anual, use_container_width=True)

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

            # Formatação
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
            )
            fig_anual_uf.add_hline(y=1.0, line_dash="dash", line_color="#EF5350")
            fig_anual_uf.update_layout(
                height=450,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(dtick=1, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(
                    tickformat=".0%", gridcolor="rgba(255,255,255,0.05)"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )
            st.plotly_chart(fig_anual_uf, use_container_width=True)

        st.markdown(
            """
            <div class="narrative-box">
            <strong>📌 Perspectiva de Longo Prazo:</strong> A análise anual permite observar tendências
            estruturais do mercado segurador. Variações interanuais podem refletir mudanças regulatórias,
            conjuntura econômica ou eventos atípicos. Para a <strong>gestão atuarial</strong>, a visão
            anual é essencial na <strong>projeção de reservas</strong>, <strong>adequação de prêmios</strong>
            e avaliação da <strong>sustentabilidade financeira</strong> do setor.
            </div>
            """,
            unsafe_allow_html=True,
        )

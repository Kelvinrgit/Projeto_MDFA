"""
Fase 5 — Elaboração de Visualizações Analíticas
Disciplina: Manipulação e Análise de Dados Financeiros e Atuariais (MDAF)
Grupo 3:
  - Igor Botosi Kutelak
  - Kelvin Rammon Cavalcante Heleno da Silva
  - Tatiane Ponce Leon de Sousa Alves
  - Ana Clara Lima de França
  - Sabrina do Nascimento Duarte
  - Jessica Camila Pereira Furtado

Objetivo:
    Construir um conjunto de visualizações tecnicamente corretas, coerentes com
    as análises das fases anteriores e capazes de comunicar conclusões objetivas
    sobre o cenário atuarial do mercado segurador brasileiro.

Fonte de dados:
    Banco SQLite gerado na Fase 4 (dados/db/susep_mdaf.db).
"""

# ============================================================
# IMPORTAÇÕES
# ============================================================

import os
import sqlite3
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURAÇÃO GLOBAL DE ESTILO (Seaborn + Matplotlib)
# ============================================================

sns.set_theme(
    style="whitegrid",
    context="notebook",
    palette="muted",
    font_scale=1.1,
    rc={
        "figure.figsize": (12, 6),
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "figure.dpi": 120,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    },
)

PALETA_UFS = "tab20"  # paleta para variáveis categóricas (27 UFs)
COR_PRINCIPAL = "#2774AE"
COR_DESTAQUE = "#E74C3C"
COR_POSITIVA = "#27AE60"

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "dados", "db", "susep_mdaf.db")

conn = sqlite3.connect(DB_PATH)

df_mensal = pd.read_sql("SELECT * FROM trusted_susep_sinistralidade_mensal", conn)
df_resumo_uf = pd.read_sql("SELECT * FROM analytical_resumo_por_uf", conn)
df_outliers = pd.read_sql("SELECT * FROM analytical_outliers_iqr", conn)
df_resumo_outliers = pd.read_sql("SELECT * FROM analytical_resumo_outliers", conn)
df_anual = pd.read_sql("SELECT * FROM analytical_sinistralidade_anual", conn)

conn.close()

# Conversões de tipo
df_mensal["Data"] = pd.to_datetime(df_mensal["Data"], errors="coerce")
df_outliers["Data"] = pd.to_datetime(df_outliers["Data"], errors="coerce")

# Diretório de saída para as figuras
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "graficos_fase5")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Dados carregados: {len(df_mensal)} registros mensais, {df_mensal['UF'].nunique()} UFs.")
print(f"Figuras serão salvas em: {OUTPUT_DIR}\n")


# ============================================================
# GRÁFICO 1 — RANKING DE SINISTRALIDADE MÉDIA POR UF
# ============================================================
# OBJETIVO: Identificar quais estados apresentam os maiores
# índices médios de sinistralidade, evidenciando concentrações
# de risco que exigem atenção atuarial.
# Tipo: Barplot horizontal ordenado (adequado para ranking).

print("=" * 70)
print("GRÁFICO 1 — Ranking de Sinistralidade Média por UF")
print("=" * 70)

ranking = (
    df_mensal.groupby("UF", as_index=False)["Sinistralidade"]
    .mean()
    .sort_values("Sinistralidade", ascending=True)
)

# Classificação por faixa de risco
cores = [
    COR_DESTAQUE if v > 1.0 else "#F39C12" if v > 0.7 else COR_POSITIVA
    for v in ranking["Sinistralidade"]
]

fig, ax = plt.subplots(figsize=(10, 9))
bars = ax.barh(ranking["UF"], ranking["Sinistralidade"], color=cores, edgecolor="white", linewidth=0.5)

# Linha de equilíbrio atuarial (100%)
ax.axvline(x=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1.2, label="Equilíbrio (100%)")

# Anotações nos valores
for bar, val in zip(bars, ranking["Sinistralidade"]):
    ax.text(
        bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
        f"{val:.1%}", va="center", fontsize=9, color="#333"
    )

ax.set_xlabel("Sinistralidade Média")
ax.set_title("Ranking de Sinistralidade Média por UF", fontweight="bold", pad=15)
ax.legend(loc="lower right", fontsize=10)
ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
sns.despine(left=True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "01_ranking_sinistralidade_uf.png"))
plt.show()

print("""
CONCLUSÃO: O ranking permite identificar rapidamente as UFs com maior
desequilíbrio atuarial (sinistralidade > 100%). Estas regiões demandam
atenção prioritária para reprecificação de riscos e adequação de reservas.
UFs com sinistralidade consistentemente abaixo de 70% indicam mercados
mais estáveis e rentáveis para as seguradoras.
""")


# ============================================================
# GRÁFICO 2 — SÉRIE TEMPORAL DA SINISTRALIDADE (BRASIL)
# ============================================================
# OBJETIVO: Avaliar a tendência de longo prazo da sinistralidade
# do mercado segurador brasileiro. Oscilações e picos ajudam a
# entender sazonalidade e eventos atípicos.
# Tipo: Lineplot com área preenchida (adequado para séries temporais).

print("=" * 70)
print("GRÁFICO 2 — Série Temporal da Sinistralidade Mensal — Brasil")
print("=" * 70)

serie_brasil = (
    df_mensal.groupby("Data", as_index=False)["Sinistralidade"]
    .mean()
    .sort_values("Data")
)

fig, ax = plt.subplots(figsize=(14, 5))

ax.fill_between(
    serie_brasil["Data"], serie_brasil["Sinistralidade"],
    alpha=0.15, color=COR_PRINCIPAL
)
sns.lineplot(
    data=serie_brasil, x="Data", y="Sinistralidade",
    color=COR_PRINCIPAL, linewidth=2, ax=ax
)

ax.axhline(y=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1.2, label="Equilíbrio (100%)")

ax.set_xlabel("Período")
ax.set_ylabel("Sinistralidade")
ax.set_title("Evolução da Sinistralidade Mensal Média — Brasil", fontweight="bold", pad=15)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
ax.legend(fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "02_serie_temporal_brasil.png"))
plt.show()

print("""
CONCLUSÃO: A série temporal revela a dinâmica da sinistralidade ao longo do
período analisado. Picos acima de 100% sinalizam momentos de desequilíbrio
em que os sinistros pagos superaram os prêmios arrecadados. Eventuais padrões
sazonais auxiliam as seguradoras no dimensionamento de reservas técnicas e na
definição de estratégias de precificação.
""")


# ============================================================
# GRÁFICO 3 — BOXPLOT DA SINISTRALIDADE POR UF
# ============================================================
# OBJETIVO: Visualizar a dispersão e assimetria da sinistralidade
# em cada UF. Outliers são indicados explicitamente.
# Tipo: Boxplot (ideal para comparar distribuições entre grupos).

print("=" * 70)
print("GRÁFICO 3 — Boxplot da Sinistralidade por UF")
print("=" * 70)

# Ordenar UFs pela mediana para leitura intuitiva
ordem_mediana = (
    df_mensal.groupby("UF")["Sinistralidade"]
    .median()
    .sort_values(ascending=False)
    .index.tolist()
)

fig, ax = plt.subplots(figsize=(14, 7))

sns.boxplot(
    data=df_mensal, x="UF", y="Sinistralidade",
    order=ordem_mediana,
    palette="coolwarm",
    flierprops=dict(marker="o", markersize=3, alpha=0.5),
    linewidth=0.8,
    ax=ax,
)

ax.axhline(y=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1.2, label="Equilíbrio (100%)")
ax.set_xlabel("Unidade Federativa")
ax.set_ylabel("Sinistralidade")
ax.set_title("Distribuição da Sinistralidade Mensal por UF", fontweight="bold", pad=15)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
plt.xticks(rotation=45, ha="right")
ax.legend(fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "03_boxplot_sinistralidade_uf.png"))
plt.show()

print("""
CONCLUSÃO: O boxplot revela a variabilidade intra-estadual da sinistralidade.
UFs com caixas mais largas possuem maior dispersão (risco heterogêneo), enquanto
bigodes longos e pontos fora do box indicam eventos extremos. A assimetria das
distribuições é relevante para a modelagem atuarial — distribuições com cauda
superior longa exigem carregamentos de segurança maiores na precificação.
""")


# ============================================================
# GRÁFICO 4 — HEATMAP DE CORRELAÇÃO DE SPEARMAN
# ============================================================
# OBJETIVO: Quantificar relações monotônicas entre as variáveis
# financeiras. A correlação de Spearman é adequada para dados
# com possíveis outliers e relações não-lineares.
# Tipo: Heatmap anotado (clareza visual para matrizes).

print("=" * 70)
print("GRÁFICO 4 — Matriz de Correlação de Spearman")
print("=" * 70)

cols_corr = ["Prêmio Direto (R$)", "Sinistro Direto (R$)", "Sinistralidade"]
corr_matrix = df_mensal[cols_corr].corr(method="spearman")

fig, ax = plt.subplots(figsize=(7, 6))

sns.heatmap(
    corr_matrix,
    annot=True, fmt=".3f",
    cmap="Blues",
    vmin=-1, vmax=1,
    square=True,
    linewidths=1, linecolor="white",
    cbar_kws={"shrink": 0.8, "label": "Correlação de Spearman"},
    ax=ax,
)

ax.set_title("Matriz de Correlação de Spearman", fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "04_heatmap_correlacao_spearman.png"))
plt.show()

print("""
CONCLUSÃO: A alta correlação entre Prêmio e Sinistro Direto confirma que
mercados maiores (com mais prêmios) também geram mais sinistros — relação
esperada. Já a correlação da sinistralidade (Sinistro/Prêmio) com o volume
financeiro indica se mercados maiores são mais ou menos eficientes na gestão
de riscos, informação crucial para a alocação de capital regulatório.
""")


# ============================================================
# GRÁFICO 5 — DISPERSÃO PRÊMIO × SINISTRO
# ============================================================
# OBJETIVO: Visualizar a relação entre prêmios e sinistros e
# identificar padrões de proporcionalidade ou desvios.
# Tipo: Scatterplot com linha de regressão (identifica tendência).

print("=" * 70)
print("GRÁFICO 5 — Dispersão: Prêmio Direto vs. Sinistro Direto")
print("=" * 70)

fig, ax = plt.subplots(figsize=(10, 7))

sns.regplot(
    data=df_mensal,
    x="Prêmio Direto (R$)",
    y="Sinistro Direto (R$)",
    scatter_kws=dict(alpha=0.35, s=20, color=COR_PRINCIPAL),
    line_kws=dict(color=COR_DESTAQUE, linewidth=2),
    ci=95,
    ax=ax,
)

# Linha de equilíbrio (sinistro = prêmio)
lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
ax.plot([0, lim], [0, lim], "--", color="#888", linewidth=1, label="Sinistro = Prêmio (100%)")

ax.set_xlabel("Prêmio Direto (R$)")
ax.set_ylabel("Sinistro Direto (R$)")
ax.set_title("Prêmio Direto vs. Sinistro Direto (com Regressão Linear)", fontweight="bold", pad=15)
ax.legend(fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "05_dispersao_premio_sinistro.png"))
plt.show()

# Coeficiente angular
coef = np.polyfit(
    df_mensal["Prêmio Direto (R$)"].dropna(),
    df_mensal["Sinistro Direto (R$)"].dropna(),
    1,
)
print(f"Coeficiente angular da regressão: {coef[0]:.4f}")
print("""
CONCLUSÃO: Pontos acima da linha tracejada (Sinistro = Prêmio) representam
observações com sinistralidade superior a 100%. A inclinação da reta de
regressão (~slope) indica o percentual médio de sinistro para cada real de
prêmio. Um coeficiente < 1 sugere que, em média, o mercado retém margem
técnica positiva — condição essencial para a sustentabilidade das seguradoras.
""")


# ============================================================
# GRÁFICO 6 — SINISTRALIDADE ANUAL MÉDIA (LINHA TEMPORAL)
# ============================================================
# OBJETIVO: Acompanhar a dinâmica da sinistralidade em base
# anual, suavizando oscilações mensais para revelar a tendência.
# Tipo: Line + marker (destaca cada ponto anual).

print("=" * 70)
print("GRÁFICO 6 — Sinistralidade Anual Média — Brasil")
print("=" * 70)

anual_media = (
    df_anual.groupby("Ano", as_index=False)["Sinistralidade_Anual"]
    .mean()
    .sort_values("Ano")
)

fig, ax = plt.subplots(figsize=(10, 5))

sns.lineplot(
    data=anual_media, x="Ano", y="Sinistralidade_Anual",
    marker="o", markersize=9, linewidth=2.5,
    color=COR_PRINCIPAL, ax=ax,
)

ax.axhline(y=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1.2, label="Equilíbrio (100%)")

# Anotações com valor em cada ponto
for _, row in anual_media.iterrows():
    ax.annotate(
        f"{row['Sinistralidade_Anual']:.1%}",
        xy=(row["Ano"], row["Sinistralidade_Anual"]),
        xytext=(0, 12), textcoords="offset points",
        ha="center", fontsize=8.5, color="#333",
    )

ax.set_xlabel("Ano")
ax.set_ylabel("Sinistralidade Anual Média")
ax.set_title("Evolução da Sinistralidade Anual Média — Brasil", fontweight="bold", pad=15)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
ax.legend(fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "06_sinistralidade_anual_brasil.png"))
plt.show()

print("""
CONCLUSÃO: A visão anual permite avaliar tendências estruturais de forma mais
clara que a série mensal. Variações interanuais podem refletir mudanças no
mix de risco, inflação de sinistros, alterações regulatórias ou eventos
macroeconômicos. Para o atuário, essa perspectiva é essencial na projeção
de reservas e na adequação de prêmios futuros.
""")


# ============================================================
# GRÁFICO 7 — CONTAGEM DE OUTLIERS POR UF (SUPERIORES vs INFERIORES)
# ============================================================
# OBJETIVO: Identificar quais estados concentram mais eventos
# extremos e categorizar o tipo (superior = pior cenário).
# Tipo: Barplot empilhado (compara composição interna).

print("=" * 70)
print("GRÁFICO 7 — Outliers por UF (Superiores vs Inferiores)")
print("=" * 70)

resumo_o = df_resumo_outliers.copy()
resumo_o = resumo_o.sort_values("Total_Outliers", ascending=True)

fig, ax = plt.subplots(figsize=(10, 8))

ax.barh(
    resumo_o["UF"], resumo_o["Outliers_Superiores"],
    color=COR_DESTAQUE, label="Superiores (acima do esperado)", edgecolor="white", linewidth=0.5,
)
ax.barh(
    resumo_o["UF"], resumo_o["Outliers_Inferiores"],
    left=resumo_o["Outliers_Superiores"],
    color=COR_POSITIVA, label="Inferiores (abaixo do esperado)", edgecolor="white", linewidth=0.5,
)

ax.set_xlabel("Quantidade de Outliers")
ax.set_title("Outliers Detectados (IQR) por UF — Superiores vs. Inferiores", fontweight="bold", pad=15)
ax.legend(loc="lower right", fontsize=10)
sns.despine(left=True)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "07_outliers_por_uf.png"))
plt.show()

print("""
CONCLUSÃO: Outliers superiores indicam meses em que a sinistralidade excedeu
significativamente o padrão daquela UF, sugerindo eventos extremos (catástrofes,
fraudes ou concentração de grandes sinistros). Outliers inferiores podem representar
meses atipicamente favoráveis. A contagem por UF ajuda a priorizar as regiões
que exigem maior atenção no provisionamento de reservas técnicas.
""")


# ============================================================
# GRÁFICO 8 — VIOLINPLOT: DISTRIBUIÇÃO DETALHADA TOP 10 UFs
# ============================================================
# OBJETIVO: Complementar o boxplot com uma visão mais detalhada
# da forma da distribuição (multimodalidade, assimetria).
# Tipo: Violinplot (mostra densidade + quartis simultaneamente).

print("=" * 70)
print("GRÁFICO 8 — Violinplot: Top 10 UFs por Sinistralidade Média")
print("=" * 70)

top10_ufs = (
    df_mensal.groupby("UF")["Sinistralidade"]
    .mean()
    .nlargest(10)
    .index.tolist()
)

df_top10 = df_mensal[df_mensal["UF"].isin(top10_ufs)].copy()

fig, ax = plt.subplots(figsize=(12, 6))

sns.violinplot(
    data=df_top10, x="UF", y="Sinistralidade",
    order=top10_ufs,
    palette="Reds_r",
    inner="quartile",
    linewidth=0.8,
    ax=ax,
)

ax.axhline(y=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1.2, label="Equilíbrio (100%)")
ax.set_xlabel("Unidade Federativa")
ax.set_ylabel("Sinistralidade")
ax.set_title("Distribuição da Sinistralidade — Top 10 UFs (Violinplot)", fontweight="bold", pad=15)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
ax.legend(fontsize=10)
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "08_violinplot_top10_ufs.png"))
plt.show()

print("""
CONCLUSÃO: O violinplot permite visualizar a forma completa da distribuição
da sinistralidade por UF. Distribuições bimodais podem indicar perfis de
risco distintos dentro de um mesmo estado. Caudas longas na parte superior
revelam propensão a eventos extremos — informação valiosa para a modelagem
de risco e definição de carregamentos de segurança nas tarifas.
""")


# ============================================================
# GRÁFICO 9 — HEATMAP ANUAL POR UF
# ============================================================
# OBJETIVO: Criar uma visão matricial (UF × Ano) da sinistralidade
# anual para identificar padrões regionais e temporais.
# Tipo: Heatmap (visualização matricial eficiente).

print("=" * 70)
print("GRÁFICO 9 — Heatmap: Sinistralidade Anual por UF")
print("=" * 70)

pivot_anual = df_anual.pivot_table(
    index="UF", columns="Ano", values="Sinistralidade_Anual"
)

# Ordenar pelo valor médio para melhor leitura
pivot_anual = pivot_anual.loc[pivot_anual.mean(axis=1).sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(14, 10))

sns.heatmap(
    pivot_anual,
    annot=True, fmt=".0%",
    cmap="RdYlGn_r",   # vermelho = alta sinistralidade, verde = baixa
    center=0.5,
    linewidths=0.5, linecolor="white",
    cbar_kws={"shrink": 0.7, "label": "Sinistralidade Anual"},
    ax=ax,
)

ax.set_xlabel("Ano")
ax.set_ylabel("Unidade Federativa")
ax.set_title("Mapa de Calor — Sinistralidade Anual por UF", fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "09_heatmap_anual_uf.png"))
plt.show()

print("""
CONCLUSÃO: O heatmap permite identificar simultaneamente padrões temporais
e regionais. Células em tons vermelhos/alaranjados indicam sinistralidade
elevada, enquanto tons verdes representam equilíbrio ou superávit. Padrões
de cores concentrados em linhas inteiras sugerem problemas estruturais
em determinadas UFs, enquanto padrões em colunas inteiras podem indicar
eventos sistêmicos que afetaram todo o mercado naquele ano.
""")


# ============================================================
# GRÁFICO 10 — COEFICIENTE DE VARIAÇÃO POR UF
# ============================================================
# OBJETIVO: Avaliar a homogeneidade do risco em cada UF.
# Um CV alto indica alta variabilidade relativa, ou seja,
# previsibilidade menor — relevante para precificação.
# Tipo: Barplot vertical ordenado (ranking comparativo).

print("=" * 70)
print("GRÁFICO 10 — Coeficiente de Variação (CV) da Sinistralidade por UF")
print("=" * 70)

cv_uf = df_resumo_uf[["UF", "CV"]].copy().sort_values("CV", ascending=False)

cores_cv = [COR_DESTAQUE if v > 1.0 else "#F39C12" if v > 0.5 else COR_POSITIVA for v in cv_uf["CV"]]

fig, ax = plt.subplots(figsize=(13, 5))

bars = ax.bar(cv_uf["UF"], cv_uf["CV"], color=cores_cv, edgecolor="white", linewidth=0.5)

ax.axhline(y=1.0, color=COR_DESTAQUE, linestyle="--", linewidth=1, label="CV = 1 (alta variabilidade)")
ax.axhline(y=0.5, color="#F39C12", linestyle=":", linewidth=1, label="CV = 0.5 (limiar moderado)")

ax.set_xlabel("Unidade Federativa")
ax.set_ylabel("Coeficiente de Variação (CV)")
ax.set_title("Coeficiente de Variação da Sinistralidade por UF", fontweight="bold", pad=15)
plt.xticks(rotation=45, ha="right")
ax.legend(fontsize=9, loc="upper right")
sns.despine()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "10_coeficiente_variacao_uf.png"))
plt.show()

print("""
CONCLUSÃO: O Coeficiente de Variação mede a dispersão relativa. UFs com
CV > 1 possuem desvio padrão superior à própria média, indicando extrema
heterogeneidade no perfil de risco — essas regiões são mais difíceis de
precificar e demandam carregamentos de segurança mais elevados. UFs com
CV baixo possuem risco mais homogêneo e, portanto, maior previsibilidade
para as projeções atuariais.
""")


# ============================================================
# RESUMO FINAL
# ============================================================

print("=" * 70)
print("FASE 5 — FINALIZADA COM SUCESSO")
print("=" * 70)

graficos = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")]
print(f"\n{len(graficos)} visualizações geradas e salvas em: {OUTPUT_DIR}/")
for g in sorted(graficos):
    print(f"  • {g}")

print("""
Todas as visualizações foram elaboradas seguindo critérios de:
  ✓ Correção técnica (escalas corretas, formatação percentual)
  ✓ Coerência com as análises realizadas (Fases 1–4)
  ✓ Comunicação de conclusões objetivas (narrativa atuarial)
  ✓ Clareza visual (evitando poluição e redundância)
  ✓ Uso de Seaborn e Matplotlib para padronização visual
""")

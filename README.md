# Dashboard de Sinistralidade — SUSEP (MDAF)

📊 **Dashboard Interativo para Análise de Prêmios e Sinistros do Mercado Segurador Brasileiro.**

Este projeto foi desenvolvido como a **Fase 5** da disciplina de *Manipulação e Análise de Dados Financeiros e Atuariais (MDAF)*. Ele consolida os dados das fases anteriores (coleta, tratamento e análise) em um dashboard interativo construído com [Streamlit](https://streamlit.io/) e [Plotly](https://plotly.com/).

## 👥 Equipe (Grupo 3)
- Igor Botosi Kutelak
- Kelvin Rammon Cavalcante Heleno da Silva
- Tatiane Ponce Leon de Sousa Alves
- Ana Clara Lima de França
- Sabrina do Nascimento Duarte
- Jessica Camila Pereira Furtado

## 🎯 Objetivo
O objetivo principal deste dashboard é:
1. **Integrar** as análises produzidas ao longo do projeto.
2. Permitir a **interatividade** através de filtros por Unidade Federativa (UF) e Período (anos).
3. Apresentar uma **narrativa analítica** consistente com as análises do contexto atuarial.
4. Detectar de forma visual as anomalias estaduais (método IQR) e acompanhar o histórico de sinistralidade.

## ⚙️ Funcionalidades e Abas do Dashboard

O painel é dividido logicamente nas seguintes visões:
- **📊 Visão Geral:** KPIs consolidados e ranking das UFs baseado na média de sinistralidade, evidenciando onde ocorrem os maiores desequilíbrios atuariais.
- **📈 Série Temporal:** Evolução da sinistralidade mensal ao nível Brasil e comparações entre estados selecionados, destacando tendências de longo prazo.
- **🏛️ Análise por UF:** Abordagem estatística com Boxplots das distribuições, estatísticas descritivas (média, mediana, IQR, CV), gráfico de dispersão e Matriz de Correlação.
- **⚠️ Outliers:** Detalhamento das anomalias detectadas pelo método IQR (superiores e inferiores) e suas implicações para reservas técnicas e solvência.
- **📅 Visão Anual:** Resumo agregado ano a ano revelando mudanças macrodinâmicas e evolução a longo prazo por UF.

## 🏗️ Estrutura do Projeto
A arquitetura se baseia em um Data Warehouse simples, processado nas Fases 1 a 4 utilizando Pandas, SQLite e Parquet.

```bash
Projeto_MDFA/
├── dados/
│   ├── analytical/      # Camada analítica (.parquet)
│   ├── catalog/         # Logs, schema MD5
│   ├── db/              # Banco SQLite (susep_mdaf.db) utilizado pelo App
│   ├── raw/             # Base Bruta (.parquet)
│   └── trusted/         # Base Normalizada (.parquet)
├── .streamlit/
│   └── config.toml      # Configuração customizada do tema Escuro (Dark)
├── requirements.txt     # Dependências de execução
├── streamlit_run.py     # ✅ Código Fonte Principal (Streamlit)
└── README.md            # Documentação
```

## 🚀 Como Executar Localmente

**1. Clone o repositório:**
```bash
git clone https://github.com/Kelvinrgit/Projeto_MDFA.git
cd Projeto_MDFA
```

**2. Crie e ative o ambiente virtual:**
- No Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
- No Linux/Mac:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**4. Execute o Streamlit:**
```bash
streamlit run streamlit_run.py
```

O painel ficará disponível no seu navegador em `http://localhost:8501`.

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Resolução de credenciais:
# 1. Streamlit Cloud → st.secrets["POSTGRES_URL"]
# 2. Local           → variável de ambiente carregada do .env
# ---------------------------------------------------------------------------
def _get_postgres_url() -> str:
    # Streamlit Cloud injeta as secrets via st.secrets
    try:
        url = st.secrets.get("POSTGRES_URL")
        if url:
            return url
    except Exception:
        pass

    # Fallback local: procura o .env na pasta do projeto ou na pasta .llm pai
    for candidate in [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".llm" / ".env",
    ]:
        if candidate.exists():
            load_dotenv(dotenv_path=candidate)
            break

    url = os.getenv("POSTGRES_URL")
    if not url:
        st.error(
            "Variável POSTGRES_URL não encontrada.\n\n"
            "**Local:** crie o arquivo `.env` na pasta `case-01-dashboard/` com `POSTGRES_URL=...`\n\n"
            "**Streamlit Cloud:** adicione `POSTGRES_URL` em *Settings → Secrets*."
        )
        st.stop()
    return url

POSTGRES_URL = _get_postgres_url()

st.set_page_config(layout="wide", page_title="E-commerce Analytics", page_icon="📊")

# ---------------------------------------------------------------------------
# Background — gradiente azul escuro
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(ellipse at 78% 2%, #1a50ae 0%, #0a2a72 18%, transparent 48%),
        radial-gradient(circle at -8% 48%, #0d3888 0%, transparent 42%),
        radial-gradient(circle at 48% 105%, #0a2260 0%, transparent 52%);
    background-color: #010e24;
}
[data-testid="stHeader"] {
    background-color: transparent;
}
section[data-testid="stSidebar"] {
    background-color: rgba(1, 8, 28, 0.88);
    border-right: 1px solid rgba(255,255,255,0.08);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
.stApp * {
    color: #e2e8f0;
}
.stMetric label, .stMetric [data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
}
[data-testid="stMetricDelta"] {
    color: #94a3b8 !important;
}
.stSelectbox label, .stMultiSelect label {
    color: #94a3b8 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Design system — paleta semântica consistente (skill: "color with purpose")
# ---------------------------------------------------------------------------
PALETA = {
    "primario":   "#0068C9",   # azul — métrica neutra / tendência
    "positivo":   "#00CC96",   # verde — bom, mais barato, crescimento
    "negativo":   "#EF553B",   # vermelho — alerta, mais caro
    "atencao":    "#F59E0B",   # âmbar — atenção / VIP/destaque
    "neutro":     "#6B7280",   # cinza — secundário / TOP_TIER
}

CORES_SEGMENTO = {
    "VIP":      PALETA["atencao"],
    "TOP_TIER": PALETA["neutro"],
    "REGULAR":  PALETA["primario"],
}

CORES_PRICING = {
    "MAIS_CARO_QUE_TODOS":   PALETA["negativo"],
    "MAIS_BARATO_QUE_TODOS": PALETA["positivo"],
    "ACIMA_DA_MEDIA":        "#FF8C42",
    "ABAIXO_DA_MEDIA":       "#48CAE4",
    "NA_MEDIA":              PALETA["neutro"],
}

# Template plotly — dark para harmonizar com o background
TEMPLATE = "plotly_dark"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_data(query: str) -> pd.DataFrame:
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        with conn.cursor() as cur:
            cur.execute(query)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        conn.close()
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.error(
            f"Não foi possível conectar ao banco de dados. "
            f"Verifique o arquivo .env.\n\nDetalhe: {e}"
        )
        return pd.DataFrame()


def fmt_brl(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ -"


def fmt_int(value) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "-"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("E-commerce Analytics")
pagina = st.sidebar.radio("Navegação", ["Vendas", "Clientes", "Pricing"])


# ===========================================================================
# PÁGINA 1: VENDAS
# ===========================================================================

if pagina == "Vendas":
    st.title("📈 Vendas — Visão do Diretor Comercial")

    df = get_data("SELECT * FROM public_gold_sales.vendas_temporais")
    if df.empty:
        st.stop()

    # Casting numérico antecipado (evita erros silenciosos nos gráficos)
    for col in ["receita_total", "total_vendas", "total_clientes_unicos", "ticket_medio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Filtro de mês
    meses_disponiveis = sorted(df["mes_venda"].unique().tolist())
    opcoes_mes = ["Todos os meses"] + [str(m) for m in meses_disponiveis]
    mes_sel = st.selectbox("Filtrar por mês:", opcoes_mes)

    df_filtrado = df if mes_sel == "Todos os meses" else df[df["mes_venda"] == int(mes_sel)]

    if df_filtrado.empty:
        st.info("Nenhum dado disponível para o filtro selecionado.")
        st.stop()

    # KPIs
    receita_total = df_filtrado["receita_total"].sum()
    total_vendas  = df_filtrado["total_vendas"].sum()
    ticket_medio  = receita_total / total_vendas if total_vendas > 0 else 0
    clientes_unicos = df_filtrado["total_clientes_unicos"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Receita Total",    fmt_brl(receita_total))
    c2.metric("🛒 Total de Vendas",  fmt_int(total_vendas))
    c3.metric("🎯 Ticket Médio",     fmt_brl(ticket_medio))
    c4.metric("👥 Clientes Únicos",  fmt_int(clientes_unicos))

    st.divider()

    # Gráfico 1 — Receita Diária (tendência)
    df_dia = (
        df_filtrado.groupby("data_venda", as_index=False)["receita_total"]
        .sum()
        .sort_values("data_venda")
    )
    fig1 = px.line(
        df_dia,
        x="data_venda",
        y="receita_total",
        title="Receita Diária — evolução no período",
        labels={"data_venda": "Data", "receita_total": "Receita (R$)"},
        template=TEMPLATE,
        color_discrete_sequence=[PALETA["primario"]],
    )
    fig1.update_traces(hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>")
    fig1.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    st.plotly_chart(fig1, width='stretch')

    col_a, col_b = st.columns(2)

    # Gráfico 2 — Receita por Dia da Semana
    ordem_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    df_semana = df_filtrado.groupby("dia_semana_nome", as_index=False)["receita_total"].sum()
    ordem_map = {dia: i for i, dia in enumerate(ordem_dias)}
    df_semana["_ordem"] = df_semana["dia_semana_nome"].map(ordem_map)
    df_semana = df_semana.sort_values("_ordem").drop(columns="_ordem")
    fig2 = px.bar(
        df_semana,
        x="dia_semana_nome",
        y="receita_total",
        title="Receita por Dia da Semana — qual dia vende mais?",
        labels={"dia_semana_nome": "", "receita_total": "Receita (R$)"},
        template=TEMPLATE,
        color_discrete_sequence=[PALETA["primario"]],
    )
    fig2.update_traces(hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>")
    fig2.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    col_a.plotly_chart(fig2, width='stretch')

    # Gráfico 3 — Vendas por Hora
    df_hora = (
        df_filtrado.groupby("hora_venda", as_index=False)["total_vendas"]
        .sum()
        .sort_values("hora_venda")
    )
    fig3 = px.bar(
        df_hora,
        x="hora_venda",
        y="total_vendas",
        title="Volume de Vendas por Hora — horário de pico",
        labels={"hora_venda": "Hora", "total_vendas": "Vendas"},
        template=TEMPLATE,
        color_discrete_sequence=[PALETA["primario"]],
    )
    fig3.update_traces(hovertemplate="<b>%{x}h</b><br>Vendas: %{y}<extra></extra>")
    col_b.plotly_chart(fig3, width='stretch')


# ===========================================================================
# PÁGINA 2: CLIENTES
# ===========================================================================

elif pagina == "Clientes":
    st.title("👥 Clientes — Visão da Diretora de Customer Success")

    df = get_data("SELECT * FROM public_gold_cs.clientes_segmentacao")
    if df.empty:
        st.stop()

    # Casting numérico antecipado
    for col in ["receita_total", "ticket_medio", "total_compras", "ranking_receita"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # KPIs (sempre sobre a base completa)
    total_clientes    = len(df)
    clientes_vip      = len(df[df["segmento_cliente"] == "VIP"])
    receita_vip       = df[df["segmento_cliente"] == "VIP"]["receita_total"].sum()
    ticket_medio_geral = df["ticket_medio"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Total Clientes",      fmt_int(total_clientes))
    c2.metric("⭐ Clientes VIP",        fmt_int(clientes_vip))
    c3.metric("💎 Receita VIP",         fmt_brl(receita_vip))
    c4.metric("🎯 Ticket Médio Geral",  fmt_brl(ticket_medio_geral))

    st.divider()

    col_a, col_b = st.columns(2)

    # Gráfico 1 — Distribuição por Segmento (donut — skill: "Part of whole → Donut")
    df_seg = (
        df.groupby("segmento_cliente", as_index=False)
        .size()
        .rename(columns={"size": "total"})
    )
    fig1 = px.pie(
        df_seg,
        names="segmento_cliente",
        values="total",
        hole=0.45,
        title="Distribuição de Clientes por Segmento",
        color="segmento_cliente",
        color_discrete_map=CORES_SEGMENTO,
        template=TEMPLATE,
    )
    fig1.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Clientes: %{value}<br>%{percent}<extra></extra>")
    col_a.plotly_chart(fig1, width='stretch')

    # Gráfico 2 — Receita por Segmento
    df_rec_seg = df.groupby("segmento_cliente", as_index=False)["receita_total"].sum()
    fig2 = px.bar(
        df_rec_seg,
        x="segmento_cliente",
        y="receita_total",
        title="Receita por Segmento — VIP concentra maior valor",
        labels={"segmento_cliente": "", "receita_total": "Receita (R$)"},
        color="segmento_cliente",
        color_discrete_map=CORES_SEGMENTO,
        template=TEMPLATE,
    )
    fig2.update_traces(hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>")
    fig2.update_layout(showlegend=False, yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    col_b.plotly_chart(fig2, width='stretch')

    col_c, col_d = st.columns(2)

    # Gráfico 3 — Top 10 Clientes (barras horizontais)
    df_top10 = df[df["ranking_receita"] <= 10].sort_values("receita_total", ascending=True)
    fig3 = px.bar(
        df_top10,
        x="receita_total",
        y="nome_cliente",
        orientation="h",
        title="Top 10 Clientes por Receita",
        labels={"nome_cliente": "", "receita_total": "Receita (R$)"},
        template=TEMPLATE,
        color_discrete_sequence=[PALETA["atencao"]],
    )
    fig3.update_traces(hovertemplate="<b>%{y}</b><br>Receita: R$ %{x:,.2f}<extra></extra>")
    fig3.update_layout(xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f")
    col_c.plotly_chart(fig3, width='stretch')

    # Gráfico 4 — Clientes por Estado (Mapa coroplético)
    df_estado = (
        df.groupby("estado", as_index=False)
        .size()
        .rename(columns={"size": "total"})
        .sort_values("total", ascending=False)
    )
    _BRAZIL_GEOJSON = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    fig4 = px.choropleth(
        df_estado,
        geojson=_BRAZIL_GEOJSON,
        locations="estado",
        featureidkey="properties.sigla",
        color="total",
        color_continuous_scale=["#dbeafe", PALETA["primario"]],
        title="Clientes por Estado — distribuição geográfica",
        labels={"total": "Clientes", "estado": "UF"},
        hover_data={"estado": True, "total": True},
    )
    fig4.update_geos(
        fitbounds="locations",
        visible=False,
    )
    fig4.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar={"title": "Clientes"},
    )
    fig4.update_traces(hovertemplate="<b>%{location}</b><br>Clientes: %{z}<extra></extra>")
    col_d.plotly_chart(fig4, width='stretch')

    st.divider()

    # Filtro + Tabela detalhada
    segmentos = ["Todos"] + sorted(df["segmento_cliente"].unique().tolist())
    seg_sel = st.selectbox("Filtrar tabela por segmento:", segmentos)
    df_tabela = df if seg_sel == "Todos" else df[df["segmento_cliente"] == seg_sel]
    if df_tabela.empty:
        st.info("Nenhum cliente encontrado para o segmento selecionado.")
    else:
        st.dataframe(df_tabela, width='stretch')


# ===========================================================================
# PÁGINA 3: PRICING
# ===========================================================================

elif pagina == "Pricing":
    st.title("🏷️ Pricing — Visão do Diretor de Pricing")

    df = get_data("SELECT * FROM public_gold_pricing.precos_competitividade")
    if df.empty:
        st.stop()

    # Casting numérico antecipado
    for col in ["nosso_preco", "preco_medio_concorrentes", "preco_minimo_concorrentes",
                "preco_maximo_concorrentes", "diferenca_percentual_vs_media",
                "diferenca_percentual_vs_minimo", "receita_total", "quantidade_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Filtro de categoria
    categorias = sorted(df["categoria"].unique().tolist())
    cat_sel = st.multiselect("Filtrar por categoria:", categorias)
    df_filtrado = df[df["categoria"].isin(cat_sel)] if cat_sel else df

    if df_filtrado.empty:
        st.info("Nenhum produto encontrado para as categorias selecionadas.")
        st.stop()

    # KPIs
    total_produtos = len(df_filtrado)
    mais_caros  = len(df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"])
    mais_baratos = len(df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS"])
    diff_media  = df_filtrado["diferenca_percentual_vs_media"].mean()
    diff_str    = (
        f"{'+' if diff_media >= 0 else ''}{diff_media:.1f}%"
        if not pd.isna(diff_media) else "-"
    )
    diff_delta_color = "inverse" if diff_media > 0 else "normal"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Produtos Monitorados",     fmt_int(total_produtos))
    c2.metric("🔴 Mais Caros que Todos",      fmt_int(mais_caros))
    c3.metric("🟢 Mais Baratos que Todos",    fmt_int(mais_baratos))
    c4.metric("📊 Diferença Média vs Mercado", diff_str)

    st.divider()

    col_a, col_b = st.columns(2)

    # Gráfico 1 — Posicionamento por Classificação (donut)
    df_class = (
        df_filtrado.groupby("classificacao_preco", as_index=False)
        .size()
        .rename(columns={"size": "total"})
    )
    fig1 = px.pie(
        df_class,
        names="classificacao_preco",
        values="total",
        hole=0.45,
        title="Posicionamento de Preço vs Concorrência",
        color="classificacao_preco",
        color_discrete_map=CORES_PRICING,
        template=TEMPLATE,
    )
    fig1.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Produtos: %{value}<br>%{percent}<extra></extra>")
    col_a.plotly_chart(fig1, width='stretch')

    # Gráfico 2 — Competitividade por Categoria
    df_cat = df_filtrado.groupby("categoria", as_index=False)["diferenca_percentual_vs_media"].mean()
    df_cat["posicao"] = df_cat["diferenca_percentual_vs_media"].apply(
        lambda x: "Mais caro" if x > 0 else "Mais barato"
    )
    fig2 = px.bar(
        df_cat,
        x="categoria",
        y="diferenca_percentual_vs_media",
        color="posicao",
        color_discrete_map={"Mais caro": PALETA["negativo"], "Mais barato": PALETA["positivo"]},
        title="Competitividade por Categoria — vermelho = mais caro que concorrentes",
        labels={
            "categoria": "",
            "diferenca_percentual_vs_media": "Diff % vs Média Mercado",
            "posicao": "Posição",
        },
        template=TEMPLATE,
    )
    fig2.update_traces(hovertemplate="<b>%{x}</b><br>Diff: %{y:.1f}%<extra></extra>")
    fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    col_b.plotly_chart(fig2, width='stretch')

    # Gráfico 3 — Scatter: Competitividade x Volume
    df_scatter = df_filtrado.copy()
    df_scatter["size_col"] = df_scatter["receita_total"].clip(lower=0) + 1
    fig3 = px.scatter(
        df_scatter,
        x="diferenca_percentual_vs_media",
        y="quantidade_total",
        color="classificacao_preco",
        size="size_col",
        hover_name="nome_produto",
        hover_data={"size_col": False, "categoria": True, "nosso_preco": True},
        title="Competitividade x Volume — produtos mais caros vendem menos?",
        labels={
            "diferenca_percentual_vs_media": "Diff % vs Média Mercado",
            "quantidade_total": "Qtd Vendida",
            "classificacao_preco": "Classificação",
        },
        color_discrete_map=CORES_PRICING,
        template=TEMPLATE,
    )
    fig3.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig3, width='stretch')

    st.divider()

    # Tabela de Alertas
    st.subheader("🚨 Produtos em Alerta — mais caros que todos os concorrentes")
    df_alerta = df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"][
        [
            "produto_id",
            "nome_produto",
            "categoria",
            "nosso_preco",
            "preco_maximo_concorrentes",
            "diferenca_percentual_vs_media",
        ]
    ].sort_values("diferenca_percentual_vs_media", ascending=False)
    if df_alerta.empty:
        st.success("Nenhum produto mais caro que todos os concorrentes no filtro atual.")
    else:
        st.caption(f"{len(df_alerta)} produto(s) precisam de revisão de preço.")
        st.dataframe(df_alerta, width='stretch')

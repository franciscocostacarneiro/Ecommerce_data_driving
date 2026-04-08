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

st.set_page_config(layout="wide", page_title="E-commerce Analytics")


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
    st.title("Vendas — Visão do Diretor Comercial")

    df = get_data("SELECT * FROM public_gold_sales.vendas_temporais")
    if df.empty:
        st.stop()

    # Filtro de mês
    meses_disponiveis = sorted(df["mes_venda"].unique().tolist())
    opcoes_mes = ["Todos os meses"] + [str(m) for m in meses_disponiveis]
    mes_sel = st.selectbox("Filtrar por mês:", opcoes_mes)

    df_filtrado = df if mes_sel == "Todos os meses" else df[df["mes_venda"] == int(mes_sel)]

    # KPIs
    receita_total = df_filtrado["receita_total"].sum()
    total_vendas = df_filtrado["total_vendas"].sum()
    ticket_medio = receita_total / total_vendas if total_vendas > 0 else 0
    clientes_unicos = df_filtrado["total_clientes_unicos"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Total", fmt_brl(receita_total))
    c2.metric("Total de Vendas", fmt_int(total_vendas))
    c3.metric("Ticket Médio", fmt_brl(ticket_medio))
    c4.metric("Clientes Únicos", fmt_int(clientes_unicos))

    st.divider()

    # Gráfico 1 — Receita Diária
    df_dia = (
        df_filtrado.groupby("data_venda", as_index=False)["receita_total"]
        .sum()
        .sort_values("data_venda")
    )
    fig1 = px.line(
        df_dia,
        x="data_venda",
        y="receita_total",
        title="Receita Diária",
        labels={"data_venda": "Data", "receita_total": "Receita (R$)"},
    )
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
        title="Receita por Dia da Semana",
        labels={"dia_semana_nome": "Dia", "receita_total": "Receita (R$)"},
    )
    col_a.plotly_chart(fig2, use_container_width=True)

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
        title="Volume de Vendas por Hora",
        labels={"hora_venda": "Hora", "total_vendas": "Vendas"},
    )
    col_b.plotly_chart(fig3, use_container_width=True)


# ===========================================================================
# PÁGINA 2: CLIENTES
# ===========================================================================

elif pagina == "Clientes":
    st.title("Clientes — Visão da Diretora de Customer Success")

    df = get_data("SELECT * FROM public_gold_cs.clientes_segmentacao")
    if df.empty:
        st.stop()

    # KPIs (sempre sobre a base completa)
    total_clientes = len(df)
    clientes_vip = len(df[df["segmento_cliente"] == "VIP"])
    receita_vip = df[df["segmento_cliente"] == "VIP"]["receita_total"].sum()
    ticket_medio_geral = df["ticket_medio"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Clientes", fmt_int(total_clientes))
    c2.metric("Clientes VIP", fmt_int(clientes_vip))
    c3.metric("Receita VIP", fmt_brl(receita_vip))
    c4.metric("Ticket Médio Geral", fmt_brl(ticket_medio_geral))

    st.divider()

    col_a, col_b = st.columns(2)

    # Gráfico 1 — Distribuição por Segmento
    df_seg = (
        df.groupby("segmento_cliente", as_index=False)
        .size()
        .rename(columns={"size": "total"})
    )
    fig1 = px.pie(
        df_seg,
        names="segmento_cliente",
        values="total",
        title="Distribuição de Clientes por Segmento",
    )
    col_a.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2 — Receita por Segmento
    df_rec_seg = df.groupby("segmento_cliente", as_index=False)["receita_total"].sum()
    fig2 = px.bar(
        df_rec_seg,
        x="segmento_cliente",
        y="receita_total",
        title="Receita por Segmento",
        labels={"segmento_cliente": "Segmento", "receita_total": "Receita (R$)"},
    )
    col_b.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    # Gráfico 3 — Top 10 Clientes (barras horizontais)
    df_top10 = df[df["ranking_receita"] <= 10].sort_values("receita_total")
    fig3 = px.bar(
        df_top10,
        x="receita_total",
        y="nome_cliente",
        orientation="h",
        title="Top 10 Clientes",
        labels={"nome_cliente": "Cliente", "receita_total": "Receita (R$)"},
    )
    col_c.plotly_chart(fig3, use_container_width=True)

    # Gráfico 4 — Clientes por Estado
    df_estado = (
        df.groupby("estado", as_index=False)
        .size()
        .rename(columns={"size": "total"})
        .sort_values("total", ascending=False)
    )
    fig4 = px.bar(
        df_estado,
        x="estado",
        y="total",
        title="Clientes por Estado",
        labels={"estado": "Estado", "total": "Clientes"},
    )
    col_d.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # Filtro + Tabela detalhada
    segmentos = ["Todos"] + sorted(df["segmento_cliente"].unique().tolist())
    seg_sel = st.selectbox("Filtrar tabela por segmento:", segmentos)
    df_tabela = df if seg_sel == "Todos" else df[df["segmento_cliente"] == seg_sel]
    st.dataframe(df_tabela, use_container_width=True)


# ===========================================================================
# PÁGINA 3: PRICING
# ===========================================================================

elif pagina == "Pricing":
    st.title("Pricing — Visão do Diretor de Pricing")

    df = get_data("SELECT * FROM public_gold_pricing.precos_competitividade")
    if df.empty:
        st.stop()

    # Filtro de categoria
    categorias = sorted(df["categoria"].unique().tolist())
    cat_sel = st.multiselect("Filtrar por categoria:", categorias)
    df_filtrado = df[df["categoria"].isin(cat_sel)] if cat_sel else df

    # KPIs
    total_produtos = len(df_filtrado)
    mais_caros = len(df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"])
    mais_baratos = len(df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS"])
    diff_media = df_filtrado["diferenca_percentual_vs_media"].mean()
    diff_str = (
        f"{'+' if diff_media >= 0 else ''}{diff_media:.1f}%"
        if not pd.isna(diff_media)
        else "-"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Produtos Monitorados", fmt_int(total_produtos))
    c2.metric("Mais Caros que Todos", fmt_int(mais_caros))
    c3.metric("Mais Baratos que Todos", fmt_int(mais_baratos))
    c4.metric("Diferença Média vs Mercado", diff_str)

    st.divider()

    col_a, col_b = st.columns(2)

    # Gráfico 1 — Posicionamento por Classificação
    df_class = (
        df_filtrado.groupby("classificacao_preco", as_index=False)
        .size()
        .rename(columns={"size": "total"})
    )
    fig1 = px.pie(
        df_class,
        names="classificacao_preco",
        values="total",
        title="Posicionamento de Preço vs Concorrência",
    )
    col_a.plotly_chart(fig1, use_container_width=True)

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
        color_discrete_map={"Mais caro": "#EF553B", "Mais barato": "#00CC96"},
        title="Competitividade por Categoria",
        labels={
            "categoria": "Categoria",
            "diferenca_percentual_vs_media": "Diff % vs Média Mercado",
            "posicao": "Posição",
        },
    )
    col_b.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3 — Scatter: Competitividade x Volume
    df_scatter = df_filtrado.copy()
    df_scatter["receita_total"] = pd.to_numeric(df_scatter["receita_total"], errors="coerce").fillna(0)
    df_scatter["quantidade_total"] = pd.to_numeric(df_scatter["quantidade_total"], errors="coerce").fillna(0)
    df_scatter["diferenca_percentual_vs_media"] = pd.to_numeric(df_scatter["diferenca_percentual_vs_media"], errors="coerce").fillna(0)
    df_scatter["size_col"] = df_scatter["receita_total"].clip(lower=0) + 1  # garantir valores > 0 para size
    fig3 = px.scatter(
        df_scatter,
        x="diferenca_percentual_vs_media",
        y="quantidade_total",
        color="classificacao_preco",
        size="size_col",
        hover_name="nome_produto",
        title="Competitividade x Volume de Vendas",
        labels={
            "diferenca_percentual_vs_media": "Diff % vs Média Mercado",
            "quantidade_total": "Qtd Vendida",
            "classificacao_preco": "Classificação",
        },
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Tabela de Alertas
    st.subheader("Produtos em Alerta (mais caros que todos os concorrentes)")
    df_alerta = df_filtrado[df_filtrado["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"][
        [
            "produto_id",
            "nome_produto",
            "categoria",
            "nosso_preco",
            "preco_maximo_concorrentes",
            "diferenca_percentual_vs_media",
        ]
    ]
    st.dataframe(df_alerta, use_container_width=True)

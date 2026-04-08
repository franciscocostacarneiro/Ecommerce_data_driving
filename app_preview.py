"""
PREVIEW v3 — Estilo ECharts Streamlit App (Work Sans, Slate palette, config.toml nativo).
Execute: streamlit run app_preview.py
"""
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st
from dotenv import load_dotenv


# ── Credenciais ─────────────────────────────────────────────────────────────
def _get_postgres_url() -> str:
    try:
        url = st.secrets.get("POSTGRES_URL")
        if url:
            return url
    except Exception:
        pass
    for candidate in [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".llm" / ".env",
    ]:
        if candidate.exists():
            load_dotenv(dotenv_path=candidate)
            break
    url = os.getenv("POSTGRES_URL")
    if not url:
        st.error("Variável POSTGRES_URL não encontrada.")
        st.stop()
    return url


POSTGRES_URL = _get_postgres_url()

st.set_page_config(
    layout="wide",
    page_title="E-commerce Analytics",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS — Tailwind Slate (idêntico ao echarts.streamlit.app)
# ═══════════════════════════════════════════════════════════════════════════
BG       = "#0f172a"   # Slate-900
SURF     = "#1e293b"   # Slate-800  (cards, charts)
SURF2    = "#334155"   # Slate-700  (hover, elevado)
BORDER   = "#475569"   # Slate-600
MUTED    = "#94a3b8"   # Slate-400
TEXT     = "#f1f5f9"   # Slate-100

INDIGO   = "#6366f1"   # primary (igual ao ECharts app)
EMERALD  = "#10b981"   # positivo
ROSE     = "#f43f5e"   # alerta
AMBER    = "#f59e0b"   # atenção / VIP
SKY      = "#38bdf8"   # info / secundário

CORES_SEGMENTO = {
    "VIP":      AMBER,
    "TOP_TIER": MUTED,
    "REGULAR":  INDIGO,
}
CORES_PRICING = {
    "MAIS_CARO_QUE_TODOS":   ROSE,
    "MAIS_BARATO_QUE_TODOS": EMERALD,
    "ACIMA_DA_MEDIA":        "#f97316",
    "ABAIXO_DA_MEDIA":       SKY,
    "NA_MEDIA":              MUTED,
}

# ── CSS complementar (o grosso já vem do config.toml) ───────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Work+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

/* Fundo global */
.stApp, section[data-testid="stMain"] {{ background-color: {BG} !important; }}
.block-container {{ padding-top: 1.4rem !important; max-width: 100% !important; }}

/* Tipografia Work Sans em todo o app */
html, body, .stApp, .stMarkdown, p, span, div, button, input, label {{
    font-family: 'Work Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Sidebar — slate escura */
section[data-testid="stSidebar"] > div:first-child {{
    background-color: {SURF} !important;
    border-right: 1px solid {BORDER} !important;
}}
section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}

/* Divisores */
hr {{ border-color: {BORDER} !important; margin: 1.2rem 0 !important; }}

/* Inputs */
[data-baseweb="select"] > div {{
    background-color: {SURF} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    color: {TEXT} !important;
}}
[data-baseweb="tag"] {{ background-color: {SURF2} !important; color: {TEXT} !important; }}

/* Dataframe */
.stDataFrame {{ border-radius: 12px !important; overflow: hidden; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 6px; }}

/* Alerts */
.stAlert {{ background-color: {SURF} !important; border-radius: 12px !important; }}
.stSuccess {{ background-color: rgba(16,185,129,0.08) !important; border-color: {EMERALD} !important; }}
.stInfo {{ border-color: {INDIGO} !important; }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
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
        st.error(f"Erro de conexão: {e}")
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


def kpi_card(label: str, value: str, icon: str = "", accent: str = INDIGO) -> str:
    """Card KPI em HTML puro — independente de seletores internos do Streamlit."""
    return f"""
    <div style="
        background: {SURF};
        border-radius: 14px;
        padding: 20px 22px 18px;
        border: 1px solid {BORDER};
        border-left: 4px solid {accent};
        box-shadow: 0 2px 12px rgba(0,0,0,0.4);
        min-height: 90px;
    ">
        <div style="
            color: {MUTED};
            font-family: 'Work Sans', sans-serif;
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 10px;
            display: flex; align-items: center; gap: 7px;
        ">
            <span style="font-size:0.9rem;">{icon}</span>{label}
        </div>
        <div style="
            color: {TEXT};
            font-family: 'Work Sans', sans-serif;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.02em;
        ">{value}</div>
    </div>"""


def kpi_row(metrics: list):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.markdown(
                kpi_card(m["label"], m["value"], m.get("icon", ""), m.get("accent", INDIGO)),
                unsafe_allow_html=True,
            )


def chart_cfg(fig, title: str = "", height: int = 360):
    """Layout Plotly consistente com a paleta Slate."""
    fig.update_layout(
        paper_bgcolor=SURF,
        plot_bgcolor=SURF,
        font=dict(family="Work Sans, sans-serif", color=MUTED, size=11),
        title=dict(
            text=f"<b style='color:{TEXT};font-family:Work Sans,sans-serif'>{title}</b>" if title else "",
            font=dict(size=13, color=TEXT, family="Work Sans, sans-serif"),
            x=0.0, xanchor="left", pad=dict(l=4, t=4),
        ),
        xaxis=dict(gridcolor=SURF2, linecolor=BORDER, tickfont=dict(size=10, color=MUTED), zeroline=False),
        yaxis=dict(gridcolor=SURF2, linecolor=BORDER, tickfont=dict(size=10, color=MUTED), zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=MUTED), borderwidth=0),
        hoverlabel=dict(bgcolor=SURF2, bordercolor=BORDER, font=dict(color=TEXT, size=12, family="Work Sans, sans-serif")),
        margin=dict(l=8, r=8, t=50, b=8),
        height=height,
    )
    return fig


def page_header(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div style="
        display: flex; align-items: center; gap: 14px;
        background: {SURF};
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 22px;
        border: 1px solid {BORDER};
        border-left: 5px solid {INDIGO};
    ">
        <span style="font-size:1.6rem;">{icon}</span>
        <div>
            <div style="color:{TEXT}; font-family:'Work Sans',sans-serif; font-size:1.15rem;
                        font-weight:700; letter-spacing:-0.01em; line-height:1.2;">{title}</div>
            <div style="color:{MUTED}; font-family:'Work Sans',sans-serif; font-size:0.78rem;
                        margin-top:3px;">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_label(text: str, accent: str = INDIGO):
    st.markdown(
        f"<div style='color:{MUTED}; font-family:Work Sans,sans-serif; font-size:0.65rem; "
        f"font-weight:600; text-transform:uppercase; letter-spacing:0.12em; "
        f"border-left:3px solid {accent}; padding-left:9px; margin:20px 0 10px 0;'>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:24px 8px 24px; text-align:center;
                border-bottom:1px solid {BORDER}; margin-bottom:22px;">
        <div style="width:52px; height:52px; border-radius:14px;
                    background:linear-gradient(135deg,{INDIGO},{SURF2});
                    display:flex; align-items:center; justify-content:center;
                    font-size:1.5rem; margin:0 auto 12px; border:1px solid {BORDER};
                    box-shadow:0 4px 16px rgba(0,0,0,0.5);">
            📊
        </div>
        <div style="color:{TEXT}; font-family:'Work Sans',sans-serif; font-size:0.95rem;
                    font-weight:700; line-height:1.3;">E-commerce<br>Analytics</div>
        <div style="color:{MUTED}; font-family:'Work Sans',sans-serif; font-size:0.62rem;
                    margin-top:6px; text-transform:uppercase; letter-spacing:0.12em;">
            Intelligence Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<p style='color:{MUTED}; font-size:0.62rem; font-weight:600; font-family:Work Sans,sans-serif; "
        f"text-transform:uppercase; letter-spacing:0.12em; margin:0 0 8px 2px;'>Navegação</p>",
        unsafe_allow_html=True,
    )
    pagina = st.radio(
        label="nav",
        options=["📈  Vendas", "👥  Clientes", "🏷️  Pricing"],
        label_visibility="collapsed",
    )
    pagina = pagina.split("  ")[1]

    st.markdown(
        f"<div style='color:{MUTED}; font-size:0.62rem; font-family:Work Sans,sans-serif; "
        f"text-align:center; padding-top:28px;'>"
        f"Atualizado em {pd.Timestamp.now().strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True,
    )


# ===========================================================================
# PÁGINA 1 — VENDAS
# ===========================================================================
if pagina == "Vendas":
    page_header("📈", "Vendas", "Visão do Diretor Comercial")

    df = get_data("SELECT * FROM public_gold_sales.vendas_temporais")
    if df.empty:
        st.stop()

    for col in ["receita_total", "total_vendas", "total_clientes_unicos", "ticket_medio"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    filt_col, _ = st.columns([2, 8])
    with filt_col:
        meses = ["Todos os meses"] + [str(m) for m in sorted(df["mes_venda"].unique())]
        mes_sel = st.selectbox("Mês:", meses)

    df_f = df if mes_sel == "Todos os meses" else df[df["mes_venda"] == int(mes_sel)]
    if df_f.empty:
        st.info("Nenhum dado para o filtro selecionado.")
        st.stop()

    receita_total  = df_f["receita_total"].sum()
    total_vendas_v = df_f["total_vendas"].sum()
    ticket         = receita_total / total_vendas_v if total_vendas_v > 0 else 0
    clientes_u     = df_f["total_clientes_unicos"].sum()

    kpi_row([
        {"label": "Receita Total",   "value": fmt_brl(receita_total),  "icon": "💰", "accent": AMBER},
        {"label": "Total de Vendas", "value": fmt_int(total_vendas_v), "icon": "🛒", "accent": INDIGO},
        {"label": "Ticket Médio",    "value": fmt_brl(ticket),         "icon": "🎯", "accent": SKY},
        {"label": "Clientes Únicos", "value": fmt_int(clientes_u),     "icon": "👥", "accent": EMERALD},
    ])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    section_label("Evolução Temporal")

    df_dia = df_f.groupby("data_venda", as_index=False)["receita_total"].sum().sort_values("data_venda")
    fig1 = px.line(df_dia, x="data_venda", y="receita_total",
                   labels={"data_venda": "", "receita_total": "Receita (R$)"},
                   color_discrete_sequence=[INDIGO])
    fig1.update_traces(
        line=dict(width=2.5, color=INDIGO),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.08)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Receita: R$ %{y:,.2f}<extra></extra>",
    )
    fig1.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    chart_cfg(fig1, "Receita Diária", height=300)
    st.plotly_chart(fig1, use_container_width=True)

    section_label("Padrões de Comportamento")
    col_a, col_b = st.columns(2)

    ordem_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    df_semana = df_f.groupby("dia_semana_nome", as_index=False)["receita_total"].sum()
    df_semana["_ord"] = df_semana["dia_semana_nome"].map({d: i for i, d in enumerate(ordem_dias)})
    df_semana = df_semana.sort_values("_ord").drop(columns="_ord")
    fig2 = px.bar(df_semana, x="dia_semana_nome", y="receita_total",
                  labels={"dia_semana_nome": "", "receita_total": "Receita (R$)"},
                  color_discrete_sequence=[INDIGO])
    fig2.update_traces(marker_line_width=0, marker_cornerradius=4,
                       hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
    fig2.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    chart_cfg(fig2, "Receita por Dia da Semana")
    col_a.plotly_chart(fig2, use_container_width=True)

    df_hora = df_f.groupby("hora_venda", as_index=False)["total_vendas"].sum().sort_values("hora_venda")
    fig3 = px.bar(df_hora, x="hora_venda", y="total_vendas",
                  labels={"hora_venda": "Hora", "total_vendas": "Vendas"},
                  color_discrete_sequence=[EMERALD])
    fig3.update_traces(marker_line_width=0, marker_cornerradius=4,
                       hovertemplate="<b>%{x}h</b><br>%{y} vendas<extra></extra>")
    chart_cfg(fig3, "Volume de Vendas por Hora")
    col_b.plotly_chart(fig3, use_container_width=True)


# ===========================================================================
# PÁGINA 2 — CLIENTES
# ===========================================================================
elif pagina == "Clientes":
    page_header("👥", "Clientes", "Visão da Diretora de Customer Success")

    df = get_data("SELECT * FROM public_gold_cs.clientes_segmentacao")
    if df.empty:
        st.stop()

    for col in ["receita_total", "ticket_medio", "total_compras", "ranking_receita"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    total_clientes     = len(df)
    clientes_vip       = len(df[df["segmento_cliente"] == "VIP"])
    receita_vip        = df[df["segmento_cliente"] == "VIP"]["receita_total"].sum()
    ticket_medio_geral = df["ticket_medio"].mean()

    kpi_row([
        {"label": "Total de Clientes", "value": fmt_int(total_clientes),     "icon": "👤", "accent": INDIGO},
        {"label": "Clientes VIP",      "value": fmt_int(clientes_vip),       "icon": "⭐", "accent": AMBER},
        {"label": "Receita VIP",       "value": fmt_brl(receita_vip),        "icon": "💎", "accent": AMBER},
        {"label": "Ticket Médio",      "value": fmt_brl(ticket_medio_geral), "icon": "🎯", "accent": SKY},
    ])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    section_label("Segmentação de Clientes")
    col_a, col_b = st.columns(2)

    df_seg = df.groupby("segmento_cliente", as_index=False).size().rename(columns={"size": "total"})
    fig1 = px.pie(df_seg, names="segmento_cliente", values="total", hole=0.58,
                  color="segmento_cliente", color_discrete_map=CORES_SEGMENTO)
    fig1.update_traces(
        textinfo="percent+label",
        textfont=dict(size=11, color=TEXT, family="Work Sans, sans-serif"),
        hovertemplate="<b>%{label}</b><br>%{value} clientes (%{percent})<extra></extra>",
        insidetextorientation="horizontal",
    )
    chart_cfg(fig1, "Distribuição por Segmento", height=340)
    col_a.plotly_chart(fig1, use_container_width=True)

    df_rec_seg = df.groupby("segmento_cliente", as_index=False)["receita_total"].sum()
    fig2 = px.bar(df_rec_seg, x="segmento_cliente", y="receita_total",
                  color="segmento_cliente", color_discrete_map=CORES_SEGMENTO,
                  labels={"segmento_cliente": "", "receita_total": "Receita (R$)"})
    fig2.update_traces(marker_line_width=0, marker_cornerradius=6,
                       hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
    fig2.update_layout(showlegend=False, yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f")
    chart_cfg(fig2, "Receita por Segmento", height=340)
    col_b.plotly_chart(fig2, use_container_width=True)

    section_label("Ranking & Distribuição Geográfica")
    col_c, col_d = st.columns(2)

    df_top10 = df[df["ranking_receita"] <= 10].sort_values("receita_total", ascending=True)
    fig3 = px.bar(df_top10, x="receita_total", y="nome_cliente", orientation="h",
                  labels={"nome_cliente": "", "receita_total": "Receita (R$)"},
                  color_discrete_sequence=[AMBER])
    fig3.update_traces(marker_line_width=0, marker_cornerradius=4,
                       hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
    fig3.update_layout(xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f")
    chart_cfg(fig3, "Top 10 Clientes por Receita", height=340)
    col_c.plotly_chart(fig3, use_container_width=True)

    df_estado = (
        df.groupby("estado", as_index=False).size()
        .rename(columns={"size": "total"}).sort_values("total", ascending=False)
    )
    _GEO = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
            "master/public/data/brazil-states.geojson")
    fig4 = px.choropleth(
        df_estado, geojson=_GEO, locations="estado",
        featureidkey="properties.sigla", color="total",
        color_continuous_scale=[[0, SURF2], [1, INDIGO]],
        labels={"total": "Clientes", "estado": "UF"},
        hover_data={"estado": True, "total": True},
    )
    fig4.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig4.update_layout(
        paper_bgcolor=SURF, geo=dict(bgcolor=SURF),
        margin={"r": 0, "t": 50, "l": 0, "b": 0}, height=340,
        font=dict(family="Work Sans, sans-serif", color=MUTED, size=11),
        title=dict(text=f"<b style='color:{TEXT}'>Distribuição Geográfica</b>",
                   font=dict(size=13, color=TEXT, family="Work Sans, sans-serif"), x=0.0, xanchor="left"),
        coloraxis_colorbar=dict(
            title=dict(text="Clientes", font=dict(color=MUTED, size=10)),
            tickfont=dict(color=MUTED, size=10), thickness=10,
        ),
        hoverlabel=dict(bgcolor=SURF2, bordercolor=BORDER, font=dict(color=TEXT, size=12)),
    )
    fig4.update_traces(hovertemplate="<b>%{location}</b><br>Clientes: %{z}<extra></extra>")
    col_d.plotly_chart(fig4, use_container_width=True)

    st.divider()
    section_label("Detalhe por Cliente")
    filt_col, _ = st.columns([2, 8])
    with filt_col:
        segmentos = ["Todos"] + sorted(df["segmento_cliente"].unique().tolist())
        seg_sel = st.selectbox("Filtrar por segmento:", segmentos)
    df_tab = df if seg_sel == "Todos" else df[df["segmento_cliente"] == seg_sel]
    if df_tab.empty:
        st.info("Nenhum cliente encontrado.")
    else:
        st.dataframe(df_tab, use_container_width=True)


# ===========================================================================
# PÁGINA 3 — PRICING
# ===========================================================================
elif pagina == "Pricing":
    page_header("🏷️", "Pricing", "Visão do Diretor de Pricing")

    df = get_data("SELECT * FROM public_gold_pricing.precos_competitividade")
    if df.empty:
        st.stop()

    for col in ["nosso_preco", "preco_medio_concorrentes", "preco_minimo_concorrentes",
                "preco_maximo_concorrentes", "diferenca_percentual_vs_media",
                "diferenca_percentual_vs_minimo", "receita_total", "quantidade_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    filt_col, _ = st.columns([4, 6])
    with filt_col:
        cat_sel = st.multiselect("Filtrar por categoria:", sorted(df["categoria"].unique()))
    df_f = df[df["categoria"].isin(cat_sel)] if cat_sel else df

    if df_f.empty:
        st.info("Nenhum produto encontrado.")
        st.stop()

    total_produtos = len(df_f)
    mais_caros     = len(df_f[df_f["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"])
    mais_baratos   = len(df_f[df_f["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS"])
    diff_media     = df_f["diferenca_percentual_vs_media"].mean()
    diff_str       = (f"{'+' if diff_media >= 0 else ''}{diff_media:.1f}%"
                      if not pd.isna(diff_media) else "-")
    diff_accent    = ROSE if diff_media > 0 else EMERALD

    kpi_row([
        {"label": "Produtos Monitorados",      "value": fmt_int(total_produtos), "icon": "📦", "accent": INDIGO},
        {"label": "Mais Caros que Todos",       "value": fmt_int(mais_caros),    "icon": "🔴", "accent": ROSE},
        {"label": "Mais Baratos que Todos",     "value": fmt_int(mais_baratos),  "icon": "🟢", "accent": EMERALD},
        {"label": "Diferença Média vs Mercado", "value": diff_str,               "icon": "📊", "accent": diff_accent},
    ])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    section_label("Posicionamento Competitivo")
    col_a, col_b = st.columns(2)

    df_class = df_f.groupby("classificacao_preco", as_index=False).size().rename(columns={"size": "total"})
    fig1 = px.pie(df_class, names="classificacao_preco", values="total", hole=0.58,
                  color="classificacao_preco", color_discrete_map=CORES_PRICING)
    fig1.update_traces(
        textinfo="percent+label",
        textfont=dict(size=11, color=TEXT, family="Work Sans, sans-serif"),
        hovertemplate="<b>%{label}</b><br>%{value} produtos (%{percent})<extra></extra>",
        insidetextorientation="horizontal",
    )
    chart_cfg(fig1, "Posicionamento vs Concorrência", height=340)
    col_a.plotly_chart(fig1, use_container_width=True)

    df_cat = df_f.groupby("categoria", as_index=False)["diferenca_percentual_vs_media"].mean()
    df_cat["posicao"] = df_cat["diferenca_percentual_vs_media"].apply(
        lambda x: "Mais caro" if x > 0 else "Mais barato"
    )
    fig2 = px.bar(df_cat, x="categoria", y="diferenca_percentual_vs_media", color="posicao",
                  color_discrete_map={"Mais caro": ROSE, "Mais barato": EMERALD},
                  labels={"categoria": "", "diferenca_percentual_vs_media": "Diff % vs Média", "posicao": ""})
    fig2.update_traces(marker_line_width=0, marker_cornerradius=4,
                       hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>")
    fig2.add_hline(y=0, line_dash="dot", line_color=MUTED, opacity=0.4)
    chart_cfg(fig2, "Competitividade por Categoria", height=340)
    col_b.plotly_chart(fig2, use_container_width=True)

    section_label("Análise de Correlação: Preço × Volume")
    df_scatter = df_f.copy()
    df_scatter["size_col"] = df_scatter["receita_total"].clip(lower=0) + 1
    fig3 = px.scatter(
        df_scatter,
        x="diferenca_percentual_vs_media", y="quantidade_total",
        color="classificacao_preco", size="size_col",
        hover_name="nome_produto",
        hover_data={"size_col": False, "categoria": True, "nosso_preco": True},
        labels={"diferenca_percentual_vs_media": "Diff % vs Média",
                "quantidade_total": "Qtd Vendida", "classificacao_preco": "Classificação"},
        color_discrete_map=CORES_PRICING,
    )
    fig3.add_vline(x=0, line_dash="dot", line_color=MUTED, opacity=0.4)
    chart_cfg(fig3, "Competitividade × Volume de Vendas", height=400)
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    section_label("🚨  Alertas — Produtos mais caros que todos os concorrentes", accent=ROSE)
    df_alerta = df_f[df_f["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"][[
        "produto_id", "nome_produto", "categoria",
        "nosso_preco", "preco_maximo_concorrentes", "diferenca_percentual_vs_media",
    ]].sort_values("diferenca_percentual_vs_media", ascending=False)

    if df_alerta.empty:
        st.success("Nenhum produto mais caro que todos os concorrentes no filtro atual.")
    else:
        st.caption(f"{len(df_alerta)} produto(s) precisam de revisão de preço.")
        st.dataframe(df_alerta, use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Restaurant Campaign Performance", layout="wide")

st.markdown("""
<style>
    .kpi-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .kpi-label {
        font-size: 12px;
        color: #a6adc8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #cdd6f4;
    }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #cdd6f4;
        margin: 24px 0 10px 0;
        border-bottom: 1px solid #313244;
        padding-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

METRIC_COLS = [
    "Incr Txns", "Incr Burn", "Incr GMV",
    "Incr New Txns", "Campaign ULV", "Campaign Incr ULV",
]

CHART_GROUPS = [
    ("Transactions", ["Incr Txns", "Incr New Txns"],       ["#89b4fa", "#b4befe"]),
    ("Burn & GMV",   ["Incr Burn", "Incr GMV"],             ["#f38ba8", "#fab387"]),
    ("ULV",          ["Campaign ULV", "Campaign Incr ULV"], ["#a6e3a1", "#94e2d5"]),
]

CHART_THEME = dict(
    plot_bgcolor="#1e1e2e",
    paper_bgcolor="#1e1e2e",
    font_color="#cdd6f4",
    margin=dict(t=40, b=20, l=10, r=10),
    xaxis=dict(gridcolor="#313244"),
    yaxis=dict(gridcolor="#313244"),
    legend=dict(bgcolor="#1e1e2e"),
    height=320,
)


def fmt_val(val):
    try:
        return f"{val:,.2f}"
    except Exception:
        return str(val)


def generate_sample_data():
    rng = np.random.default_rng(42)
    restaurants = [
        "Burger Palace", "Sushi Zen", "Taco Fiesta", "Pizza Heaven",
        "Noodle House", "The Grill Co", "Green Bowl", "Spice Route",
    ]
    rows = []
    for r in restaurants:
        start = pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 60)))
        end   = start + pd.Timedelta(days=int(rng.integers(14, 45)))
        rows.append({
            "Restaurant Name":   r,
            "Campaign Start":    start.strftime("%Y-%m-%d"),
            "Campaign End":      end.strftime("%Y-%m-%d"),
            "Incr Txns":         round(rng.uniform(200, 2000), 2),
            "Incr Burn":         round(rng.uniform(500, 15000), 2),
            "Incr GMV":          round(rng.uniform(1000, 50000), 2),
            "Incr New Txns":     round(rng.uniform(50, 800), 2),
            "Campaign ULV":      round(rng.uniform(20, 120), 2),
            "Campaign Incr ULV": round(rng.uniform(5, 60), 2),
        })
    return pd.DataFrame(rows)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Campaign Dashboard")
    st.markdown("---")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.success(f"Loaded {len(df)} rows")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            df = generate_sample_data()
    else:
        df = generate_sample_data()
        st.info("Showing sample data")

    df.columns = [c.strip() for c in df.columns]

    missing = ({"Restaurant Name"} | set(METRIC_COLS)) - set(df.columns)
    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    st.markdown("---")
    restaurants = sorted(df["Restaurant Name"].dropna().unique().tolist())
    selected = st.selectbox("Select Restaurant", restaurants)

# ── Filter ────────────────────────────────────────────────────────────────────
row = df[df["Restaurant Name"] == selected].iloc[0]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## {selected}")

date_cols = [c for c in ["Campaign Start", "Campaign End"] if c in df.columns]
if date_cols:
    st.markdown("  ·  ".join(f"**{c}:** {row[c]}" for c in date_cols))

st.markdown("---")

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)

cols = st.columns(len(METRIC_COLS))
for col_ui, metric in zip(cols, METRIC_COLS):
    val = row[metric]
    col_ui.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{metric}</div>
        <div class="kpi-value">{fmt_val(val)}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Bar Charts ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Metric Charts</div>', unsafe_allow_html=True)

chart_cols = st.columns(3)
for col_ui, (title, metrics, colors) in zip(chart_cols, CHART_GROUPS):
    fig = go.Figure()
    for metric, color in zip(metrics, colors):
        val = row[metric]
        fig.add_trace(go.Bar(
            name=metric,
            x=[metric],
            y=[val],
            marker_color=color,
            text=[fmt_val(val)],
            textposition="outside",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#cdd6f4")),
        showlegend=True,
        barmode="group",
        **CHART_THEME,
    )
    col_ui.plotly_chart(fig, use_container_width=True)

# ── Full Table ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">All Restaurants</div>', unsafe_allow_html=True)


def highlight_row(row_data):
    base      = "background-color: #1e1e2e; color: #cdd6f4"
    highlight = "background-color: #313244; color: #89b4fa; font-weight: 600"
    return [highlight if row_data["Restaurant Name"] == selected else base] * len(row_data)


display_df = df.copy()
for m in METRIC_COLS:
    if m in display_df.columns:
        display_df[m] = display_df[m].apply(lambda x: f"{x:,.2f}")

styled = display_df.style.apply(highlight_row, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.download_button(
    label="⬇ Download data as CSV",
    data=df.to_csv(index=False).encode(),
    file_name="campaign_data.csv",
    mime="text/csv",
)

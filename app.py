import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

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
    .kpi-delta {
        font-size: 13px;
        margin-top: 4px;
    }
    .delta-up   { color: #a6e3a1; }
    .delta-down { color: #f38ba8; }
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

METRIC_FMT = {
    "Incr Txns":        ("{:,.0f}",  ""),
    "Incr Burn":        ("${:,.2f}", ""),
    "Incr GMV":         ("${:,.2f}", ""),
    "Incr New Txns":    ("{:,.0f}",  ""),
    "Campaign ULV":     ("${:,.2f}", ""),
    "Campaign Incr ULV":("${:,.2f}", ""),
}


def fmt_val(col, val):
    pattern, _ = METRIC_FMT.get(col, ("{}", ""))
    try:
        return pattern.format(val)
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
            "Restaurant Name":  r,
            "Campaign Start":   start.strftime("%Y-%m-%d"),
            "Campaign End":     end.strftime("%Y-%m-%d"),
            "Incr Txns":        round(rng.uniform(200, 2000)),
            "Incr Burn":        round(rng.uniform(500, 15000), 2),
            "Incr GMV":         round(rng.uniform(1000, 50000), 2),
            "Incr New Txns":    round(rng.uniform(50, 800)),
            "Campaign ULV":     round(rng.uniform(20, 120), 2),
            "Campaign Incr ULV":round(rng.uniform(5, 60), 2),
        })
    return pd.DataFrame(rows)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Campaign Dashboard")
    st.markdown("---")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    use_sample = st.checkbox("Use sample data", value=uploaded is None)

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
        if use_sample:
            st.info("Showing sample data")

    # normalise column names (strip whitespace)
    df.columns = [c.strip() for c in df.columns]

    required = {"Restaurant Name"} | set(METRIC_COLS)
    missing  = required - set(df.columns)
    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    st.markdown("---")
    restaurants = sorted(df["Restaurant Name"].dropna().unique().tolist())
    selected = st.selectbox("Select Restaurant", restaurants)

    show_compare = st.toggle("Compare vs all restaurants", value=True)

# ── Filter ───────────────────────────────────────────────────────────────────
row = df[df["Restaurant Name"] == selected].iloc[0]
avg = df[METRIC_COLS].mean()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"## {selected}")

date_cols = [c for c in ["Campaign Start", "Campaign End"] if c in df.columns]
if date_cols:
    date_str = "  ·  ".join(f"**{c}:** {row[c]}" for c in date_cols)
    st.markdown(date_str)

st.markdown("---")

# ── KPI Cards ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)

cols = st.columns(len(METRIC_COLS))
for col_ui, metric in zip(cols, METRIC_COLS):
    val     = row[metric]
    avg_val = avg[metric]
    delta   = val - avg_val
    pct     = (delta / avg_val * 100) if avg_val else 0
    arrow   = "▲" if delta >= 0 else "▼"
    cls     = "delta-up" if delta >= 0 else "delta-down"
    delta_html = (
        f'<div class="kpi-delta {cls}">{arrow} {abs(pct):.1f}% vs avg</div>'
        if show_compare else ""
    )
    col_ui.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{metric}</div>
        <div class="kpi-value">{fmt_val(metric, val)}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ── Bar Chart ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Metric Comparison</div>', unsafe_allow_html=True)

norm_selected = [(row[m] / avg[m] - 1) * 100 if avg[m] else 0 for m in METRIC_COLS]

if show_compare:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=selected,
        x=METRIC_COLS,
        y=[row[m] for m in METRIC_COLS],
        marker_color="#89b4fa",
        text=[fmt_val(m, row[m]) for m in METRIC_COLS],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="All Restaurants Avg",
        x=METRIC_COLS,
        y=[avg[m] for m in METRIC_COLS],
        marker_color="#6c7086",
        text=[fmt_val(m, avg[m]) for m in METRIC_COLS],
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        legend=dict(bgcolor="#1e1e2e"),
        margin=dict(t=30, b=20),
        xaxis=dict(gridcolor="#313244"),
        yaxis=dict(gridcolor="#313244"),
        height=380,
    )
else:
    fig = go.Figure(go.Bar(
        x=METRIC_COLS,
        y=[row[m] for m in METRIC_COLS],
        marker_color="#89b4fa",
        text=[fmt_val(m, row[m]) for m in METRIC_COLS],
        textposition="outside",
    ))
    fig.update_layout(
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        margin=dict(t=30, b=20),
        xaxis=dict(gridcolor="#313244"),
        yaxis=dict(gridcolor="#313244"),
        height=360,
    )

st.plotly_chart(fig, use_container_width=True)

# ── Full Table ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">All Restaurants</div>', unsafe_allow_html=True)


def highlight_row(row_data):
    base = "background-color: #1e1e2e; color: #cdd6f4"
    highlight = "background-color: #313244; color: #89b4fa; font-weight: 600"
    return [highlight if row_data["Restaurant Name"] == selected else base] * len(row_data)


display_df = df.copy()
for m in ["Incr Burn", "Incr GMV", "Campaign ULV", "Campaign Incr ULV"]:
    if m in display_df.columns:
        display_df[m] = display_df[m].apply(lambda x: f"${x:,.2f}")
for m in ["Incr Txns", "Incr New Txns"]:
    if m in display_df.columns:
        display_df[m] = display_df[m].apply(lambda x: f"{int(x):,}")

styled = display_df.style.apply(highlight_row, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
csv_bytes = df.to_csv(index=False).encode()
st.download_button(
    label="⬇ Download data as CSV",
    data=csv_bytes,
    file_name="campaign_data.csv",
    mime="text/csv",
)

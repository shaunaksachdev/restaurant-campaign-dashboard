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
        padding: 16px 14px;
        text-align: center;
    }
    .kpi-label {
        font-size: 11px;
        color: #a6adc8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #cdd6f4;
    }
    .section-title {
        font-size: 15px;
        font-weight: 600;
        color: #cdd6f4;
        margin: 22px 0 10px 0;
        border-bottom: 1px solid #313244;
        padding-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ── Column definitions ────────────────────────────────────────────────────────

# D–M: paired bar charts (base vs incremental)
BAR_PAIRS = [
    ("GMV",       "gmv(camp)",       "inc_gmv(camp)"),
    ("Txns",      "txns(campaign)",  "inc_txns (campaign)"),
    ("ULV",       "ulv (camp)",      "inc_ulv(camp)"),
    ("New Txns",  "n_txns (camp)",   "inc_n_txns(sum)"),
    ("Bookings",  "bookings (camp)", "inc_bookings (camp)"),
]

# N–S: individual line charts over time
LINE_COLS = ["gmv", "ulv", "txns", "n_txns", "bookings_made", "u2t"]

# T–Z: KPI cards
KPI_COLS = [
    "inc_burn (campaign)",
    "inc_cpit(campaign)",
    "txns growth (campaign)",
    "ulv growth (Campaign growth)",
    "Banner impressions",
    "Banner clicks",
    "banner ctr",
]

CHART_BASE = dict(
    plot_bgcolor="#1e1e2e",
    paper_bgcolor="#1e1e2e",
    font_color="#cdd6f4",
    margin=dict(t=40, b=20, l=10, r=10),
    xaxis=dict(gridcolor="#313244", showgrid=True),
    yaxis=dict(gridcolor="#313244", showgrid=True),
    legend=dict(bgcolor="#1e1e2e", font=dict(size=11)),
    height=300,
)

BAR_COLORS = [
    ("#89b4fa", "#b4befe"),
    ("#f38ba8", "#fab387"),
    ("#a6e3a1", "#94e2d5"),
    ("#cba6f7", "#f5c2e7"),
    ("#f9e2af", "#eba0ac"),
]


def fmt(val):
    try:
        f = float(val)
        if abs(f) >= 1_000_000:
            return f"{f/1_000_000:.2f}M"
        if abs(f) >= 1_000:
            return f"{f:,.1f}"
        return f"{f:,.2f}"
    except Exception:
        return str(val)


def generate_sample_data():
    rng = np.random.default_rng(42)
    cams = ["Burger Palace_w16", "Sushi Zen_w16", "Taco Fiesta_w16", "Pizza Heaven_w16"]
    rows = []
    for cam in cams:
        for day_offset in range(7):
            dt = pd.Timestamp("2026-04-13") + pd.Timedelta(days=day_offset)
            base_gmv   = rng.uniform(100_000, 500_000)
            base_txns  = rng.uniform(50, 200)
            base_ulv   = rng.uniform(300, 1500)
            base_ntxns = rng.uniform(10, 60)
            base_book  = rng.uniform(20, 100)
            rows.append({
                "dt":                          dt.strftime("%m/%d/%Y"),
                "city":                        rng.choice(["Delhi", "Mumbai", "Bangalore"]),
                "cam":                         cam,
                "gmv(camp)":                   round(base_gmv, 2),
                "inc_gmv(camp)":               round(base_gmv * rng.uniform(0.4, 0.7), 2),
                "txns(campaign)":              round(base_txns, 2),
                "inc_txns (campaign)":         round(base_txns * rng.uniform(0.3, 0.6), 2),
                "ulv (camp)":                  round(base_ulv, 2),
                "inc_ulv(camp)":               round(base_ulv * rng.uniform(0.2, 0.5), 2),
                "n_txns (camp)":               round(base_ntxns, 2),
                "inc_n_txns(sum)":             round(base_ntxns * rng.uniform(0.3, 0.7), 2),
                "bookings (camp)":             round(base_book, 2),
                "inc_bookings (camp)":         round(base_book * rng.uniform(0.4, 0.8), 2),
                "gmv":                         round(base_gmv * rng.uniform(0.8, 1.2), 2),
                "ulv":                         round(base_ulv * rng.uniform(0.9, 1.1), 2),
                "txns":                        round(base_txns * rng.uniform(0.9, 1.1), 2),
                "n_txns":                      round(base_ntxns * rng.uniform(0.8, 1.2), 2),
                "bookings_made":               round(base_book * rng.uniform(0.8, 1.2), 2),
                "u2t":                         round(rng.uniform(5, 25), 2),
                "inc_burn (campaign)":         round(rng.uniform(-20000, 50000), 2),
                "inc_cpit(campaign)":          round(rng.uniform(-500, 1000), 2),
                "txns growth (campaign)":      round(rng.uniform(1.0, 3.5), 4),
                "ulv growth (Campaign growth)":round(rng.uniform(1.0, 3.5), 4),
                "Banner impressions":          round(rng.uniform(10000, 200000)),
                "Banner clicks":               round(rng.uniform(100, 5000)),
                "banner ctr":                  round(rng.uniform(0.005, 0.05), 4),
            })
    return pd.DataFrame(rows)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Campaign Dashboard")
    st.markdown("---")

    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            st.success(f"Loaded {len(df)} rows")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            df = generate_sample_data()
    else:
        df = generate_sample_data()
        st.info("Showing sample data")

    df.columns = [c.strip() for c in df.columns]

    cam_col = "cam" if "cam" in df.columns else df.columns[0]

    st.markdown("---")
    campaigns = sorted(df[cam_col].dropna().unique().tolist())
    selected = st.selectbox("Select Restaurant / Campaign", campaigns)

# ── Filter rows for selected campaign ────────────────────────────────────────
sel_df = df[df[cam_col] == selected].copy()

# Campaign-level values: D–M and T–Z repeat per row, so take first
camp_row = sel_df.iloc[0]

# Sort daily rows by date for line charts
if "dt" in sel_df.columns:
    sel_df["_dt"] = pd.to_datetime(sel_df["dt"], dayfirst=False, errors="coerce")
    sel_df = sel_df.sort_values("_dt")
    dates = sel_df["_dt"]
else:
    dates = pd.Series(range(len(sel_df)))

# ── Header ────────────────────────────────────────────────────────────────────
city = camp_row.get("city", "")
st.markdown(f"## {selected}" + (f"  —  {city}" if city else ""))

st.markdown("---")

# ── Section 1a: KPI Cards (D,F,H,J,L) ───────────────────────────────────────
present_pairs = [(title, base, incr) for title, base, incr in BAR_PAIRS
                 if base in df.columns and incr in df.columns]

if present_pairs:
    base_cols = [(title, base) for title, base, incr in present_pairs]
    top_kpi_cols = st.columns(len(base_cols))
    for col_ui, (title, base_col) in zip(top_kpi_cols, base_cols):
        val = camp_row.get(base_col, "—")
        col_ui.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{fmt(val)}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Section 1b: KPI Cards (T–Z) ──────────────────────────────────────────────
present_kpi = [c for c in KPI_COLS if c in df.columns]
if present_kpi:
    st.markdown('<div class="section-title">Campaign KPIs</div>', unsafe_allow_html=True)
    kpi_cols = st.columns(len(present_kpi))
    for col_ui, metric in zip(kpi_cols, present_kpi):
        val = camp_row.get(metric, "—")
        label = metric.replace("(campaign)", "").replace("(Campaign growth)", "").replace("(camp)", "").strip()
        col_ui.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{fmt(val)}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Section 2: Bar Charts (D–M, paired) ──────────────────────────────────────
if present_pairs:
    st.markdown('<div class="section-title">Campaign vs Incremental</div>', unsafe_allow_html=True)

    per_row = 3
    for row_start in range(0, len(present_pairs), per_row):
        chunk = present_pairs[row_start:row_start + per_row]
        bar_cols = st.columns(per_row)
        for col_ui, (title, base_col, incr_col), (c1, c2) in zip(
            bar_cols, chunk, BAR_COLORS[row_start:]
        ):
            base_val = camp_row.get(base_col, 0)
            incr_val = camp_row.get(incr_col, 0)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name=base_col,
                x=[base_col.split("(")[0].strip()],
                y=[base_val],
                marker_color=c1,
                text=[fmt(base_val)],
                textposition="outside",
            ))
            fig.add_trace(go.Bar(
                name=incr_col,
                x=[incr_col.split("(")[0].strip()],
                y=[incr_val],
                marker_color=c2,
                text=[fmt(incr_val)],
                textposition="outside",
            ))
            fig.update_layout(
                title=dict(text=title, font=dict(size=13, color="#cdd6f4")),
                barmode="group",
                showlegend=False,
                **CHART_BASE,
            )
            col_ui.plotly_chart(fig, use_container_width=True)

# ── Section 3: Line Charts (N–S) ─────────────────────────────────────────────
present_lines = [c for c in LINE_COLS if c in df.columns]

if present_lines:
    st.markdown('<div class="section-title">Daily Trends</div>', unsafe_allow_html=True)

    LINE_COLORS = ["#89b4fa", "#a6e3a1", "#f38ba8", "#fab387", "#cba6f7", "#f9e2af"]
    per_row = 3
    for row_start in range(0, len(present_lines), per_row):
        chunk = present_lines[row_start:row_start + per_row]
        line_cols = st.columns(per_row)
        for col_ui, metric, color in zip(line_cols, chunk, LINE_COLORS[row_start:]):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=sel_df[metric],
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
                name=metric,
            ))
            fig.update_layout(
                title=dict(text=metric, font=dict(size=13, color="#cdd6f4")),
                showlegend=False,
                **CHART_BASE,
            )
            col_ui.plotly_chart(fig, use_container_width=True)

# ── Full Table ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">All Data</div>', unsafe_allow_html=True)


def highlight_row(row_data):
    base      = "background-color: #1e1e2e; color: #cdd6f4"
    highlight = "background-color: #313244; color: #89b4fa; font-weight: 600"
    return [highlight if row_data.get(cam_col) == selected else base] * len(row_data)


display_df = df.drop(columns=["_dt"], errors="ignore").copy()
styled = display_df.style.apply(highlight_row, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.download_button(
    label="⬇ Download data as CSV",
    data=df.drop(columns=["_dt"], errors="ignore").to_csv(index=False).encode(),
    file_name="campaign_data.csv",
    mime="text/csv",
)

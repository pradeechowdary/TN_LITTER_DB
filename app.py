import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

# =====================================================
# GLOBAL CONFIG
# =====================================================
pio.templates.default = "plotly_white"

st.set_page_config(
    page_title="TN Litter Dashboard",
    page_icon="🗺️",
    layout="wide",
)

# =====================================================
# PATHS
# =====================================================
BASE = Path(__file__).parent

STATE_FILE = BASE / "state_year_kpis.csv"
MAP_FILE = BASE / "TN_Litter_Map_County_Year.csv"
GEOJSON_FILE = BASE / "tn_counties.geojson"
GEOJSON_KEY = "NAME"

# =====================================================
# STYLING
# =====================================================
st.markdown("""
<style>
.block-container { padding-top: 0.8rem; }

.panel {
  background: #0b0f14;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #1f2937;
}

.overview-text h2 {
  margin-top: 0;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD DATA (CACHED)
# =====================================================
@st.cache_data(show_spinner=False)
def load_data():
    df_state = pd.read_csv(STATE_FILE)
    df_map = pd.read_csv(MAP_FILE)
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    df_map["county"] = df_map["county"].str.strip()
    return df_state, df_map, geojson

df_state, df_map, geojson = load_data()

years = sorted(df_state["year"].unique())
counties = sorted(df_map["county"].unique())

# =====================================================
# GLOBAL CONTROLS
# =====================================================
c1, c2, c3 = st.columns([1.2, 1.4, 1.6])

with c1:
    year = st.selectbox("Select Fiscal Year", years, index=len(years)-1)

with c2:
    metric = st.radio(
        "Map Metric",
        ["litter", "recycled", "dumps"],
        horizontal=True
    )

with c3:
    selected_county = st.selectbox(
        "Select County (for trend)",
        counties,
        index=counties.index("Anderson") if "Anderson" in counties else 0
    )

# =====================================================
# TABS
# =====================================================
tab_overview, tab_trends, tab_compare, tab_summary = st.tabs(
    ["🗺️ Overview", "📈 Trends", "📊 Comparisons", "📌 Summary"]
)

# =====================================================
# TAB 1 — OVERVIEW
# =====================================================
with tab_overview:
    left, center, right = st.columns([1.2, 2.8, 1.8], gap="large")

    # ---------- LEFT TEXT ----------
    with left:
        st.markdown('<div class="panel overview-text">', unsafe_allow_html=True)
        st.markdown("## Overview")
        st.write("""
This dashboard provides a statewide view of **litter collection**,
**recycling efforts**, and **dump site activity** across Tennessee.

The **county map** is the primary overview, helping identify
spatial patterns for the selected year.
""")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- CENTER MAP ----------
    with center:
        d = df_map[df_map["year"] == year].copy()

        if not d.empty:
            max_val = d[metric].max()
            bins = [0, .2*max_val, .4*max_val, .6*max_val, .8*max_val, max_val]
            labels = ["Very Low", "Low", "Medium", "High", "Very High"]
            d["Intensity"] = pd.cut(d[metric], bins=bins, labels=labels, include_lowest=True)

            palette = (
                ["#fff5eb", "#fdd0a2", "#fdae6b", "#e6550d", "#a63603"]
                if metric == "litter" else
                ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"]
                if metric == "recycled" else
                ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"]
            )

            fig_map = px.choropleth_mapbox(
                d,
                geojson=geojson,
                locations="county",
                featureidkey=f"properties.{GEOJSON_KEY}",
                color="Intensity",
                hover_name="county",
                hover_data={
                    "litter": ":,.0f",
                    "recycled": ":,.0f",
                    "dumps": True,
                },
                mapbox_style="carto-positron",
                zoom=5.8,
                center={"lat": 35.75, "lon": -86.4},
                color_discrete_sequence=palette,
            )

            fig_map.update_layout(
                height=520,
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(
                    title="Intensity",
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#d1d5db",
                    borderwidth=1,
                ),
            )

            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No data available for selected year.")

    # ---------- RIGHT TREND ----------
    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"### {selected_county} Trend")

        county_trend = (
            df_map[df_map["county"] == selected_county]
            .sort_values("year")
        )

        if not county_trend.empty:
            fig_trend = px.line(
                county_trend,
                x="year",
                y=["litter", "recycled"],
                markers=True,
            )
            fig_trend.update_layout(height=360)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No trend data available for this county.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- KPI ROW ----------
    st.markdown("### Key Metrics")

    row = df_state[df_state["year"] == year].iloc[0]
    k1, k2, k3, k4 = st.columns(4)

    def fmt(x):
        if x >= 1_000_000:
            return f"{x/1_000_000:.1f}M"
        if x >= 1_000:
            return f"{x/1_000:.1f}K"
        return f"{int(x)}"

    k1.metric("Total Litter (lbs)", fmt(row["litter"]))
    k2.metric("Recycled (lbs)", fmt(row["recycled"]))
    k3.metric("Dump Sites", fmt(row["dumps"]))
    k4.metric("Partners", fmt(row["partners"]))

# =====================================================
# TAB 2 — STATEWIDE TRENDS
# =====================================================
with tab_trends:
    fig = px.line(
        df_state.sort_values("year"),
        x="year",
        y=["litter", "recycled"],
        markers=True,
    )
    fig.update_layout(height=520)
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 3 — COMPARISONS
# =====================================================
with tab_compare:
    top = (
        df_map[df_map["year"] == year]
        .sort_values(metric, ascending=False)
        .head(10)
    )

    fig = px.bar(
        top,
        x="county",
        y=metric,
        title=f"Top 10 Counties by {metric.title()}",
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 4 — SUMMARY
# =====================================================
with tab_summary:
    st.write("High-level summary and interpretation can go here.")

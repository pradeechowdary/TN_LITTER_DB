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
DATA = BASE / "data"

STATE_FILE = DATA / "state_year_kpis.csv"
MAP_FILE = DATA / "TN_Litter_Map_County_Year.csv"
GEOJSON_FILE = DATA / "tn_counties.geojson"
GEOJSON_KEY = "NAME"

# =====================================================
# STYLING
# =====================================================
st.markdown("""
<style>
.block-container { padding-top: 0.8rem; }

.header {
  background: #1fb6a6;
  padding: 16px 24px;
  border-radius: 14px;
  color: white;
  margin-bottom: 10px;
}

.header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
}

.panel {
  background: white;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid #e5e7eb;
}

.overview-text h2 {
  margin-top: 0;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD DATA
# =====================================================
df_state = pd.read_csv(STATE_FILE)
df_map = pd.read_csv(MAP_FILE)
geojson = json.load(open(GEOJSON_FILE, "r", encoding="utf-8"))

df_map["county"] = df_map["county"].str.strip()
years = sorted(df_state["year"].unique())

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="header">
  <h1>Tennessee Statewide Litter, Recycling & Dump Sites</h1>
</div>
""", unsafe_allow_html=True)

# =====================================================
# GLOBAL CONTROLS
# =====================================================
c1, c2 = st.columns([1.3, 1])

with c1:
    year = st.selectbox("Select Year", years, index=len(years)-1)

with c2:
    metric = st.radio(
        "Map Metric",
        ["litter", "recycled", "dumps"],
        horizontal=True
    )

# =====================================================
# TABS
# =====================================================
tab_overview, tab_trends, tab_compare, tab_summary = st.tabs(
    ["🗺️ Overview", "📈 Trends", "📊 Comparisons", "📌 Summary"]
)

# =====================================================
# TAB 1 — OVERVIEW (COUNTY MAP HERO)
# =====================================================
with tab_overview:
    left, right = st.columns([1, 2.3], gap="large")

    # ---- LEFT TEXT (like ArcGIS reference)
    with left:
        st.markdown('<div class="panel overview-text">', unsafe_allow_html=True)
        st.markdown("## Overview")
        st.write("""
This dashboard provides a statewide view of litter collection,
recycling efforts, and dump site activity across Tennessee.

The **county map** is the primary overview, allowing users to visually
identify spatial patterns and regional differences for the selected year.
""")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- RIGHT MAP (BIG, CLEAN)
    with right:
        d = df_map[df_map["year"] == year].copy()
        values = d[metric]

        # Stable bins (ArcGIS-like)
        max_val = values.max()
        bins = [0, 0.2*max_val, 0.4*max_val, 0.6*max_val, 0.8*max_val, max_val]
        labels = ["Very Low", "Low", "Medium", "High", "Very High"]
        d["Intensity"] = pd.cut(values, bins=bins, labels=labels, include_lowest=True)

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
            height=650,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                title="Intensity",
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#d1d5db",
                borderwidth=1,
                x=0.98,
                y=0.02,
                xanchor="right",
                yanchor="bottom",
            ),
        )

        st.plotly_chart(fig_map, use_container_width=True)

# =====================================================
# TAB 2 — TRENDS
# =====================================================
with tab_trends:
    st.markdown("## Statewide Trends Over Time")

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
    st.markdown("## County Comparison")

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
# TAB 4 — SUMMARY / KPIs
# =====================================================
with tab_summary:
    st.markdown("## Key Metrics")

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

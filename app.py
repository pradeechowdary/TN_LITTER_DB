"""
Streamlit dashboard for Tennessee litter, recycling and dump site analytics.

This version extends the original dashboard by introducing monthly data
support, improved trend visualisations and a more informative homepage.
The overall structure, look and feel of the original application have
been preserved to minimise disruption to existing users.

Key enhancements:

* Monthly county‐level data is loaded from ``data/monthly_county.csv``
  and exposed alongside the existing yearly datasets. A new line chart
  on the overview tab plots litter and recycling volumes by month for
  the selected county and fiscal year.
* Statewide recycling trends are displayed as a year‑over‑year growth
  bar chart instead of a simple line plot. This makes it easier to
  answer the question “Is recycling improving year over year in
  Tennessee?”. Positive growth is shown in green while negative growth
  is shown in red.
* Summary KPI cards for litter, recycling, dumps and partners are
  displayed on the homepage under the map. They update based on the
  selected fiscal year just like the original summary tab.

The remainder of the application—including the map, comparison tab
and overall layout—remains unchanged from the baseline implementation.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
DATA_DIR = BASE / "data"

# Yearly datasets
YEARLY_STATE_FILE = DATA_DIR / "yearly_state.csv"
YEARLY_COUNTY_FILE = DATA_DIR / "yearly_county.csv"

# Monthly datasets
MONTHLY_COUNTY_FILE = DATA_DIR / "monthly_county.csv"
MONTHLY_STATE_FILE = DATA_DIR / "monthly_state.csv"

# GeoJSON
GEOJSON_FILE = DATA_DIR / "geojson.json"
GEOJSON_KEY = "NAME"


# =====================================================
# STYLING
# =====================================================
st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)


# =====================================================
# LOAD DATA (CACHED)
# =====================================================
@st.cache_data(show_spinner=False)
def load_yearly_data():
    """Load yearly state and county data along with the GeoJSON.

    Returns
    -------
    tuple(pandas.DataFrame, pandas.DataFrame, dict)
        The state KPI data, county map data and GeoJSON definition.
    """
    df_state = pd.read_csv(YEARLY_STATE_FILE)
    df_map = pd.read_csv(YEARLY_COUNTY_FILE)
    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    # Normalise county names for consistent matching
    df_map["county"] = df_map["county"].str.strip()
    return df_state, df_map, geojson


@st.cache_data(show_spinner=False)
def load_monthly_data():
    """Load monthly county and state aggregates.

    Returns
    -------
    tuple(pandas.DataFrame, pandas.DataFrame)
        The monthly county‐level data and aggregated monthly state data.
        If the files are missing or invalid, empty DataFrames are
        returned instead of raising an exception.
    """
    try:
        df_monthly_county = pd.read_csv(MONTHLY_COUNTY_FILE)
    except Exception:
        df_monthly_county = pd.DataFrame()
    try:
        df_monthly_state = pd.read_csv(MONTHLY_STATE_FILE)
    except Exception:
        df_monthly_state = pd.DataFrame()
    return df_monthly_county, df_monthly_state


# Load datasets
df_state, df_map, geojson = load_yearly_data()
df_monthly_county, df_monthly_state = load_monthly_data()

# Prepare options
years = sorted(df_state["year"].unique())
counties = sorted(df_map["county"].unique())


# =====================================================
# GLOBAL CONTROLS
# =====================================================
c1, c2, c3 = st.columns([1.2, 1.4, 1.6])

with c1:
    # The most recent fiscal year appears last in the list, so default to
    # the final element
    year = st.selectbox("Select Fiscal Year", years, index=len(years) - 1)

with c2:
    # Metric used for colouring the county map. Only the available
    # yearly metrics are allowed here. Note: monthly metrics are not
    # selectable on the map because they span fiscal years.
    metric = st.radio(
        "Map Metric",
        ["litter", "recycled", "dumps"],
        horizontal=True,
    )

with c3:
    # County drop-down for trend charts. The map itself is static and
    # does not respond to clicks due to reliability concerns.
    selected_county = st.selectbox(
        "Select County (for trend)",
        counties,
        index=counties.index("Anderson") if "Anderson" in counties else 0,
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
        st.write(
            """
            This dashboard provides a statewide view of **litter collection**,
            **recycling efforts**, and **dump site activity** across Tennessee.

            The **county map** is the primary overview, helping identify
            spatial patterns for the selected fiscal year.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- CENTER MAP ----------
    with center:
        # Filter the yearly map data by year
        d = df_map[df_map["year"] == year].copy()

        if not d.empty:
            max_val = d[metric].max()
            # Define equal frequency bins for map intensity
            bins = [0, 0.2 * max_val, 0.4 * max_val, 0.6 * max_val, 0.8 * max_val, max_val]
            labels = ["Very Low", "Low", "Medium", "High", "Very High"]
            d["Intensity"] = pd.cut(
                d[metric], bins=bins, labels=labels, include_lowest=True
            )

            # Choose colour palette based on metric
            palette = (
                ["#fff5eb", "#fdd0a2", "#fdae6b", "#e6550d", "#a63603"]
                if metric == "litter"
                else ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"]
                if metric == "recycled"
                else ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"]
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
        st.markdown(f"### {selected_county} Trend (Yearly)")

        # Yearly trend for the selected county using yearly data
        county_trend = (
            df_map[df_map["county"] == selected_county]
            .sort_values("year")
        )

        if not county_trend.empty:
            fig_trend_yearly = px.line(
                county_trend,
                x="year",
                y=["litter", "recycled"],
                markers=True,
                labels={"value": "Tonnage (lbs)", "year": "Fiscal Year"},
            )
            fig_trend_yearly.update_layout(height=360)
            st.plotly_chart(fig_trend_yearly, use_container_width=True)
        else:
            st.info("No trend data available for this county.")

        # Monthly trend (new) for the selected county
        if not df_monthly_county.empty:
            df_cty_month = df_monthly_county[
                (df_monthly_county["county"] == selected_county)
                & (df_monthly_county["year"] == year)
            ]
            if not df_cty_month.empty:
                # Preserve month order for correct chronological plotting
                month_order = [
                    "July",
                    "Aug",
                    "Sept",
                    "Oct",
                    "Nov",
                    "Dec",
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "June",
                ]
                df_cty_month = df_cty_month.copy()
                df_cty_month["month"] = pd.Categorical(
                    df_cty_month["month"], categories=month_order, ordered=True
                )
                df_cty_month = df_cty_month.sort_values("month")
                fig_trend_month = px.line(
                    df_cty_month,
                    x="month",
                    y=["litter", "recycled"],
                    markers=True,
                    labels={"value": "Tonnage (lbs)", "month": "Month"},
                    title="Monthly Litter vs Recycling",
                )
                fig_trend_month.update_layout(height=360)
                st.plotly_chart(fig_trend_month, use_container_width=True)
            else:
                st.info(
                    "No monthly data available for this county and fiscal year."
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- KPI ROW ----------
    # Summarise statewide metrics for the selected year
    row = df_state[df_state["year"] == year]
    if not row.empty:
        row = row.iloc[0]
        k1, k2, k3, k4 = st.columns(4)

        def fmt(x: float) -> str:
            """Format numbers into a human‑friendly representation."""
            if x >= 1_000_000:
                return f"{x / 1_000_000:.1f}M"
            if x >= 1_000:
                return f"{x / 1_000:.1f}K"
            return f"{int(x)}"

        k1.metric("Total Litter (lbs)", fmt(row["litter"]))
        k2.metric("Recycled (lbs)", fmt(row["recycled"]))
        k3.metric("Dump Sites", fmt(row["dumps"]))
        k4.metric("Partners", fmt(row["partners"]))


# =====================================================
# TAB 2 — STATEWIDE TRENDS
# =====================================================
with tab_trends:
    # Compute year‑over‑year growth in recycling. This avoids simply
    # plotting the raw line again and directly answers whether recycling
    # performance is improving year to year. Growth is expressed as a
    # percentage relative to the prior year.
    df_state_sorted = df_state.sort_values("year")
    df_state_sorted["recycle_growth_pct"] = df_state_sorted["recycled"].pct_change()
    # Remove the first year, which has no prior year for comparison
    df_growth = df_state_sorted.dropna(subset=["recycle_growth_pct"]).copy()
    # Convert to percentage and handle infinite values gracefully
    df_growth["growth_percent"] = (df_growth["recycle_growth_pct"] * 100).round(1)
    # Colour based on sign of growth
    df_growth["color"] = df_growth["growth_percent"].apply(
        lambda x: "#2ca02c" if x >= 0 else "#d62728"
    )
    # Bar chart for year‑over‑year recycling growth
    fig_growth = go.Figure(
        data=[
            go.Bar(
                x=df_growth["year"],
                y=df_growth["growth_percent"],
                marker_color=df_growth["color"],
            )
        ]
    )
    fig_growth.update_layout(
        title="Year‑over‑Year Recycling Growth (%)",
        xaxis_title="Fiscal Year",
        yaxis_title="Growth (%)",
        height=520,
        showlegend=False,
    )
    st.plotly_chart(fig_growth, use_container_width=True)


# =====================================================
# TAB 3 — COMPARISONS
# =====================================================
with tab_compare:
    top = (
        df_map[df_map["year"] == year]
        .sort_values(metric, ascending=False)
        .head(10)
    )

    fig_comp = px.bar(
        top,
        x="county",
        y=metric,
        title=f"Top 10 Counties by {metric.title()}",
        labels={metric: f"{metric.title()} (lbs)" if metric in ["litter", "recycled"] else metric.title()},
    )
    st.plotly_chart(fig_comp, use_container_width=True)


# =====================================================
# TAB 4 — SUMMARY
# =====================================================
with tab_summary:
    st.write(
        """
        ## Summary

        This section can be used to provide narrative interpretation of the
        statewide data, highlight notable trends or anomalies and
        communicate recommendations based on the metrics. It is left as
        a placeholder for future expansion and currently does not
        replicate the KPI cards on the overview tab.
        """
    )
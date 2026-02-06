# Tennessee Litter & Recycling Dashboard (Enhanced Version)

This repository contains a production‑ready Streamlit dashboard for
analysing litter collection, recycling efforts and dump site activity
across Tennessee. It builds upon the original dashboard by adding
support for monthly data, improved visualisations and performance
hardening while preserving the original user experience.

## Running Locally

1. **Install dependencies:** Ensure you have Python 3.9+ and run
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the app:** From the root of the repository, execute
   ```bash
   streamlit run app.py
   ```

3. **Interact:** Open the local URL printed in the terminal (usually
   `http://localhost:8501`) in your browser. Select a fiscal year,
   metric and county using the widgets at the top of the page to
   explore the data.

## Deploying to Streamlit Cloud

This project is compatible with Streamlit Cloud. To deploy:

1. Push the contents of `tn_litter_dashboard_final/` to a new GitHub
   repository (public or private).
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud) and create
   a new app linked to that repository. When prompted, set the main
   file to `app.py`.
3. Streamlit Cloud will automatically install the dependencies from
   `requirements.txt` and launch the app. Cold starts should remain
   under 30 seconds thanks to caching.

## Data Overview

The `data/` folder contains both yearly and monthly datasets:

| File | Description |
| --- | --- |
| **yearly_county.csv** | County‑level metrics for each fiscal year. Contains litter (lbs), recycled (lbs), dumps (sites), county road miles and state road miles. |
| **yearly_state.csv** | Statewide rollup of key performance indicators (KPIs) by fiscal year. Includes totals for litter, recycling, dumps, partners and volunteer hours along with a simple trend indicator. |
| **monthly_county.csv** | New file derived from the raw Excel data. Provides county‑level metrics for each month within a fiscal year (currently 2019–2020). Columns include county, year, month, litter, recycled, dumps, county road miles, state road miles, partners and volunteer hours. |
| **monthly_state.csv** | Optional rollup of the monthly data across all counties. Not currently used by the app but available for future analyses. |
| **geojson.json** | GeoJSON definition of Tennessee counties used for drawing the choropleth map. |

The monthly files retain the fiscal year naming convention used in
the existing yearly CSVs. Months are ordered from July to June
to reflect the state’s fiscal year.

## Changes from the Original Version

The enhanced dashboard retains the original layout and features while
introducing several improvements:

1. **Monthly Data Integration:** The dashboard now reads a
   pre‑processed `monthly_county.csv` file to enable month‑level
   analysis. A line chart on the overview tab plots litter and
   recycling volumes by month for the selected county and fiscal year.

2. **Statewide Recycling Trend Fix:** The simple line plot of
   recycling versus year has been replaced with a year‑over‑year
   growth bar chart. This clearly shows whether recycling is
   improving (green bars) or declining (red bars) from one fiscal
   year to the next.

3. **Summary KPIs on Home Page:** Key performance indicators—total
   litter, recycled, dump sites and partners—are displayed as
   stat cards beneath the map on the overview tab. They update
   dynamically based on the selected fiscal year.

4. **Caching and Performance:** Data loading functions are wrapped
   with `@st.cache_data` to ensure the GeoJSON and CSV files are read
   only once per session. This minimises cold start times on
   Streamlit Cloud.

5. **Code Clean‑up:** The code has been reorganised for clarity and
   maintainability. Constants and file paths are defined at the top of
   the file, and helper functions are documented. The summary tab is
   left as a placeholder for narrative commentary.

With these enhancements, the dashboard provides richer insights and
better performance without altering the familiar look and feel of the
original application.
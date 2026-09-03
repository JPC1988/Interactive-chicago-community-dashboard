from pathlib import Path

# Target directory and file path
dataset_dir = Path("chicago_dashboard_dataset")
dataset_dir.mkdir(parents=True, exist_ok=True)
app_file = dataset_dir / "app.py"

streamlit_app = r'''import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
from pathlib import Path

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Chicago Community Development Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* Main title */
    .dashboard-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .dashboard-subtitle {
        font-size: 16px;
        color: #666;
        margin-bottom: 25px;
    }

    /* Section headers */
    .section-title {
        font-size: 23px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 12px;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 7px rgba(0,0,0,0.06);
        text-align: center;
        transition: all 0.25s ease;
        cursor: pointer;
        min-height: 135px;
    }

    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.14);
        border-color: #888;
    }

    .kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #666;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 6px;
        color: #111827;
    }

    .kpi-description {
        font-size: 11px;
        color: #888;
    }

    /* Filter information */
    .filter-box {
        background: #f8f9fa;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #555;
        margin-bottom: 20px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #777;
        font-size: 13px;
        margin-top: 40px;
        padding: 20px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():

    # Multi-path fallbacks to locate geojson dataset
    possible_paths = [
        Path(__file__).parent / "data" / "chicago_community_development.geojson",
        Path("chicago_community_development.geojson"),
        Path("chicago_dashboard_dataset/chicago_community_development.geojson"),
        Path("../chicago_community_development.geojson")
    ]

    data_path = None
    for p in possible_paths:
        if p.exists():
            data_path = p
            break

    if data_path is None:
        raise FileNotFoundError("chicago_community_development.geojson dataset file not found.")

    gdf = gpd.read_file(data_path)

    # Calculate or populate required columns if not precomputed
    if "crime_per_1000_workers" not in gdf.columns:
        if "crime_count" in gdf.columns and "labor_force" in gdf.columns:
            gdf["crime_per_1000_workers"] = (gdf["crime_count"] / gdf["labor_force"].replace(0, np.nan)) * 1000
            gdf["crime_per_1000_workers"] = gdf["crime_per_1000_workers"].fillna(0)
        else:
            gdf["crime_per_1000_workers"] = 0.0

    if "development_priority_score" not in gdf.columns:
        gdf["development_priority_score"] = gdf.get("unemployment_rate", 0) * 0.5

    if "development_priority" not in gdf.columns:
        scores = gdf["development_priority_score"]
        q25, q50, q75 = scores.quantile([0.25, 0.50, 0.75])
        
        def assign_priority(s):
            if s <= q25:
                return "Low Priority"
            elif s <= q50:
                return "Moderate Priority"
            elif s <= q75:
                return "High Priority"
            else:
                return "Very High Priority"

        gdf["development_priority"] = scores.apply(assign_priority)

    return gdf


# ============================================================
# LOAD DATA
# ============================================================

try:
    dashboard_data = load_data()

except Exception as e:

    st.error("Unable to load the Chicago community development dataset.")
    st.exception(e)
    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "GEOID",
    "NAMELSAD",
    "labor_force",
    "unemployed",
    "unemployment_rate",
    "community_resources",
    "crime_per_1000_workers",
    "college_education_rate",
    "development_priority_score",
    "development_priority",
    "geometry"
]

missing_columns = [
    col for col in required_columns
    if col not in dashboard_data.columns
]

if missing_columns:

    st.error("The following required columns are missing:")
    st.write(missing_columns)
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Dashboard Filters")

st.sidebar.markdown("Use the controls below to explore Chicago census tracts.")

st.sidebar.markdown("---")


# Map indicator

indicator_options = {
    "Unemployment Rate": "unemployment_rate",
    "Community Resources": "community_resources",
    "Crime Rate": "crime_per_1000_workers",
    "College Education Rate": "college_education_rate",
    "Development Priority Score": "development_priority_score"
}

selected_indicator = st.sidebar.selectbox(
    "Map Indicator",
    list(indicator_options.keys())
)


# Priority filter

priority_options = [
    "All",
    "Low Priority",
    "Moderate Priority",
    "High Priority",
    "Very High Priority"
]

selected_priority = st.sidebar.selectbox(
    "Development Priority",
    priority_options
)


# ============================================================
# FILTER DATA
# ============================================================

if selected_priority == "All":
    filtered_data = dashboard_data.copy()
else:
    filtered_data = dashboard_data[
        dashboard_data["development_priority"] == selected_priority
    ].copy()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">🏙️ Chicago Community Development Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Interactive analysis of employment, education, community resources, '
    'crime, and development priorities across Chicago census tracts.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# ACTIVE FILTERS
# ============================================================

st.markdown(
    f"""
    <div class="filter-box">
        <b>Active filters:</b>
        Map Indicator = {selected_indicator}
        &nbsp;&nbsp; | &nbsp;&nbsp;
        Development Priority = {selected_priority}
        &nbsp;&nbsp; | &nbsp;&nbsp;
        Census Tracts = {len(filtered_data):,}
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# KPI CALCULATIONS
# ============================================================

num_tracts = len(filtered_data)
avg_unemployment = filtered_data["unemployment_rate"].mean()
total_resources = filtered_data["community_resources"].sum()
avg_crime = filtered_data["crime_per_1000_workers"].mean()
avg_education = filtered_data["college_education_rate"].mean()
avg_priority_score = filtered_data["development_priority_score"].mean()


# ============================================================
# INTERACTIVE KPI CARDS
# ============================================================

st.markdown(
    '<div class="section-title">📊 Key Performance Indicators</div>',
    unsafe_allow_html=True
)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.markdown(
        f"""<div class="kpi-card" title="Number of census tracts included in the current filter.">
            <div class="kpi-label">Census Tracts</div>
            <div class="kpi-value">{num_tracts:,}</div>
            <div class="kpi-description">Areas currently analysed</div>
        </div>""",
        unsafe_allow_html=True
    )

with kpi2:
    st.markdown(
        f"""<div class="kpi-card" title="Average unemployment rate among the selected census tracts.">
            <div class="kpi-label">Avg Unemployment</div>
            <div class="kpi-value">{avg_unemployment:.2f}%</div>
            <div class="kpi-description">Average unemployment rate</div>
        </div>""",
        unsafe_allow_html=True
    )

with kpi3:
    st.markdown(
        f"""<div class="kpi-card" title="Total number of mapped community resources in the selected census tracts.">
            <div class="kpi-label">Community Resources</div>
            <div class="kpi-value">{total_resources:,.0f}</div>
            <div class="kpi-description">Total mapped resources</div>
        </div>""",
        unsafe_allow_html=True
    )

with kpi4:
    st.markdown(
        f"""<div class="kpi-card" title="Average reported crime count per 1,000 workers across the selected census tracts.">
            <div class="kpi-label">Avg Crime Rate</div>
            <div class="kpi-value">{avg_crime:.2f}</div>
            <div class="kpi-description">Crime per 1,000 workers</div>
        </div>""",
        unsafe_allow_html=True
    )

with kpi5:
    st.markdown(
        f"""<div class="kpi-card" title="Average percentage of residents aged 25+ with a bachelor's degree or higher.">
            <div class="kpi-label">Avg Education</div>
            <div class="kpi-value">{avg_education:.2f}%</div>
            <div class="kpi-description">Bachelor's degree or higher</div>
        </div>""",
        unsafe_allow_html=True
    )

with kpi6:
    st.markdown(
        f"""<div class="kpi-card" title="Average development priority score for the selected census tracts.">
            <div class="kpi-label">Avg Priority Score</div>
            <div class="kpi-value">{avg_priority_score:.2f}</div>
            <div class="kpi-description">Development need score</div>
        </div>""",
        unsafe_allow_html=True
    )


# ============================================================
# MAP
# ============================================================

st.markdown(
    '<div class="section-title">🗺️ Geographic Distribution</div>',
    unsafe_allow_html=True
)

map_column = indicator_options[selected_indicator]
map_data = filtered_data.copy()
map_data["map_value"] = map_data[map_column]
map_data["GEOID"] = map_data["GEOID"].astype(str)

geojson = map_data.__geo_interface__

fig_map = px.choropleth_map(
    map_data,
    geojson=geojson,
    locations="GEOID",
    featureidkey="properties.GEOID",
    color="map_value",
    color_continuous_scale="YlOrRd",
    map_style="open-street-map",
    center={"lat": 41.8781, "lon": -87.6298},
    zoom=9.5,
    opacity=0.65,
    hover_name="NAMELSAD",
    hover_data={
        "GEOID": True,
        "unemployment_rate": ":.2f",
        "community_resources": ":,.0f",
        "crime_per_1000_workers": ":.2f",
        "college_education_rate": ":.2f",
        "development_priority_score": ":.2f",
        "development_priority": True,
        "map_value": False
    },
    labels={
        "unemployment_rate": "Unemployment Rate (%)",
        "community_resources": "Community Resources",
        "crime_per_1000_workers": "Crime / 1,000 Workers",
        "college_education_rate": "College Education (%)",
        "development_priority_score": "Priority Score",
        "development_priority": "Development Priority"
    }
)

fig_map.update_layout(
    height=650,
    margin={"l": 0, "r": 0, "t": 10, "b": 0},
    coloraxis_colorbar_title=selected_indicator
)

st.plotly_chart(fig_map, use_container_width=True)


# ============================================================
# EMPLOYMENT AND COMMUNITY RESOURCES
# ============================================================

st.markdown(
    '<div class="section-title">💼 Employment & Community Resources</div>',
    unsafe_allow_html=True
)

chart1, chart2 = st.columns(2)

with chart1:
    top_unemployment = (
        filtered_data
        .nlargest(10, "unemployment_rate")
        .sort_values("unemployment_rate")
    )

    fig_unemployment = px.bar(
        top_unemployment,
        x="unemployment_rate",
        y="NAMELSAD",
        orientation="h",
        title="Top 10 Census Tracts by Unemployment Rate",
        labels={"unemployment_rate": "Unemployment Rate (%)", "NAMELSAD": "Census Tract"},
        text="unemployment_rate",
        color_discrete_sequence=["#D62728"]
    )

    fig_unemployment.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_unemployment.update_layout(height=480, showlegend=False, margin=dict(l=20, r=20, t=60, b=20))

    st.plotly_chart(fig_unemployment, use_container_width=True)

with chart2:
    top_resources = (
        filtered_data
        .nlargest(10, "community_resources")
        .sort_values("community_resources")
    )

    fig_resources = px.bar(
        top_resources,
        x="community_resources",
        y="NAMELSAD",
        orientation="h",
        title="Top 10 Census Tracts by Community Resources",
        labels={"community_resources": "Community Resources", "NAMELSAD": "Census Tract"},
        text="community_resources",
        color_discrete_sequence=["#2CA02C"]
    )

    fig_resources.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_resources.update_layout(height=480, showlegend=False, margin=dict(l=20, r=20, t=60, b=20))

    st.plotly_chart(fig_resources, use_container_width=True)


# ============================================================
# PRIORITY ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">🎯 Development Priority Analysis</div>',
    unsafe_allow_html=True
)

priority1, priority2 = st.columns(2)

with priority1:
    priority_counts = (
        filtered_data["development_priority"]
        .value_counts()
        .reset_index()
    )
    priority_counts.columns = ["development_priority", "count"]

    fig_priority = px.pie(
        priority_counts,
        names="development_priority",
        values="count",
        title="Distribution of Development Priority Areas",
        hole=0.45,
        color_discrete_sequence=["#4C78A8", "#F2CF5B", "#F58518", "#E45756"]
    )

    fig_priority.update_layout(height=480, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_priority, use_container_width=True)

with priority2:
    priority_unemployment = (
        filtered_data
        .groupby("development_priority", as_index=False)["unemployment_rate"]
        .mean()
    )

    priority_order = ["Low Priority", "Moderate Priority", "High Priority", "Very High Priority"]
    priority_unemployment["order"] = priority_unemployment["development_priority"].map(
        {name: i for i, name in enumerate(priority_order)}
    )
    priority_unemployment = priority_unemployment.sort_values("order")

    fig_priority_unemployment = px.bar(
        priority_unemployment,
        x="development_priority",
        y="unemployment_rate",
        title="Average Unemployment Rate by Development Priority",
        labels={
            "development_priority": "Development Priority",
            "unemployment_rate": "Average Unemployment Rate (%)"
        },
        text="unemployment_rate",
        color="development_priority",
        color_discrete_sequence=["#54A24B", "#ECA82C", "#F58518", "#D62728"]
    )

    fig_priority_unemployment.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_priority_unemployment.update_layout(height=480, showlegend=False, margin=dict(l=20, r=20, t=60, b=20))

    st.plotly_chart(fig_priority_unemployment, use_container_width=True)


top_priority = (
    filtered_data
    .nlargest(10, "development_priority_score")
    .sort_values("development_priority_score")
)

fig_top_priority = px.bar(
    top_priority,
    x="development_priority_score",
    y="NAMELSAD",
    orientation="h",
    title="Top 10 Community Development Priority Areas",
    labels={
        "development_priority_score": "Development Priority Score",
        "NAMELSAD": "Census Tract"
    },
    text="development_priority_score",
    color_discrete_sequence=["#9467BD"]
)

fig_top_priority.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig_top_priority.update_layout(height=500, showlegend=False, margin=dict(l=20, r=20, t=60, b=20))

st.plotly_chart(fig_top_priority, use_container_width=True)


# ============================================================
# UNEMPLOYMENT TREND ACROSS CENSUS TRACTS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Unemployment Variation Across Chicago</div>',
    unsafe_allow_html=True
)

line_data = filtered_data.sort_values("unemployment_rate", ascending=False).reset_index(drop=True)
line_data["rank"] = line_data.index + 1

fig_line = px.line(
    line_data,
    x="rank",
    y="unemployment_rate",
    title="Unemployment Rate Across Chicago Census Tracts",
    labels={"rank": "Census Tract Rank", "unemployment_rate": "Unemployment Rate (%)"},
    markers=True
)

fig_line.update_traces(line=dict(color="#17BECF", width=3), marker=dict(color="#17BECF", size=6))
fig_line.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=20))

st.plotly_chart(fig_line, use_container_width=True)


# ============================================================
# RELATIONSHIPS
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Relationships Between Community Conditions</div>',
    unsafe_allow_html=True
)

relationship1, relationship2 = st.columns(2)

with relationship1:
    scatter_data = filtered_data.dropna(subset=["college_education_rate", "crime_per_1000_workers"])

    fig_crime_education = px.scatter(
        scatter_data,
        x="college_education_rate",
        y="crime_per_1000_workers",
        title="Crime Rate vs Educational Attainment",
        labels={
            "college_education_rate": "College Education Rate (%)",
            "crime_per_1000_workers": "Crime per 1,000 Workers"
        },
        hover_name="NAMELSAD",
        size="community_resources",
        color_discrete_sequence=["#FF7F0E"]
    )

    fig_crime_education.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_crime_education, use_container_width=True)

with relationship2:
    education_data = filtered_data.dropna(subset=["unemployment_rate", "college_education_rate"])

    fig_unemployment_education = px.scatter(
        education_data,
        x="college_education_rate",
        y="unemployment_rate",
        title="Unemployment Rate vs College Education Rate",
        labels={
            "college_education_rate": "College Education Rate (%)",
            "unemployment_rate": "Unemployment Rate (%)"
        },
        hover_name="NAMELSAD",
        color_discrete_sequence=["#7F3C8D"]
    )

    fig_unemployment_education.update_layout(height=500, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_unemployment_education, use_container_width=True)


# ============================================================
# DATA TABLE
# ============================================================

st.markdown(
    '<div class="section-title">📋 Underlying Census Tract Data</div>',
    unsafe_allow_html=True
)

display_columns = [
    "GEOID",
    "NAMELSAD",
    "unemployment_rate",
    "community_resources",
    "crime_per_1000_workers",
    "college_education_rate",
    "development_priority_score",
    "development_priority"
]

display_data = filtered_data[display_columns].copy()

display_data = display_data.rename(columns={
    "GEOID": "GEOID",
    "NAMELSAD": "Census Tract",
    "unemployment_rate": "Unemployment Rate (%)",
    "community_resources": "Community Resources",
    "crime_per_1000_workers": "Crime / 1,000 Workers",
    "college_education_rate": "College Education (%)",
    "development_priority_score": "Priority Score",
    "development_priority": "Development Priority"
})

for column in ["Unemployment Rate (%)", "Crime / 1,000 Workers", "College Education (%)", "Priority Score"]:
    display_data[column] = display_data[column].round(2)

st.dataframe(
    display_data,
    use_container_width=True,
    height=450,
    hide_index=True
)


# ============================================================
# CSV DOWNLOAD
# ============================================================

st.markdown(
    '<div class="section-title">⬇️ Download Filtered Data</div>',
    unsafe_allow_html=True
)

csv_data = display_data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download Filtered CSV",
    data=csv_data,
    file_name="chicago_community_development_filtered.csv",
    mime="text/csv"
)


# ============================================================
# DASHBOARD GUIDE
# ============================================================

with st.expander("ℹ️ Dashboard Guide"):
    st.markdown("""
    ### How to use this dashboard

    **1. Map Indicator**
    Select an indicator to change the variable displayed on the Chicago census tract map.

    **2. Development Priority**
    Filter the dashboard to focus on Low, Moderate, High, or Very High Priority areas.

    **3. Key Performance Indicators**
    The KPI cards provide a quick summary of the selected census tracts. Hover over a card to see what each indicator represents.

    **4. Charts**
    The visualisations examine:
    - Unemployment differences across census tracts
    - Distribution of community resources
    - Development priority levels
    - Average unemployment by priority
    - Crime and education relationships
    - Unemployment and education relationships

    **5. Development Priority**
    Higher development priority scores identify census tracts with greater combinations of community challenges.

    **6. Data Table**
    The table provides the underlying census tract-level indicators used in the analysis.

    **7. Download**
    Download the currently filtered dataset as a CSV file.
    """)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        Chicago Community Development Dashboard |
        Census Tract Analysis |
        Community Development Planning
    </div>
    """,
    unsafe_allow_html=True
)
'''

# Write to target files
app_file.write_text(streamlit_app, encoding="utf-8")
Path("app.py").write_text(streamlit_app, encoding="utf-8")


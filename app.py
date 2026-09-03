
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np

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

    .main {
        background-color: #f8f9fa;
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 5px;
    }

    .dashboard-subtitle {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 650;
        color: #1f2937;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    .guide-box {
        background-color: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    data_path = (
        Path(__file__).parent
        / "data"
        / "chicago_community_development.geojson"
    )

    data = gpd.read_file(data_path)

    data["GEOID"] = data["GEOID"].astype(str)

    return data


try:
    dashboard_data = load_data()

except Exception as e:

    st.error("Unable to load dashboard data.")

    st.exception(e)

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "GEOID",
    "tract_name",
    "labor_force",
    "unemployed",
    "unemployment_rate",
    "employment_rate",
    "community_resources",
    "resources_per_1000_workers",
    "crime_count",
    "crime_per_1000_workers",
    "population_25_plus",
    "bachelors_or_higher",
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

    st.error(
        f"Missing required columns: {missing_columns}"
    )

    st.stop()


# ============================================================
# INDICATOR CONFIGURATION
# ============================================================

indicator_options = {
    "Unemployment Rate": "unemployment_rate",
    "Community Resources": "community_resources",
    "Crime Rate": "crime_per_1000_workers",
    "College Education Rate": "college_education_rate",
    "Development Priority Score": "development_priority_score"
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Dashboard Filters")

st.sidebar.markdown(
    "Use the filters below to explore community development "
    "conditions across Chicago census tracts."
)

indicator = st.sidebar.selectbox(
    "Map Indicator",
    list(indicator_options.keys())
)

priority_options = [
    "All",
    "Low Priority",
    "Moderate Priority",
    "High Priority",
    "Very High Priority"
]

priority = st.sidebar.selectbox(
    "Development Priority",
    priority_options
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_data = dashboard_data.copy()

if priority != "All":

    filtered_data = filtered_data[
        filtered_data["development_priority"] == priority
    ].copy()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    '🏙️ Chicago Community Development Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Interactive analysis of unemployment, education, community '
    'resources, crime, and development priorities across '
    'Chicago census tracts.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD GUIDE
# ============================================================

st.markdown(
    """
    <div class="guide-box">

    <b>📌 Dashboard Guide</b><br><br>

    This dashboard identifies areas of Chicago that may require
    greater attention for community development planning.

    <ul>
        <li><b>Employment:</b> Explore unemployment and employment conditions.</li>
        <li><b>Education:</b> Examine college educational attainment.</li>
        <li><b>Resources:</b> Assess the distribution of community resources.</li>
        <li><b>Crime:</b> Compare reported crime across census tracts.</li>
        <li><b>Priority:</b> Identify areas facing multiple development challenges.</li>
        <li><b>Relationships:</b> Explore connections between unemployment,
        education, crime, and resources.</li>
    </ul>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# ACTIVE FILTER
# ============================================================

st.info(
    f"**Active filters:** Development Priority = **{priority}** | "
    f"Map Indicator = **{indicator}** | "
    f"Census Tracts = **{len(filtered_data):,}**"
)


# ============================================================
# KPI CARDS
# ============================================================

avg_unemployment = filtered_data["unemployment_rate"].mean()

total_resources = filtered_data["community_resources"].sum()

avg_crime = filtered_data["crime_per_1000_workers"].mean()

avg_education = filtered_data["college_education_rate"].mean()

avg_priority = filtered_data["development_priority_score"].mean()


kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.metric(
        "Census Tracts",
        f"{len(filtered_data):,}"
    )

with kpi2:
    st.metric(
        "Avg Unemployment",
        f"{avg_unemployment:.2f}%"
    )

with kpi3:
    st.metric(
        "Community Resources",
        f"{total_resources:,.0f}"
    )

with kpi4:
    st.metric(
        "Avg Crime Rate",
        f"{avg_crime:.2f}"
    )

with kpi5:
    st.metric(
        "Avg Education",
        f"{avg_education:.2f}%"
    )

with kpi6:
    st.metric(
        "Avg Priority Score",
        f"{avg_priority:.2f}"
    )


# ============================================================
# MAP
# ============================================================

st.markdown(
    '<div class="section-title">🗺️ Chicago Community Development Map</div>',
    unsafe_allow_html=True
)

map_data = filtered_data.copy()

map_data["map_value"] = pd.to_numeric(
    map_data[indicator_options[indicator]],
    errors="coerce"
)

map_data = map_data.replace(
    [np.inf, -np.inf],
    np.nan
)

map_data = map_data.dropna(
    subset=["map_value"]
)

geojson = map_data.__geo_interface__


fig_map = px.choropleth_map(
    map_data,
    geojson=geojson,
    locations="GEOID",
    featureidkey="properties.GEOID",
    color="map_value",
    color_continuous_scale="YlOrRd",
    map_style="open-street-map",
    center={
        "lat": 41.8781,
        "lon": -87.6298
    },
    zoom=9.5,
    opacity=0.65,
    hover_name="tract_name",
    hover_data={
        "GEOID": True,
        "unemployment_rate": ":.2f",
        "community_resources": True,
        "crime_per_1000_workers": ":.2f",
        "college_education_rate": ":.2f",
        "development_priority_score": ":.2f",
        "development_priority": True,
        "map_value": False
    },
    labels={
        "unemployment_rate": "Unemployment Rate (%)",
        "community_resources": "Community Resources",
        "crime_per_1000_workers": "Crime per 1,000 Workers",
        "college_education_rate": "College Education (%)",
        "development_priority_score": "Priority Score",
        "development_priority": "Development Priority"
    }
)

fig_map.update_layout(
    height=650,
    margin=dict(l=0, r=0, t=10, b=0),
    coloraxis_colorbar_title=indicator
)

st.plotly_chart(
    fig_map,
    use_container_width=True
)


# ============================================================
# EMPLOYMENT AND RESOURCES
# ============================================================

st.markdown(
    '<div class="section-title">📊 Employment and Resources</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# TOP 10 UNEMPLOYMENT
# ------------------------------------------------------------

with col1:

    unemployment_top = (
        filtered_data[
            [
                "tract_name",
                "unemployment_rate"
            ]
        ]
        .sort_values(
            "unemployment_rate",
            ascending=False
        )
        .head(10)
    )

    unemployment_top = unemployment_top.sort_values(
        "unemployment_rate"
    )

    fig_unemployment = px.bar(
        unemployment_top,
        x="unemployment_rate",
        y="tract_name",
        orientation="h",
        title="Top 10 Census Tracts by Unemployment Rate",
        labels={
            "unemployment_rate": "Unemployment Rate (%)",
            "tract_name": "Census Tract"
        },
        text="unemployment_rate"
    )

    fig_unemployment.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside"
    )

    fig_unemployment.update_layout(
        height=500,
        margin=dict(l=20, r=30, t=60, b=20)
    )

    st.plotly_chart(
        fig_unemployment,
        use_container_width=True
    )


# ------------------------------------------------------------
# TOP 10 COMMUNITY RESOURCES
# ------------------------------------------------------------

with col2:

    resources_top = (
        filtered_data[
            [
                "tract_name",
                "community_resources"
            ]
        ]
        .sort_values(
            "community_resources",
            ascending=False
        )
        .head(10)
    )

    resources_top = resources_top.sort_values(
        "community_resources"
    )

    fig_resources = px.bar(
        resources_top,
        x="community_resources",
        y="tract_name",
        orientation="h",
        title="Top 10 Census Tracts by Community Resources",
        labels={
            "community_resources": "Community Resources",
            "tract_name": "Census Tract"
        },
        text="community_resources"
    )

    fig_resources.update_traces(
        textposition="outside"
    )

    fig_resources.update_layout(
        height=500,
        margin=dict(l=20, r=30, t=60, b=20)
    )

    st.plotly_chart(
        fig_resources,
        use_container_width=True
    )


# ------------------------------------------------------------
# UNEMPLOYMENT LINE CHART
# ------------------------------------------------------------

ranked_unemployment = (
    filtered_data[
        [
            "tract_name",
            "unemployment_rate"
        ]
    ]
    .sort_values(
        "unemployment_rate",
        ascending=False
    )
    .reset_index(drop=True)
)

ranked_unemployment["rank"] = (
    ranked_unemployment.index + 1
)


fig_unemployment_line = px.line(
    ranked_unemployment,
    x="rank",
    y="unemployment_rate",
    markers=True,
    title="Unemployment Rate Across Chicago Census Tracts",
    labels={
        "rank": "Census Tract Rank",
        "unemployment_rate": "Unemployment Rate (%)"
    }
)

fig_unemployment_line.update_layout(
    height=500
)

st.plotly_chart(
    fig_unemployment_line,
    use_container_width=True
)


# ============================================================
# PRIORITY AND DISTRIBUTION ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">🎯 Priority and Distribution Analysis</div>',
    unsafe_allow_html=True
)

col3, col4 = st.columns(2)


# ------------------------------------------------------------
# PRIORITY DONUT
# ------------------------------------------------------------

with col3:

    priority_counts = (
        filtered_data["development_priority"]
        .value_counts()
        .reset_index()
    )

    priority_counts.columns = [
        "development_priority",
        "count"
    ]

    fig_priority = px.pie(
        priority_counts,
        names="development_priority",
        values="count",
        hole=0.35,
        title="Distribution of Development Priority Areas"
    )

    fig_priority.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_priority,
        use_container_width=True
    )


# ------------------------------------------------------------
# TOP 10 PRIORITY AREAS
# ------------------------------------------------------------

with col4:

    priority_top = (
        filtered_data[
            [
                "tract_name",
                "development_priority_score"
            ]
        ]
        .sort_values(
            "development_priority_score",
            ascending=False
        )
        .head(10)
    )

    priority_top = priority_top.sort_values(
        "development_priority_score"
    )

    fig_priority_rank = px.bar(
        priority_top,
        x="development_priority_score",
        y="tract_name",
        orientation="h",
        title="Top 10 Community Development Priority Areas",
        labels={
            "development_priority_score": "Priority Score",
            "tract_name": "Census Tract"
        },
        text="development_priority_score"
    )

    fig_priority_rank.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_priority_rank.update_layout(
        height=500,
        margin=dict(l=20, r=30, t=60, b=20)
    )

    st.plotly_chart(
        fig_priority_rank,
        use_container_width=True
    )


# ============================================================
# COMMUNITY DEVELOPMENT RELATIONSHIPS
# ============================================================

st.markdown(
    '<div class="section-title">🔗 Community Development Relationships</div>',
    unsafe_allow_html=True
)


col5, col6 = st.columns(2)


# ------------------------------------------------------------
# CRIME VS EDUCATION
# ------------------------------------------------------------

with col5:

    crime_education = filtered_data[
        [
            "tract_name",
            "crime_per_1000_workers",
            "college_education_rate",
            "community_resources"
        ]
    ].replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    fig_crime_education = px.scatter(
        crime_education,
        x="college_education_rate",
        y="crime_per_1000_workers",
        size="community_resources",
        hover_name="tract_name",
        title="Crime Rate vs Educational Attainment",
        labels={
            "college_education_rate":
                "College Education Rate (%)",
            "crime_per_1000_workers":
                "Crime per 1,000 Workers",
            "community_resources":
                "Community Resources"
        }
    )

    fig_crime_education.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_crime_education,
        use_container_width=True
    )


# ------------------------------------------------------------
# UNEMPLOYMENT VS EDUCATION
# ------------------------------------------------------------

with col6:

    unemployment_education = filtered_data[
        [
            "tract_name",
            "unemployment_rate",
            "college_education_rate",
            "community_resources"
        ]
    ].replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    fig_unemployment_education = px.scatter(
        unemployment_education,
        x="college_education_rate",
        y="unemployment_rate",
        size="community_resources",
        hover_name="tract_name",
        title="Unemployment Rate vs College Education Rate",
        labels={
            "college_education_rate":
                "College Education Rate (%)",
            "unemployment_rate":
                "Unemployment Rate (%)",
            "community_resources":
                "Community Resources"
        }
    )

    fig_unemployment_education.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_unemployment_education,
        use_container_width=True
    )


# ------------------------------------------------------------
# UNEMPLOYMENT VS COMMUNITY RESOURCES
# ------------------------------------------------------------

unemployment_resources = filtered_data[
    [
        "tract_name",
        "unemployment_rate",
        "community_resources"
    ]
].replace(
    [np.inf, -np.inf],
    np.nan
).dropna()


fig_unemployment_resources = px.scatter(
    unemployment_resources,
    x="community_resources",
    y="unemployment_rate",
    hover_name="tract_name",
    title="Unemployment Rate vs Community Resources",
    labels={
        "community_resources":
            "Community Resources",
        "unemployment_rate":
            "Unemployment Rate (%)"
    }
)

fig_unemployment_resources.update_layout(
    height=500
)

st.plotly_chart(
    fig_unemployment_resources,
    use_container_width=True
)


# ============================================================
# UNDERLYING DATA
# ============================================================

st.markdown(
    '<div class="section-title">📋 Underlying Census Tract Data</div>',
    unsafe_allow_html=True
)

display_columns = [
    "GEOID",
    "tract_name",
    "unemployment_rate",
    "employment_rate",
    "community_resources",
    "resources_per_1000_workers",
    "crime_count",
    "crime_per_1000_workers",
    "college_education_rate",
    "development_priority_score",
    "development_priority"
]

display_data = filtered_data[
    display_columns
].copy()


# ------------------------------------------------------------
# FORMAT NUMERICAL VALUES
# ------------------------------------------------------------

for col in [
    "unemployment_rate",
    "employment_rate",
    "resources_per_1000_workers",
    "crime_per_1000_workers",
    "college_education_rate",
    "development_priority_score"
]:

    display_data[col] = display_data[col].round(2)


st.dataframe(
    display_data,
    use_container_width=True,
    height=500
)


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

st.markdown(
    '<div class="section-title">📥 Export Filtered Data</div>',
    unsafe_allow_html=True
)

download_data = filtered_data.drop(
    columns=["geometry"],
    errors="ignore"
).copy()

csv_data = download_data.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Filtered Census Tract Data (CSV)",
    data=csv_data,
    file_name="chicago_community_development_filtered.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Chicago Community Development Dashboard | "
    "Census-tract level analysis of employment, education, "
    "community resources, crime, and development priorities."
)


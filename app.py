import streamlit as st
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
    initial_sidebar_state="collapsed"
)


# ============================================================
# RESPONSIVE CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       GENERAL LAYOUT
    -------------------------------------------------------- */

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 1600px;
    }

    /* --------------------------------------------------------
       DASHBOARD TITLE
    -------------------------------------------------------- */

    .dashboard-title {
        font-size: 2.6rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }

    .dashboard-subtitle {
        text-align: center;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        opacity: 0.75;
    }

    /* --------------------------------------------------------
       SECTION TITLES
    -------------------------------------------------------- */

    .section-title {
        font-size: 1.45rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    /* --------------------------------------------------------
       KPI CARDS
    -------------------------------------------------------- */

    .kpi-card {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        text-align: center;
        min-height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 0.8rem;
        background: rgba(128, 128, 128, 0.04);
    }

    .kpi-label {
        font-size: 0.85rem;
        font-weight: 600;
        opacity: 0.75;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.1;
    }

    /* --------------------------------------------------------
       INFO BOX
    -------------------------------------------------------- */

    .info-box {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* --------------------------------------------------------
       FOOTER
    -------------------------------------------------------- */

    .footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128, 128, 128, 0.25);
        font-size: 0.85rem;
        opacity: 0.7;
    }

    /* --------------------------------------------------------
       TABLET
    -------------------------------------------------------- */

    @media (max-width: 992px) {

        .block-container {
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }

        .dashboard-title {
            font-size: 2.1rem;
        }

        .dashboard-subtitle {
            font-size: 0.95rem;
        }

        .section-title {
            font-size: 1.3rem;
        }

        .kpi-card {
            min-height: 110px;
        }

        .kpi-value {
            font-size: 1.45rem;
        }
    }

    /* --------------------------------------------------------
       MOBILE
    -------------------------------------------------------- */

    @media (max-width: 768px) {

        .block-container {
            padding-top: 1rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        .dashboard-title {
            font-size: 1.65rem;
        }

        .dashboard-subtitle {
            font-size: 0.85rem;
            line-height: 1.4;
        }

        .section-title {
            font-size: 1.15rem;
        }

        .kpi-card {
            min-height: 95px;
            padding: 0.7rem;
            border-radius: 10px;
        }

        .kpi-label {
            font-size: 0.72rem;
        }

        .kpi-value {
            font-size: 1.2rem;
        }

        .info-box {
            font-size: 0.85rem;
        }

    }

    /* --------------------------------------------------------
       SMALL MOBILE
    -------------------------------------------------------- */

    @media (max-width: 480px) {

        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        .dashboard-title {
            font-size: 1.4rem;
        }

        .dashboard-subtitle {
            font-size: 0.78rem;
        }

        .kpi-card {
            min-height: 85px;
            padding: 0.5rem;
        }

        .kpi-label {
            font-size: 0.65rem;
        }

        .kpi-value {
            font-size: 1rem;
        }

        .section-title {
            font-size: 1rem;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():

    possible_paths = [
        Path(__file__).parent / "data" / "chicago_community_development.geojson",
        Path(__file__).parent / "chicago_community_development.geojson",
        Path("chicago_community_development.geojson"),
        Path("chicago_dashboard_dataset") / "chicago_community_development.geojson",
        Path("../chicago_community_development.geojson")
    ]

    data_path = None

    for path in possible_paths:
        if path.exists():
            data_path = path
            break

    if data_path is None:
        raise FileNotFoundError(
            "The file 'chicago_community_development.geojson' "
            "could not be found."
        )

    gdf = gpd.read_file(data_path)

    # --------------------------------------------------------
    # Ensure GEOID is treated as text
    # --------------------------------------------------------

    if "GEOID" in gdf.columns:
        gdf["GEOID"] = gdf["GEOID"].astype(str)

    # --------------------------------------------------------
    # Crime rate
    # --------------------------------------------------------

    if "crime_per_1000_workers" not in gdf.columns:

        if (
            "crime_count" in gdf.columns
            and "labor_force" in gdf.columns
        ):

            labor_force = gdf["labor_force"].replace(0, np.nan)

            gdf["crime_per_1000_workers"] = (
                gdf["crime_count"] / labor_force
            ) * 1000

            gdf["crime_per_1000_workers"] = (
                gdf["crime_per_1000_workers"]
                .replace([np.inf, -np.inf], np.nan)
                .fillna(0)
            )

        else:
            gdf["crime_per_1000_workers"] = 0.0

    # --------------------------------------------------------
    # Development priority score
    # --------------------------------------------------------

    if "development_priority_score" not in gdf.columns:

        unemployment = pd.to_numeric(
            gdf.get("unemployment_rate", 0),
            errors="coerce"
        ).fillna(0)

        education = pd.to_numeric(
            gdf.get("college_education_rate", 0),
            errors="coerce"
        ).fillna(0)

        resources = pd.to_numeric(
            gdf.get("community_resources", 0),
            errors="coerce"
        ).fillna(0)

        crime = pd.to_numeric(
            gdf.get("crime_per_1000_workers", 0),
            errors="coerce"
        ).fillna(0)

        # Normalize indicators to 0–100 where possible.
        unemployment_score = unemployment.clip(0, 100)

        education_score = (
            100 - education.clip(0, 100)
        )

        resource_score = (
            100
            - (
                resources / resources.max() * 100
                if resources.max() > 0
                else resources
            )
        )

        crime_score = (
            crime / crime.max() * 100
            if crime.max() > 0
            else crime
        )

        # Higher score = greater development need.
        gdf["development_priority_score"] = (
            unemployment_score * 0.40
            + education_score * 0.25
            + resource_score * 0.20
            + crime_score * 0.15
        )

    # --------------------------------------------------------
    # Development priority category
    # --------------------------------------------------------

    if "development_priority" not in gdf.columns:

        scores = pd.to_numeric(
            gdf["development_priority_score"],
            errors="coerce"
        ).fillna(0)

        q25, q50, q75 = scores.quantile(
            [0.25, 0.50, 0.75]
        )

        def assign_priority(score):

            if score <= q25:
                return "Low Priority"

            elif score <= q50:
                return "Moderate Priority"

            elif score <= q75:
                return "High Priority"

            else:
                return "Very High Priority"

        gdf["development_priority"] = (
            scores.apply(assign_priority)
        )

    # --------------------------------------------------------
    # Clean numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "labor_force",
        "unemployed",
        "unemployment_rate",
        "community_resources",
        "crime_per_1000_workers",
        "college_education_rate",
        "development_priority_score"
    ]

    for column in numeric_columns:

        if column in gdf.columns:

            gdf[column] = pd.to_numeric(
                gdf[column],
                errors="coerce"
            ).fillna(0)

    return gdf


# ============================================================
# LOAD DATA
# ============================================================

try:

    dashboard_data = load_data()

except Exception as e:

    st.error(
        "Unable to load the Chicago community development dataset."
    )

    st.exception(e)

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "GEOID",
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
    column
    for column in required_columns
    if column not in dashboard_data.columns
]

if missing_columns:

    st.error(
        "The dataset is missing the following required columns:"
    )

    st.write(missing_columns)

    st.stop()


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    '🏙️ Chicago Community Development Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Geospatial analysis of employment, education, crime, '
    'and community resources across Chicago census tracts'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛️ Dashboard Filters")

st.sidebar.markdown(
    "Use the filters below to explore different development "
    "conditions across Chicago."
)


# ------------------------------------------------------------
# Map indicator
# ------------------------------------------------------------

indicator_options = {
    "Unemployment Rate": "unemployment_rate",
    "Community Resources": "community_resources",
    "Crime Rate": "crime_per_1000_workers",
    "College Education Rate": "college_education_rate",
    "Development Priority Score": "development_priority_score"
}

selected_indicator_label = st.sidebar.selectbox(
    "Map Indicator",
    list(indicator_options.keys())
)

selected_indicator = indicator_options[
    selected_indicator_label
]


# ------------------------------------------------------------
# Development priority filter
# ------------------------------------------------------------

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

filtered_data = dashboard_data.copy()

if selected_priority != "All":

    filtered_data = filtered_data[
        filtered_data["development_priority"]
        == selected_priority
    ].copy()


# ============================================================
# KPI SECTION
# ============================================================

st.markdown(
    '<div class="section-title">📊 Key Performance Indicators</div>',
    unsafe_allow_html=True
)


total_tracts = len(filtered_data)

average_unemployment = (
    filtered_data["unemployment_rate"].mean()
    if total_tracts > 0
    else 0
)

total_resources = (
    filtered_data["community_resources"].sum()
    if total_tracts > 0
    else 0
)

average_crime_rate = (
    filtered_data["crime_per_1000_workers"].mean()
    if total_tracts > 0
    else 0
)

average_education = (
    filtered_data["college_education_rate"].mean()
    if total_tracts > 0
    else 0
)

average_priority = (
    filtered_data["development_priority_score"].mean()
    if total_tracts > 0
    else 0
)


# ------------------------------------------------------------
# KPI columns
# ------------------------------------------------------------

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">CENSUS TRACTS</div>
            <div class="kpi-value">{total_tracts:,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">AVG. UNEMPLOYMENT</div>
            <div class="kpi-value">{average_unemployment:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">COMMUNITY RESOURCES</div>
            <div class="kpi-value">{total_resources:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


kpi4, kpi5, kpi6 = st.columns(3)

with kpi4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">AVG. CRIME RATE</div>
            <div class="kpi-value">{average_crime_rate:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi5:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">AVG. COLLEGE EDUCATION</div>
            <div class="kpi-value">{average_education:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with kpi6:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">AVG. PRIORITY SCORE</div>
            <div class="kpi-value">{average_priority:.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MAP SECTION
# ============================================================

st.markdown(
    '<div class="section-title">🗺️ Chicago Community Development Map</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="info-box">
        <b>Current map indicator:</b> {selected_indicator_label}
        <br>
        Darker areas represent higher values of the selected indicator.
        Use the sidebar to change the indicator or development priority.
    </div>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# Prepare map data
# ------------------------------------------------------------

map_data = filtered_data.copy()

# Create a readable display value.
map_data["Map Value"] = map_data[selected_indicator].round(2)

# Remove empty geometries.
map_data = map_data[
    map_data.geometry.notna()
].copy()


# ------------------------------------------------------------
# Plotly choropleth map
# ------------------------------------------------------------

if len(map_data) > 0:

    fig_map = px.choropleth_map(
        map_data,
        geojson=map_data.__geo_interface__,
        locations="GEOID",
        featureidkey="properties.GEOID",
        color=selected_indicator,
        color_continuous_scale="YlOrRd",
        map_style="open-street-map",
        center={
            "lat": 41.8781,
            "lon": -87.6298
        },
        zoom=9.5,
        opacity=0.65,
        hover_data={
            "GEOID": True,
            "unemployment_rate": ":.2f",
            "community_resources": True,
            "crime_per_1000_workers": ":.2f",
            "college_education_rate": ":.2f",
            "development_priority": True,
            selected_indicator: False
        }
    )

    fig_map.update_layout(
        autosize=True,
        height=650,
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        },
        coloraxis_colorbar={
            "title": selected_indicator_label
        }
    )

    st.plotly_chart(
        fig_map,
        use_container_width=True
    )

else:

    st.warning(
        "No census tracts match the selected filter."
    )


# ============================================================
# CHART SECTION
# ============================================================

st.markdown(
    '<div class="section-title">📈 Development Analysis</div>',
    unsafe_allow_html=True
)


# ============================================================
# CHART 1 — TOP 10 UNEMPLOYMENT
# ============================================================

chart_data = filtered_data.nlargest(
    10,
    "unemployment_rate"
).copy()

chart_data = chart_data.sort_values(
    "unemployment_rate"
)

fig1 = px.bar(
    chart_data,
    x="unemployment_rate",
    y="GEOID",
    orientation="h",
    title="Top 10 Census Tracts by Unemployment Rate",
    labels={
        "unemployment_rate": "Unemployment Rate (%)",
        "GEOID": "Census Tract"
    },
    text="unemployment_rate"
)

fig1.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig1.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# CHART 2 — COMMUNITY RESOURCES
# ============================================================

resource_data = filtered_data.nlargest(
    10,
    "community_resources"
).copy()

resource_data = resource_data.sort_values(
    "community_resources"
)

fig2 = px.bar(
    resource_data,
    x="community_resources",
    y="GEOID",
    orientation="h",
    title="Top 10 Census Tracts by Community Resources",
    labels={
        "community_resources": "Community Resources",
        "GEOID": "Census Tract"
    },
    text="community_resources"
)

fig2.update_traces(
    texttemplate="%{text:.0f}",
    textposition="outside"
)

fig2.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ------------------------------------------------------------
# Display charts
# ------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

with col2:

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# ============================================================
# CHART 3 — PRIORITY DISTRIBUTION
# ============================================================

priority_counts = (
    filtered_data["development_priority"]
    .value_counts()
    .reindex(
        [
            "Low Priority",
            "Moderate Priority",
            "High Priority",
            "Very High Priority"
        ],
        fill_value=0
    )
    .reset_index()
)

priority_counts.columns = [
    "Development Priority",
    "Number of Tracts"
]

fig3 = px.pie(
    priority_counts,
    names="Development Priority",
    values="Number of Tracts",
    title="Development Priority Distribution",
    hole=0.35
)

fig3.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# CHART 4 — AVG UNEMPLOYMENT BY PRIORITY
# ============================================================

priority_unemployment = (
    filtered_data
    .groupby("development_priority")[
        "unemployment_rate"
    ]
    .mean()
    .reindex(
        [
            "Low Priority",
            "Moderate Priority",
            "High Priority",
            "Very High Priority"
        ]
    )
    .reset_index()
)

fig4 = px.bar(
    priority_unemployment,
    x="development_priority",
    y="unemployment_rate",
    title="Average Unemployment Rate by Development Priority",
    labels={
        "development_priority": "Development Priority",
        "unemployment_rate": "Average Unemployment Rate (%)"
    },
    text="unemployment_rate"
)

fig4.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig4.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


col3, col4 = st.columns(2)

with col3:

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

with col4:

    st.plotly_chart(
        fig4,
        use_container_width=True
    )


# ============================================================
# CHART 5 — TOP PRIORITY AREAS
# ============================================================

priority_data = filtered_data.nlargest(
    10,
    "development_priority_score"
).copy()

priority_data = priority_data.sort_values(
    "development_priority_score"
)

fig5 = px.bar(
    priority_data,
    x="development_priority_score",
    y="GEOID",
    orientation="h",
    title="Top 10 Development Priority Areas",
    labels={
        "development_priority_score": "Priority Score",
        "GEOID": "Census Tract"
    },
    text="development_priority_score"
)

fig5.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig5.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# CHART 6 — UNEMPLOYMENT DISTRIBUTION
# ============================================================

fig6 = px.histogram(
    filtered_data,
    x="unemployment_rate",
    nbins=25,
    title="Unemployment Rate Distribution Across Census Tracts",
    labels={
        "unemployment_rate": "Unemployment Rate (%)",
        "count": "Number of Tracts"
    }
)

fig6.update_layout(
    autosize=True,
    height=450,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


col5, col6 = st.columns(2)

with col5:

    st.plotly_chart(
        fig5,
        use_container_width=True
    )

with col6:

    st.plotly_chart(
        fig6,
        use_container_width=True
    )


# ============================================================
# CHART 7 — CRIME VS EDUCATION
# ============================================================

fig7 = px.scatter(
    filtered_data,
    x="college_education_rate",
    y="crime_per_1000_workers",
    size="community_resources",
    hover_name="GEOID",
    hover_data={
        "college_education_rate": ":.2f",
        "crime_per_1000_workers": ":.2f",
        "community_resources": True,
        "unemployment_rate": ":.2f",
        "development_priority": True
    },
    title="Crime Rate vs. Educational Attainment",
    labels={
        "college_education_rate": "College Education Rate (%)",
        "crime_per_1000_workers": "Crime Rate per 1,000 Workers",
        "community_resources": "Community Resources"
    }
)

fig7.update_layout(
    autosize=True,
    height=500,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


# ============================================================
# CHART 8 — UNEMPLOYMENT VS EDUCATION
# ============================================================

fig8 = px.scatter(
    filtered_data,
    x="college_education_rate",
    y="unemployment_rate",
    size="community_resources",
    hover_name="GEOID",
    hover_data={
        "college_education_rate": ":.2f",
        "unemployment_rate": ":.2f",
        "community_resources": True,
        "crime_per_1000_workers": ":.2f",
        "development_priority": True
    },
    title="Unemployment Rate vs. College Education Rate",
    labels={
        "college_education_rate": "College Education Rate (%)",
        "unemployment_rate": "Unemployment Rate (%)",
        "community_resources": "Community Resources"
    }
)

fig8.update_layout(
    autosize=True,
    height=500,
    margin=dict(
        l=20,
        r=20,
        t=60,
        b=20
    )
)


col7, col8 = st.columns(2)

with col7:

    st.plotly_chart(
        fig7,
        use_container_width=True
    )

with col8:

    st.plotly_chart(
        fig8,
        use_container_width=True
    )


# ============================================================
# DATA TABLE
# ============================================================

st.markdown(
    '<div class="section-title">📋 Census Tract Data</div>',
    unsafe_allow_html=True
)


display_columns = [
    "GEOID",
    "labor_force",
    "unemployed",
    "unemployment_rate",
    "community_resources",
    "crime_per_1000_workers",
    "college_education_rate",
    "development_priority_score",
    "development_priority"
]

display_data = filtered_data[
    display_columns
].copy()


# ------------------------------------------------------------
# Rename columns for presentation
# ------------------------------------------------------------

display_data = display_data.rename(
    columns={
        "GEOID": "Census Tract",
        "labor_force": "Labor Force",
        "unemployed": "Unemployed",
        "unemployment_rate": "Unemployment Rate (%)",
        "community_resources": "Community Resources",
        "crime_per_1000_workers": "Crime per 1,000 Workers",
        "college_education_rate": "College Education Rate (%)",
        "development_priority_score": "Priority Score",
        "development_priority": "Development Priority"
    }
)


# ------------------------------------------------------------
# Formatting
# ------------------------------------------------------------

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Census Tract": st.column_config.TextColumn(
            "Census Tract"
        ),
        "Labor Force": st.column_config.NumberColumn(
            "Labor Force",
            format="%d"
        ),
        "Unemployed": st.column_config.NumberColumn(
            "Unemployed",
            format="%d"
        ),
        "Unemployment Rate (%)": st.column_config.NumberColumn(
            "Unemployment Rate (%)",
            format="%.2f%%"
        ),
        "Community Resources": st.column_config.NumberColumn(
            "Community Resources",
            format="%d"
        ),
        "Crime per 1,000 Workers": st.column_config.NumberColumn(
            "Crime per 1,000 Workers",
            format="%.2f"
        ),
        "College Education Rate (%)": st.column_config.NumberColumn(
            "College Education Rate (%)",
            format="%.2f%%"
        ),
        "Priority Score": st.column_config.NumberColumn(
            "Priority Score",
            format="%.2f"
        )
    }
)


# ============================================================
# CSV DOWNLOAD
# ============================================================

st.markdown(
    '<div class="section-title">📥 Export Data</div>',
    unsafe_allow_html=True
)


csv_data = display_data.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="📥 Download Filtered CSV",
    data=csv_data,
    file_name="chicago_community_development_filtered.csv",
    mime="text/csv",
    use_container_width=True,
    key="download_filtered_data"
)


# ============================================================
# DATA SOURCE INFORMATION
# ============================================================

st.markdown(
    """
    <div class="info-box">

    <b>Data Sources</b><br><br>

    • U.S. Census Bureau — 2024 American Community Survey (ACS 5-Year)<br>
    • U.S. Census Bureau — TIGER/Line Census Tract Boundaries<br>
    • Chicago Police Department — Chicago Data Portal Crime Records<br>
    • OpenStreetMap — Community Resource Locations<br><br>

    <b>Key Indicators</b><br><br>

    • Unemployment Rate — unemployed population as a percentage of the civilian labor force<br>
    • College Education Rate — percentage of adults aged 25+ with a bachelor's degree or higher<br>
    • Community Resources — mapped schools, hospitals, clinics, libraries, community centres and places of worship<br>
    • Crime Rate — reported crime incidents per 1,000 workers<br>
    • Development Priority Score — composite indicator identifying areas with greater potential development needs

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

    <b>Chicago Community Development Dashboard</b><br>
    Geospatial Data Analysis and Community Development Planning<br>
    Data Science Project — Chicago, Illinois

    </div>
    """,
    unsafe_allow_html=True
)

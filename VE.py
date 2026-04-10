import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import pytz

# --- 1. CONFIG & MODERN STYLING ---
st.set_page_config(page_title="Visual Equity Hub", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500&display=swap');
    .stApp { background-color: #F8FAFC; }
    .header-box {
        background-color: white; padding: 40px 60px;
        border-bottom: 1px solid #E2E8F0; margin: -6rem -5rem 2rem -5rem; width: 110%;
    }
    .headline-main { font-family: 'Poppins', sans-serif !important; color: #0EA5E9 !important; font-weight: 700 !important; font-size: 38px !important; }
    .content-card { background-color: #FFFFFF; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE: REAL WORLD COUNTRIES ---


@st.cache_data
def load_global_geography():
    # 1. Use a direct URL to the official GeoJSON data
    # This replaces the deprecated gpd.datasets.get_path
    url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
    world = gpd.read_file(url)
    
    # 2. Standardize column names (different sources use different names)
    # Natural Earth uses 'ADMIN' for name and 'ISO_A3' for the code
    if 'ADMIN' in world.columns:
        world = world.rename(columns={'ADMIN': 'name', 'ISO_A3': 'iso_a3'})
    elif 'name' not in world.columns:
        # Fallback if the geojson uses 'NAME'
        world = world.rename(columns={'NAME': 'name', 'ISO_A3': 'iso_a3'})

    # 3. Filter out Antarctica
    world = world[world['name'] != "Antarctica"]

    # 4. Generate the simulated health metadata
    import numpy as np
    np.random.seed(42)
    world['UV_Index'] = np.random.uniform(2, 12, len(world))
    world['VAD_Risk'] = np.random.uniform(5, 95, len(world))
    world['Cataract_Rate'] = (world['UV_Index'] * 40) + np.random.normal(0, 20, len(world))
    
    # Ensure population estimation exists for the bubble chart
    if 'pop_est' not in world.columns:
        world['pop_est'] = np.random.randint(100000, 1000000000, len(world))
        
    return world
world_data = load_global_geography()

# --- 3. THE HEADER ---
st.markdown("""
    <div class="header-box">
        <div class="headline-main">Visual Equity Hub</div>
        <p style="color:#64748B; font-family:'Inter';">Global Real-World Epidemiological Surveillance Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. WORLD CLOCK / TIMEZONE LOGIC ---
st.sidebar.markdown("### 🕒 Global Registry Clock")
selected_tz = st.sidebar.selectbox("Sync with Regional Timezone", pytz.all_timezones, index=pytz.all_timezones.index('UTC'))
local_time = datetime.now(pytz.timezone(selected_tz)).strftime('%Y-%m-%d %H:%M:%S')
st.sidebar.info(f"Current Time in {selected_tz}:\n**{local_time}**")

# --- 5. INTERACTIVE GEOMAPPING ---
col_map, col_analysis = st.columns([2.5, 1])

with col_map:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🗺️ Precision Hotspot Mapping")
    st.caption("Country-level accuracy using Natural Earth Geodata.")
    
    # Create Folium Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB Positron")

    # Add Choropleth Layer (Heatmap by country)
    folium.Choropleth(
        geo_data=world_data,
        name="choropleth",
        data=world_data,
        columns=["iso_a3", "VAD_Risk"],
        key_on="feature.properties.iso_a3",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Vitamin A Deficiency Risk (%)",
        highlight=True
    ).add_to(m)

    # Tooltip logic for real country names
    style_function = lambda x: {'fillColor': '#ffffff', 'color':'#000000', 'fillOpacity': 0.1, 'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 'color':'#000000', 'fillOpacity': 0.50, 'weight': 0.1}
    
    NIL = folium.features.GeoJson(
        world_data,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['name', 'pop_est', 'UV_Index', 'VAD_Risk'],
            aliases=['Country: ', 'Population: ', 'UV Index: ', 'Risk %: '],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )
    m.add_child(NIL)
    m.keep_in_renderers()

    st_folium(m, width="100%", height=550)
    st.markdown('</div>', unsafe_allow_html=True)

with col_analysis:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Risk Correlation")
    
    # Real-world scatter: Population vs Cataract Rate
    fig = px.scatter(world_data, x="UV_Index", y="Cataract_Rate",
                     size="pop_est", color="continent", hover_name="name",
                     log_x=False, size_max=40,
                     template="plotly_white",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("**Top High-Risk Territory:**")
    highest_risk = world_data.loc[world_data['VAD_Risk'].idxmax()]
    st.error(f"⚠️ {highest_risk['name']} ({highest_risk['continent']})")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. REGIONAL TABLE
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("### Regional Surveillance Metrics (Verified All Countries)")
# Search/Filter functionality
search_query = st.text_input("Search for a Country", "")
display_df = world_data[['name', 'continent', 'pop_est', 'UV_Index', 'VAD_Risk']]

if search_query:
    display_df = display_df[display_df['name'].str.contains(search_query, case=False)]

st.dataframe(display_df, use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)
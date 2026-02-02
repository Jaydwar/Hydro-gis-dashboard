import pandas as pd
import folium
from folium.plugins import Draw, Fullscreen, MiniMap
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import numpy as np
from streamlit_extras.metric_cards import style_metric_cards
import matplotlib.colors as mcolors
import json

# Page configuration
st.set_page_config(
    page_title="Godavari River Basin Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main { padding: 0; }
    .main-header {
        font-size: 1.5rem; font-weight: 100; color: #0e2f44;
        text-align: center; margin-bottom: 0.5rem; padding: 1.5rem;
        background: linear-gradient(135deg, #e6f7ff 0%, #b3e0ff 100%);
        border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .section-header {
        font-size: 1.6rem; font-weight: 600; color: #0e2f44;
        margin-bottom: 1rem; padding-bottom: 0.5rem;
        border-bottom: 2px solid #4a90e2;
    }
    .info-card {
        background: linear-gradient(135deg, #f5f9ff 0%, #e0ecff 100%);
        padding: 15px; border-radius: 12px; margin-bottom: 1rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #4a90e2;
    }
    .graph-container {
        background-color: white; padding: 20px;
        border-radius: 15px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem; font-weight: 700; color: #0e2f44;
    }
    .stDownloadButton button {
        background: linear-gradient(135deg, #4a90e2 0%, #2a6cbe 100%);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 1rem; font-weight: 600;
    }
    .css-1d391kg { background: linear-gradient(180deg, #f0f8ff 0%, #e6f2ff 100%); }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .folium-map {
        border-radius: 15px; box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        margin-bottom: 1.5rem; height: 550px;
    }
</style>
""", unsafe_allow_html=True)

# Metric card styling
style_metric_cards()

# Title
st.markdown('<h1 class="main-header">Godavari River Basin Monitoring Dashboard</h1>', unsafe_allow_html=True)

# ------------------- LOAD DATA -------------------
@st.cache_data
def load_data():
    # Demo discharge data (synthetic)
    stations = {
    'AGH40A4': {'name': 'ASHTI', 'lat': 19.68667, 'lon': 79.78444},
    'AGH30E2': {'name': 'BAMNI', 'lat': 19.81389, 'lon': 79.37944},
    'AGH10L0': {'name': 'BHATPALLI', 'lat': 19.32972, 'lon': 79.50417},
    'AGG00N7': {'name': 'CHINDNAR', 'lat': 19.08333, 'lon': 81.3},
    'AGP20F4': {'name': 'DEGLOOR', 'lat': 18.56194, 'lon': 77.58306},
    'AGM00G6': {'name': 'GANDLAPET', 'lat': 18.82917, 'lon': 78.43611},
    'AGH30Q1': {'name': 'HIVRA', 'lat': 20.54722, 'lon': 78.32472},
    'AGG00R9': {'name': 'JAGDALPUR', 'lat': 19.10806, 'lon': 82.02278},
    'AGC40E9': {'name': 'MURTHAHANDI', 'lat': 19.05944, 'lon': 82.27583},
    'AGH3AF4': {'name': 'NANDGAON', 'lat': 20.52556, 'lon': 78.80889},
    'AGU00D3': {'name': 'PACHEGAON', 'lat': 19.53444, 'lon': 74.83389},
    'AGG00B5': {'name': 'PATHAGUDEM', 'lat': 18.81667, 'lon': 80.35},
    'AG000G7': {'name': 'PERUR', 'lat': 18.5325, 'lon': 80.38306},
    'AG000C3': {'name': 'POLAVARAM', 'lat': 17.25167, 'lon': 81.6525},
    'AGH30B6': {'name': 'SAKMUR', 'lat': 19.56056, 'lon': 79.61528},
    'AGC00N4': {'name': 'SARADAPUT', 'lat': 18.6125, 'lon': 82.14278},
    'AGG91F2': {'name': 'SONARPAL', 'lat': 19.26972, 'lon': 81.88389},
    'AGG60B1': {'name': 'TUMNAR', 'lat': 19.01222, 'lon': 81.2325},
    'AG000P3': {'name': 'YELLI', 'lat': 19.04417, 'lon': 77.45306},
    'AGR10C6': {'name': 'ZARI', 'lat': 19.39556, 'lon': 76.75444},
}

    all_data = []
    for station_id, info in stations.items():
        for year in range(2015, 2023):
            dates = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31')
            base_flow = np.random.uniform(10, 20)
            seasonal = 15 * np.sin(2 * np.pi * np.arange(len(dates)) / 365 + np.random.uniform(0, 2*np.pi))
            noise = np.random.normal(0, 3, len(dates))
            discharge = np.clip(base_flow + seasonal + noise, 5, 50)
            for i, date in enumerate(dates):
                all_data.append({
                    'STATION_CO': station_id,
                    'YEAR': year,
                    'MONTH': date.month,
                    'DAY': date.day,
                    'Discharge': discharge[i],
                    'Station Name': info['name'],
                    'Lat': info['lat'],
                    'Long': info['lon']
                })
    discharge_df = pd.DataFrame(all_data)

    # Full Polavaram cross-section dataset (2012 & 2022)
    polavaram_data = [
        (2012, 0, 24.985), (2012, 10, 24.7), (2012, 20, 24.565), (2012, 30, 24.45),
        (2012, 40, 23.85), (2012, 45, 23.8), (2012, 50, 22.95), (2012, 60, 19.74),
        (2012, 65, 17.305), (2012, 70, 15.11), (2012, 73, 13.735), (2012, 90, 10.335),
        (2012, 120, 10.135), (2012, 150, 10.735), (2012, 180, 11.135), (2012, 200, 11.235),
        (2012, 210, 11.435), (2012, 240, 11.335), (2012, 270, 11.335), (2012, 300, 11.235),
        (2012, 330, 11.235), (2012, 360, 11.235), (2012, 390, 11.035), (2012, 400, 10.835),
        (2012, 420, 10.635), (2012, 450, 10.735), (2012, 480, 10.835), (2012, 510, 10.735),
        (2012, 540, 10.735), (2012, 570, 10.835), (2012, 600, 10.935), (2012, 630, 11.135),
        (2012, 660, 11.535), (2012, 690, 11.635), (2012, 720, 11.635), (2012, 750, 12.235),
        (2012, 780, 13.135), (2012, 800, 13.335), (2012, 808.6, 13.735), (2012, 810, 14.135),
        (2012, 840, 14.625), (2012, 870, 14.445), (2012, 900, 16.1), (2012, 930, 15.975),
        (2012, 960, 16.17), (2012, 990, 15.54), (2012, 1000, 15.065), (2012, 1020, 14.75),
        (2012, 1050, 14.07), (2012, 1080, 14.855), (2012, 1110, 14.57), (2012, 1140, 14.81),
        (2012, 1170, 14.84), (2012, 1200, 15.65), (2012, 1230, 15.335), (2012, 1260, 16.56),
        (2012, 1290, 16.8), (2012, 1320, 16.32), (2012, 1350, 16.785), (2012, 1375, 17.21),
        (2012, 1380, 18.135), (2012, 1385, 19.94), (2012, 1390, 21.525), (2012, 1395.5, 21.31),
        (2012, 1400, 22.535), (2012, 1402, 22.765), (2012, 1410, 23.705), (2012, 1413, 24.325),
        (2012, 1440, 25.22), (2012, 1470, 24.835), (2012, 1500, 24.855),
        (2022, -166, 30.09), (2022, -164.5, 29.74), (2022, -163, 29.13), (2022, -161.5, 28.48),
        (2022, -160, 27.78), (2022, -157.5, 27.14), (2022, -156, 26.26), (2022, -154.5, 25.22),
        (2022, -153, 24.54), (2022, -150, 24.58), (2022, -120, 24.76), (2022, -90, 24.96),
        (2022, -60, 25.07), (2022, -30, 25.11), (2022, 0, 25.27), (2022, 10, 25.23),
        (2022, 19, 24.72), (2022, 20.5, 24.38), (2022, 22, 23.79), (2022, 23.5, 23.38),
        (2022, 25, 22.15), (2022, 60, 12.45), (2022, 120, 12.15), (2022, 180, 12.36),
        (2022, 240, 13.65), (2022, 300, 13.85), (2022, 360, 13.85), (2022, 420, 13.65),
        (2022, 480, 13.05), (2022, 540, 12.55), (2022, 600, 13.05), (2022, 660, 13.15),
        (2022, 720, 13.25), (2022, 780, 13.15), (2022, 840, 13.95), (2022, 900, 13.75),
        (2022, 960, 13.95), (2022, 1020, 13.65), (2022, 1080, 13.05), (2022, 1140, 12.15),
        (2022, 1200, 11.85), (2022, 1260, 11.95), (2022, 1320, 10.65), (2022, 1380, 15.15),
        (2022, 1420.1, 22.15), (2022, 1421.5, 22.62), (2022, 1423, 23.06), (2022, 1424.5, 24.73)
    ]
    cross_section_df = pd.DataFrame([{
        "Station Name": "Polavaram",
        "Year": year,
        "Reduced Distance": rd,
        "Elevation CGL": elev,
        "Lat": 17.25167,
        "Long": 81.6525
    } for year, rd, elev in polavaram_data])

    # Basin boundary
    file_path = os.path.join("Godavari_Geojon.geojson")
    try:
        # Correct use of os.path.join and open
        file_path = os.path.join("Godavari_Geojon.geojson")  # or "data/Godavari_Geojon.geojson" if inside a folder
        with open(file_path) as f:
            basin_boundary = json.load(f)
    except FileNotFoundError:
        st.error("Godavari_Geojon.geojson not found! Please ensure the file is in the correct directory.")
        basin_boundary = None

    return discharge_df, cross_section_df, basin_boundary

# Load the data
df, cross_section_df, basin_boundary = load_data()

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.markdown("<h2 style='color:#0e2f44;text-align:center;'>Dashboard Controls</h2>", unsafe_allow_html=True)
    tab_option = st.radio("Select View", ["Discharge Data", "Cross-Section Data"], index=0)

    st.markdown("---")

    if tab_option == "Discharge Data":
        stations = df[['STATION_CO', 'Station Name', 'Lat', 'Long']].drop_duplicates()
        years = sorted(df['YEAR'].unique(), reverse=True)
        selected_year = st.selectbox("Select Year", years, index=0)
        station_options = [f"{row['STATION_CO']} - {row['Station Name']}" for _, row in stations.iterrows()]
        selected_station = st.selectbox("Select Station", station_options, index=0)
        station_code = selected_station.split(" - ")[0]
        selected_years = st.multiselect("Multi-Year Comparison", years, default=[selected_year])
        station_info = stations[stations['STATION_CO'] == station_code].iloc[0]

        st.markdown("### Station Information")
        st.markdown(f"""
        <div class="info-card">
            <b>Station Code:</b> {station_info['STATION_CO']}<br>
            <b>Station Name:</b> {station_info['Station Name']}<br>
            <b>Latitude:</b> {station_info['Lat']:.5f}<br>
            <b>Longitude:</b> {station_info['Long']:.5f}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        # Discharge Statistics in the sidebar
        st.markdown("### Discharge Statistics")
        current_year_data = df[(df['STATION_CO']==station_code)&(df['YEAR']==selected_year)]
        min_discharge = current_year_data['Discharge'].min()
        max_discharge = current_year_data['Discharge'].max()
        avg_discharge = current_year_data['Discharge'].mean()
        
        st.metric(label="Min. Discharge (m³/s)", value=f"{min_discharge:,.2f}")
        st.metric(label="Max. Discharge (m³/s)", value=f"{max_discharge:,.2f}")
        st.metric(label="Avg. Discharge (m³/s)", value=f"{avg_discharge:,.2f}")

    else:
        cross_section_stations = cross_section_df[['Station Name', 'Lat', 'Long']].drop_duplicates()
        cross_section_options = list(cross_section_stations['Station Name'].unique())
        selected_cross_section = st.selectbox("Select Station", cross_section_options, index=0)
        available_years = sorted(cross_section_df[cross_section_df['Station Name'] == selected_cross_section]['Year'].unique(), reverse=True)
        selected_years = st.multiselect("Select Years", available_years, default=available_years[:2])
        station_info = cross_section_stations[cross_section_stations['Station Name'] == selected_cross_section].iloc[0]

        st.markdown("### Station Information")
        st.markdown(f"""
        <div class="info-card">
            <b>Station Name:</b> {station_info['Station Name']}<br>
            <b>Latitude:</b> {station_info['Lat']:.5f}<br>
            <b>Longitude:</b> {station_info['Long']:.5f}
        </div>
        """, unsafe_allow_html=True)

# ------------------- MAIN CONTENT -------------------
if tab_option == "Discharge Data":
    map_center = [stations['Lat'].mean(), stations['Long'].mean()]
    m = folium.Map(location=map_center, zoom_start=7, control_scale=True)
    
    if basin_boundary:
        folium.GeoJson(
            basin_boundary,
            name='Godavari Basin',
            style_function=lambda _: {'fillColor': 'blue','color':'blue','weight':2,'fillOpacity':0.1}
        ).add_to(m)

    Fullscreen().add_to(m); MiniMap().add_to(m); Draw(export=True).add_to(m)
    for _, station in stations.iterrows():
        folium.Marker([station['Lat'], station['Long']],
                     popup=f"{station['STATION_CO']} - {station['Station Name']}",
                     icon=folium.Icon(color='red' if station['STATION_CO']==station_code else 'blue')).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=500)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Hydrograph")
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        fig = go.Figure()
        colors = px.colors.qualitative.Plotly
        for i, year in enumerate(selected_years):
            hydro_data = df[(df['STATION_CO']==station_code)&(df['YEAR']==year)].copy()
            hydro_data['Date'] = pd.to_datetime(hydro_data[['YEAR','MONTH','DAY']])
            fig.add_trace(go.Scatter(x=hydro_data['Date'], y=hydro_data['Discharge'],
                                     mode='lines', name=str(year),
                                     line=dict(color=colors[i%len(colors)], width=2.5)))
        fig.update_layout(
            title=dict(
                text=f"Discharge Hydrograph - {station_info['Station Name']}",
                font=dict(family="Arial, sans-serif", size=20, color="black", weight='bold')
            ),
            xaxis_title=dict(
                text="Date",
                font=dict(family="Arial, sans-serif", size=14, color="black", weight='bold')
            ),
            yaxis_title=dict(
                text="Discharge (m³/s)",
                font=dict(family="Arial, sans-serif", size=14, color="black", weight='bold')
            ),
            hovermode="x unified",
            height=400,
            plot_bgcolor="white",
            xaxis=dict(rangeslider=dict(visible=True), type='date')
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("### Data Preview")
        preview = df[(df['STATION_CO']==station_code)&(df['YEAR']==selected_year)].copy()
        preview['Date'] = pd.to_datetime(preview[['YEAR','MONTH','DAY']])
        st.dataframe(preview[['Date','Discharge']].head(8), hide_index=True)
        st.download_button("Download Data (CSV)", data=preview.to_csv(index=False),
                           file_name=f"discharge_{station_code}_{selected_year}.csv", mime="text/csv")

else:
    map_center = [cross_section_stations['Lat'].mean(), cross_section_stations['Long'].mean()]
    m = folium.Map(location=map_center, zoom_start=7, control_scale=True)
    
    if basin_boundary:
        folium.GeoJson(
            basin_boundary,
            name='Godavari Basin',
            style_function=lambda _: {'fillColor': 'blue','color':'blue','weight':2,'fillOpacity':0.1}
        ).add_to(m)
        
    Fullscreen().add_to(m); MiniMap().add_to(m); Draw(export=True).add_to(m)
    for _, station in cross_section_stations.iterrows():
        folium.Marker([station['Lat'], station['Long']],
                     popup=f"{station['Station Name']}",
                     icon=folium.Icon(color='red' if station['Station Name']==selected_cross_section else 'blue')).add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=500)

    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("### River Cross-Section")
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        fig = go.Figure()
        colors = px.colors.qualitative.Plotly
        for i, year in enumerate(selected_years):
            section = cross_section_df[(cross_section_df['Station Name']==selected_cross_section)&(cross_section_df['Year']==year)].copy()
            section = section.sort_values('Reduced Distance')

            # convert hex to rgba properly
            base_color = colors[i % len(colors)]
            r, g, b = [int(255 * c) for c in mcolors.to_rgb(base_color)]
            rgba_color = f"rgba({r},{g},{b},0.3)"

            fig.add_trace(go.Scatter(
                x=section['Reduced Distance'], y=section['Elevation CGL'],
                mode='lines', name=str(year),
                line=dict(color=base_color, width=3),
                fill='tozeroy', 
                fillcolor=rgba_color 
            ))
        fig.update_layout(
            title=dict(
                text=f"Cross-Section at {selected_cross_section}",
                font=dict(family="Arial, sans-serif", size=20, color="black", weight='bold')
            ),
            xaxis_title=dict(
                text="Reduced Distance (m)",
                font=dict(family="Arial, sans-serif", size=14, color="black", weight='bold')
            ),
            yaxis_title=dict(
                text="Elevation (m)",
                font=dict(family="Arial, sans-serif", size=14, color="black", weight='bold')
            ),
            height=400,
            plot_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("### Data Preview")
        preview = cross_section_df[(cross_section_df['Station Name']==selected_cross_section)&(cross_section_df['Year'].isin(selected_years))]
        st.dataframe(preview[['Year','Reduced Distance','Elevation CGL']].head(10), hide_index=True)
        st.download_button("Download Data (CSV)", data=preview.to_csv(index=False),
                           file_name=f"cross_section_{selected_cross_section}.csv", mime="text/csv")

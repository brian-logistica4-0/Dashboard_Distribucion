import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Logístico", layout="wide")

st.title("📦 Dashboard Logístico - Rechazo")

# ======================
# CARGA DATOS
# ======================

@st.cache_data
def cargar_datos():
    df = pd.read_csv("dataset_limpio.csv")
    tabla_cf = pd.read_csv("tabla_rechazo.csv")
    tabla_viajes = pd.read_csv("tabla_rechazo_viajes.csv")
    return df, tabla_cf, tabla_viajes

df, tabla_cf, tabla_viajes = cargar_datos()

# ======================
# FILTRO
# ======================

st.sidebar.header("Filtros")
anio = st.sidebar.selectbox("Año", sorted(tabla_cf["AÑO"].unique()))

df_cf = tabla_cf[tabla_cf["AÑO"] == anio]
df_viajes = tabla_viajes[tabla_viajes["AÑO"] == anio]

# ======================
# 🟦 KPIs
# ======================

st.subheader("📊 Indicadores")

col1, col2, col3 = st.columns(3)

rechazo_cf = df_cf["RECHAZO_%"].mean()
rechazo_viajes = df_viajes["RECHAZO_%_VIAJES"].mean()
total_cf = df_cf["CF"].sum()

col1.metric("📦 Total Cajas", f"{int(total_cf):,}")
col2.metric("❌ Rechazo CF", f"{rechazo_cf:.2f}%")
col3.metric("🚚 Rechazo Viajes", f"{rechazo_viajes:.2f}%")

# ======================
# 🟩 EVOLUCIÓN
# ======================

st.subheader("📈 Evolución")

col1, col2 = st.columns(2)

fig_cf = px.bar(df_cf, x="MES", y="RECHAZO_%", title="Rechazo CF")
fig_viajes = px.bar(df_viajes, x="MES", y="RECHAZO_%_VIAJES", title="Rechazo Viajes")

col1.plotly_chart(fig_cf, use_container_width=True)
col2.plotly_chart(fig_viajes, use_container_width=True)

# ======================
# 🟨 CLIENTES
# ======================

st.subheader("👥 Top Clientes")

df_clientes = df.copy()
df_clientes["CF_FALLIDAS"] = np.where(df_clientes["ES_FALLIDA"], df_clientes["CF"], 0)

tabla_clientes = (
    df_clientes.groupby("CLIENTE")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

top_clientes = tabla_clientes.sort_values("CF_FALLIDAS", ascending=False).head(10)

st.dataframe(top_clientes)

# ======================
# 🚚 CAMIONES
# ======================

st.subheader("🚚 Ranking Camiones")

tabla_camion = (
    df_clientes.groupby("CAMION_U")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_camion["RECHAZO_%"] = tabla_camion["CF_FALLIDAS"] / tabla_camion["CF"] * 100
tabla_camion = tabla_camion[tabla_camion["CF"] > 1000]

st.dataframe(tabla_camion.sort_values("RECHAZO_%", ascending=False).head(10))

# ======================
# 🧑‍✈️ CHOFERES
# ======================

st.subheader("🧑‍✈️ Ranking Choferes")

tabla_chofer = (
    df_clientes.groupby("CHOFER")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_chofer["RECHAZO_%"] = tabla_chofer["CF_FALLIDAS"] / tabla_chofer["CF"] * 100
tabla_chofer = tabla_chofer[tabla_chofer["CF"] > 1000]

st.dataframe(tabla_chofer.sort_values("RECHAZO_%", ascending=False).head(10))

# ======================
# 🟥 CADENAS
# ======================

st.subheader("🏪 Cadenas")

tabla_cadena = (
    df_clientes.groupby("CADENA2")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

total = tabla_cadena["CF_FALLIDAS"].sum()

tabla_cadena["PART_RECHAZO_%"] = tabla_cadena["CF_FALLIDAS"] / total * 100

st.dataframe(tabla_cadena.sort_values("PART_RECHAZO_%", ascending=False).head(10))

# ======================
# 🟪 AUTORIZACION
# ======================

st.subheader("⚠️ AUTORIZACION DE RETORNO")

df_aut = df[df["AUTORIZADO_?"].isin(["CHOFER", "DISTRIBUCION", "GREMIO"])]

tabla_aut = (
    df_aut.groupby("AUTORIZADO_?")["CF"]
    .sum()
    .reset_index()
)

total_fallidas = tabla_aut["CF"].sum()

tabla_aut["PARTICIPACION_%"] = tabla_aut["CF"] / total_fallidas * 100

st.dataframe(tabla_aut.sort_values("PARTICIPACION_%", ascending=False))

# ======================
# 🗺️ MAPA ZONAS + CLIENTES (FORMATO JUPYTER)
# ======================

import json
import plotly.graph_objects as go

st.subheader("🗺️ Mapa de Clientes por Zona")

# ======================
# GEOJSON
# ======================
with open("amba.geojson", "r", encoding="utf-8") as f:
    geo_amba = json.load(f)

# ======================
# ZONAS
# ======================
gba_norte = ["Vicente López","San Isidro","San Fernando","Tigre","Escobar","Pilar","Malvinas Argentinas","San Miguel","José C. Paz"]
gba_oeste = ["General San Martín","Tres De Febrero","Morón","Ituzaingó","Hurlingham","La Matanza","Merlo","Moreno"]
gba_sur = ["Avellaneda","Lanús","Quilmes","Lomas De Zamora","Almirante Brown","Florencio Varela","Berazategui","Ezeiza","Esteban Echeverría","San Vicente","Presidente Perón"]

municipios_amba = ["Ciudad Autónoma de Buenos Aires"] + gba_norte + gba_oeste + gba_sur

# ======================
# FILTRAR GEOJSON
# ======================
features_filtradas = [
    f for f in geo_amba["features"]
    if f["properties"]["name"] in municipios_amba
]

geo_amba_filtrado = {
    "type": "FeatureCollection",
    "features": features_filtradas
}

# ======================
# DATAFRAME ZONAS
# ======================
df_geo = pd.DataFrame({"municipio": municipios_amba})

def clasificar(m):
    if m == "Ciudad Autónoma de Buenos Aires":
        return "CABA"
    elif m in gba_norte:
        return "GBA Norte"
    elif m in gba_oeste:
        return "GBA Oeste"
    else:
        return "GBA Sur"

df_geo["zona"] = df_geo["municipio"].apply(clasificar)

color_map = {
    "CABA": "#C62828",
    "GBA Norte": "#1565C0",
    "GBA Oeste": "#2E7D32",
    "GBA Sur": "#6A1B9A"
}

# ======================
# CLIENTES
# ======================
df_map = df.dropna(subset=["LATITUD", "LONGITUD"]).copy()

# ======================
# MAPA BASE (ZONAS)
# ======================
fig = px.choropleth_mapbox(
    df_geo,
    geojson=geo_amba_filtrado,
    locations="municipio",
    featureidkey="properties.name",
    color="zona",
    color_discrete_map=color_map,
    opacity=0.4,
    center={"lat": -34.6, "lon": -58.45},
    zoom=8,
    height=700
)

# ======================
# CLIENTES (PUNTOS NEGROS)
# ======================
fig.add_trace(go.Scattermapbox(
    lat=df_map["LATITUD"],
    lon=df_map["LONGITUD"],
    mode="markers",
    marker=dict(size=7, color="black"),
    text=df_map["CLIENTE"],
    name="Clientes"
))

# ======================
# ETIQUETAS GRANDES (OPCIONAL)
# ======================
fig.add_trace(go.Scattermapbox(
    lat=[-34.45],
    lon=[-58.55],
    text=["NORTE"],
    mode="text",
    textfont=dict(size=18, color="red"),
    showlegend=False
))

# ======================
# ESTILO FINAL
# ======================
fig.update_layout(
    mapbox_style="carto-positron",
    legend_title="Zona"
)

st.plotly_chart(fig, use_container_width=True)

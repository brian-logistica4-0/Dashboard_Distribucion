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

st.subheader("⚠️ Causas de Rechazo")

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
# 🗺️ MAPA MEJORADO (TU FORMATO)
# ======================

st.subheader("🗺️ Mapa de Clientes")

df_map = df.copy()

# limpieza segura
df_map["LATITUD"] = pd.to_numeric(df_map["LATITUD"], errors="coerce")
df_map["LONGITUD"] = pd.to_numeric(df_map["LONGITUD"], errors="coerce")
df_map["CF"] = pd.to_numeric(df_map["CF"], errors="coerce")

df_map["CF_FALLIDAS"] = np.where(df_map["ES_FALLIDA"], df_map["CF"], 0)

df_map = df_map.dropna(subset=["LATITUD", "LONGITUD"])
df_map = df_map[df_map["CF"] > 0]

fig_map = px.scatter_mapbox(
    df_map,
    lat="LATITUD",
    lon="LONGITUD",
    size="CF",                     # tamaño = volumen
    color="CF_FALLIDAS",          # color = rechazo
    color_continuous_scale="Reds",
    hover_name="CLIENTE",
    zoom=9,
    height=600
)

fig_map.update_layout(mapbox_style="carto-positron")

st.plotly_chart(fig_map, use_container_width=True)

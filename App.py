import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Logístico", layout="wide")

# Título
st.title("📦 Indicador de Rechazo Logístico")

# =========================
# Cargar datos
# =========================
tabla_cf = pd.read_csv("tabla_rechazo.csv")
tabla_viajes = pd.read_csv("tabla_rechazo_viajes.csv")

# Orden correcto de meses
orden_meses = [
    "ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
    "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"
]

for tabla in [tabla_cf, tabla_viajes]:
    tabla["MES"] = pd.Categorical(tabla["MES"], categories=orden_meses, ordered=True)
    tabla.sort_values(["AÑO", "MES"], inplace=True)

# =========================
# Selector de año
# =========================
anio = st.selectbox("Seleccionar Año", sorted(tabla_cf["AÑO"].unique()))

# Filtrar datos
df_cf = tabla_cf[tabla_cf["AÑO"] == anio]
df_viajes = tabla_viajes[tabla_viajes["AÑO"] == anio]

# =========================
# KPI (en columnas)
# =========================
col1, col2 = st.columns(2)

with col1:
    st.metric("Rechazo CF Promedio (%)", f"{df_cf['RECHAZO_%'].mean():.2f}%")

with col2:
    st.metric("Rechazo Viajes Promedio (%)", f"{df_viajes['RECHAZO_%_VIAJES'].mean():.2f}%")

# =========================
# Gráficos separados
# =========================

col1, col2 = st.columns(2)

# --- GRAFICO 1 ---
fig_cf = px.bar(
    df_cf,
    x="MES",
    y="RECHAZO_%",
    title=f"Rechazo CF - {anio}"
)

# --- GRAFICO 2 ---
fig_viajes = px.bar(
    df_viajes,
    x="MES",
    y="RECHAZO_%_VIAJES",
    title=f"Rechazo Viajes - {anio}"
)

with col1:
    st.plotly_chart(fig_cf, use_container_width=True)

with col2:
    st.plotly_chart(fig_viajes, use_container_width=True)

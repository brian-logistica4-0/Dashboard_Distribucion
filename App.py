import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Control Tower Logística", layout="wide")

st.title("🚚 Control Tower Logística - Nivel Premium")

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
# PREPARACION DATOS
# ======================
df["CF_FALLIDAS"] = np.where(df["ES_FALLIDA"], df["CF"], 0)

# ======================
# FILTROS
# ======================
st.sidebar.header("Filtros")

anio = st.sidebar.selectbox("Año", sorted(tabla_cf["AÑO"].unique()))

df_cf = tabla_cf[tabla_cf["AÑO"] == anio]
df_viajes = tabla_viajes[tabla_viajes["AÑO"] == anio]

# ======================
# KPI COLORS
# ======================
def color_kpi(valor):
    if valor < 5:
        return "green"
    elif valor < 10:
        return "orange"
    else:
        return "red"

rechazo_cf = df_cf["RECHAZO_%"].mean()
rechazo_viajes = df_viajes["RECHAZO_%_VIAJES"].mean()
total_cf = df_cf["CF"].sum()

# ======================
# 🟦 FILA 1
# ======================
col1, col2 = st.columns(2)

# -------- OPERATIVO --------
with col1:
    st.subheader("📊 Operación")

    k1, k2, k3 = st.columns(3)

    k1.metric("📦 Cajas", f"{int(total_cf):,}")
    k2.markdown(f"### ❌ Rechazo CF: <span style='color:{color_kpi(rechazo_cf)}'>{rechazo_cf:.2f}%</span>", unsafe_allow_html=True)
    k3.markdown(f"### 🚚 Rechazo Viajes: <span style='color:{color_kpi(rechazo_viajes)}'>{rechazo_viajes:.2f}%</span>", unsafe_allow_html=True)

    fig_cf = px.line(df_cf, x="MES", y="RECHAZO_%", markers=True)
    st.plotly_chart(fig_cf, use_container_width=True)

# -------- MAPA PRO --------
with col2:
    st.subheader("🗺️ Mapa de Distribución")

    df_map = df.dropna(subset=["LATITUD","LONGITUD"])

    fig_map = px.scatter_mapbox(
        df_map,
        lat="LATITUD",
        lon="LONGITUD",
        size="CF",
        color="CF_FALLIDAS",
        color_continuous_scale="Reds",
        hover_name="CLIENTE",
        zoom=9,
        height=500
    )

    fig_map.update_layout(mapbox_style="carto-positron")

    st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 🟩 FILA 2
# ======================
col3, col4 = st.columns(2)

# -------- PERFORMANCE --------
with col3:
    st.subheader("🚚 Performance")

    tabla_camion = (
        df.groupby("CAMION_U")[["CF","CF_FALLIDAS"]]
        .sum()
        .reset_index()
    )

    tabla_camion["RECHAZO_%"] = tabla_camion["CF_FALLIDAS"] / tabla_camion["CF"] * 100
    tabla_camion = tabla_camion[tabla_camion["CF"] > 1000]

    fig_camion = px.bar(
        tabla_camion.sort_values("RECHAZO_%", ascending=False).head(10),
        x="CAMION_U",
        y="RECHAZO_%",
        color="RECHAZO_%",
        color_continuous_scale="Reds"
    )

    st.plotly_chart(fig_camion, use_container_width=True)

# -------- RECHAZOS --------
with col4:
    st.subheader("📉 Rechazos")

    tabla_cadena = (
        df.groupby("CADENA2")[["CF","CF_FALLIDAS"]]
        .sum()
        .reset_index()
    )

    tabla_cadena["PART_%"] = tabla_cadena["CF_FALLIDAS"] / tabla_cadena["CF_FALLIDAS"].sum() * 100

    fig_pie = px.pie(tabla_cadena, names="CADENA2", values="PART_%")
    st.plotly_chart(fig_pie, use_container_width=True)

    df_aut = df[df["AUTORIZADO_?"].isin(["CHOFER","DISTRIBUCION","GREMIO"])]

    fig_aut = px.bar(
        df_aut.groupby("AUTORIZADO_?")["CF"].sum().reset_index(),
        x="AUTORIZADO_?",
        y="CF",
        color="CF"
    )

    st.plotly_chart(fig_aut, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Logístico", layout="wide")

# Título
st.title("📦 Indicador de Rechazo Logístico")

# Cargar datos
tabla = pd.read_csv("tabla_rechazo.csv")

# Orden correcto de meses
orden_meses = [
    "ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO",
    "JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"
]

tabla["MES"] = pd.Categorical(tabla["MES"], categories=orden_meses, ordered=True)
tabla = tabla.sort_values(["AÑO", "MES"])

# Selector de año
anio = st.selectbox("Seleccionar Año", sorted(tabla["AÑO"].unique()))

# Filtrar datos
df = tabla[tabla["AÑO"] == anio]

# KPI
st.metric("Rechazo Promedio (%)", f"{df['RECHAZO_%'].mean():.2f}%")

# Gráfico de barras interactivo
fig = px.bar(
    df,
    x="MES",
    y="RECHAZO_%",
    text="RECHAZO_%",
    title=f"Rechazo por Mes - {anio}"
)

fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")

st.plotly_chart(fig, use_container_width=True)

# Tabla
st.subheader("Tabla de Datos")
st.dataframe(df)

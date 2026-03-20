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
df["FECHA_DE_SALIDA"] = pd.to_datetime(df["FECHA_DE_SALIDA"], errors="coerce")
st.sidebar.header("Filtros")


# ======================
# CAMPOS DE TIEMPO
# ======================

# fecha limpia para filtros
df["FECHA"] = df["FECHA_DE_SALIDA"].dt.date

# agregados útiles
df["MES_NUM"] = df["FECHA_DE_SALIDA"].dt.month
df["MES"] = df["FECHA_DE_SALIDA"].dt.strftime("%b")

orden_meses = df.sort_values("MES_NUM")["MES"].unique()

df["SEMANA"] = df["FECHA_DE_SALIDA"].dt.isocalendar().week

df["AÑO"] = df["FECHA_DE_SALIDA"].dt.year
df["DIA"] = df["FECHA_DE_SALIDA"].dt.day
# ======================
# FILTROS AVANZADOS
# ======================

df_filtrado = df.copy()

# ----------------------
# AÑO
# ----------------------
anios = st.sidebar.multiselect(
    "Año",
    sorted(df["AÑO"].dropna().unique())
)

if anios:
    df_filtrado = df_filtrado[df_filtrado["AÑO"].isin(anios)]

# ----------------------
# MES
# ----------------------
meses = st.sidebar.multiselect(
    "Mes",
    sorted(
        df["MES"].dropna().unique(),
        key=lambda x: list(orden_meses).index(x)
    )
)

if meses:
    df_filtrado = df_filtrado[df_filtrado["MES"].isin(meses)]

# ----------------------
# SEMANA
# ----------------------
semanas = st.sidebar.multiselect(
    "Semana",
    sorted(df["SEMANA"].dropna().unique())
)

if semanas:
    df_filtrado = df_filtrado[df_filtrado["SEMANA"].isin(semanas)]

# ----------------------
# DIA
# ----------------------
dias = st.sidebar.multiselect(
    "Día",
    sorted(df["DIA"].dropna().unique())
)

if dias:
    df_filtrado = df_filtrado[df_filtrado["DIA"].isin(dias)]

# ----------------------
# RANGO DE FECHAS (OPCIONAL)
# ----------------------
fecha_min = df["FECHA_DE_SALIDA"].min().date()
fecha_max = df["FECHA_DE_SALIDA"].max().date()

fecha_rango = st.sidebar.date_input(
    "Rango de fechas (opcional)",
    value=(fecha_min, fecha_max)
)

if isinstance(fecha_rango, tuple) and len(fecha_rango) == 2:
    inicio, fin = fecha_rango

    inicio = pd.to_datetime(inicio)
    fin = pd.to_datetime(fin) + pd.Timedelta(days=1)

    df_filtrado = df_filtrado[
        (df_filtrado["FECHA_DE_SALIDA"] >= inicio) &
        (df_filtrado["FECHA_DE_SALIDA"] < fin)
    ]

# FORMATO
if "FORMATO_CADENA" in df.columns:
    formato = st.sidebar.multiselect(
        "Formato de Cliente",
        df["FORMATO_CADENA"].dropna().unique()
    )
    if formato:
        df_filtrado = df_filtrado[df_filtrado["FORMATO_CADENA"].isin(formato)]

# ======================
# CALCULOS
# ======================
df["ES_FALLIDA"] = df["ES_FALLIDA"].astype(str).str.upper().isin(["TRUE", "1", "SI"])

total_cf = df_filtrado["CF"].sum()
cf_rech = df_filtrado[df_filtrado["ES_FALLIDA"] == True]["CF"].sum()
rechazo_cf = (cf_rech / total_cf) * 100 if total_cf > 0 else 0

df_filtrado["VIAJE_ID"] = (
    df_filtrado["CAMION_U"].astype(str) + "_" +
    df_filtrado["FECHA_DE_SALIDA"].dt.date.astype(str)
)

viajes_total = df_filtrado["VIAJE_ID"].nunique()

viajes_fallidos = df_filtrado[
    df_filtrado["ES_FALLIDA"] == True
]["VIAJE_ID"].nunique()

rechazo_viajes = (viajes_fallidos / viajes_total) * 100 if viajes_total > 0 else 0
df_clientes = df_filtrado.copy()
df_clientes["CF_FALLIDAS"] = np.where(df_clientes["ES_FALLIDA"], df_clientes["CF"], 0)

tabla_clientes = (
    df_clientes.groupby("CLIENTE")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

top_clientes = tabla_clientes.sort_values("CF_FALLIDAS", ascending=False).head(10)

tabla_camion = (
    df_clientes.groupby("CAMION_U")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_camion["RECHAZO_%"] = tabla_camion["CF_FALLIDAS"] / tabla_camion["CF"] * 100
tabla_camion = tabla_camion[tabla_camion["CF"] > 1000]

tabla_chofer = (
    df_clientes.groupby("CHOFER")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_chofer["RECHAZO_%"] = tabla_chofer["CF_FALLIDAS"] / tabla_chofer["CF"] * 100
tabla_chofer = tabla_chofer[tabla_chofer["CF"] > 1000]

tabla_cadena = (
    df_clientes.groupby("CADENA2")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

total = tabla_cadena["CF_FALLIDAS"].sum()
tabla_cadena["PART_RECHAZO_%"] = tabla_cadena["CF_FALLIDAS"] / total * 100

df_aut = df_filtrado[df_filtrado["AUTORIZADO_?"].isin(["CHOFER", "DISTRIBUCION", "GREMIO"])]

tabla_aut = (
    df_aut.groupby("AUTORIZADO_?")["CF"]
    .sum()
    .reset_index()
)

total_fallidas = tabla_aut["CF"].sum()
tabla_aut["PARTICIPACION_%"] = tabla_aut["CF"] / total_fallidas * 100

# ======================
# GRAFICOS
# ======================
tabla_mes_cf = (
    df_filtrado
    .groupby("MES")[["CF"]]
    .sum()
    .reset_index()
)

cf_fallidas = (
    df_filtrado[df_filtrado["ES_FALLIDA"] == True]
    .groupby("MES")["CF"]
    .sum()
    .reset_index(name="CF_FALLIDAS")
)

tabla_mes_cf = tabla_mes_cf.merge(cf_fallidas, on="MES", how="left").fillna(0)

tabla_mes_cf["RECHAZO_%"] = (
    tabla_mes_cf["CF_FALLIDAS"] / tabla_mes_cf["CF"]
) * 100

fig_cf = px.bar(
    tabla_mes_cf,
    x="MES",
    y="RECHAZO_%",
    title="Rechazo CF",
    text=tabla_mes_cf["RECHAZO_%"].round(1),
    category_orders={"MES": list(orden_meses)}
)

fig_cf.update_traces(
    textposition="outside",
    marker_color="#E41A1C"
)

fig_cf.update_layout(
    yaxis_title="%",
    xaxis_title="Mes",
    height=420,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_cf.update_xaxes(showgrid=False)
fig_cf.update_yaxes(showgrid=False)
fig_cf.update_yaxes(visible=False)

# ======================
# VIAJES POR MES (SIMPLIFICADO)
# ======================

df_viajes_calc = df_filtrado.copy()

df_viajes_calc["VIAJE_ID"] = (
    df_viajes_calc["CAMION_U"].astype(str) + "_" +
    df_viajes_calc["FECHA_DE_SALIDA"].dt.date.astype(str)
)

tabla_viajes = (
    df_viajes_calc
    .groupby(["MES", "VIAJE_ID"])
    .size()
    .reset_index()
    .groupby("MES")
    .size()
    .reset_index(name="VIAJES")
)

viajes_fallidos = (
    df_viajes_calc[df_viajes_calc["ES_FALLIDA"] == True]
    .groupby(["MES", "VIAJE_ID"])
    .size()
    .reset_index()
    .groupby("MES")
    .size()
    .reset_index(name="VIAJES_FALLIDOS")
)

tabla_viajes = tabla_viajes.merge(viajes_fallidos, on="MES", how="left").fillna(0)

tabla_viajes["RECHAZO_%"] = (
    tabla_viajes["VIAJES_FALLIDOS"] / tabla_viajes["VIAJES"]
) * 100

fig_viajes = px.bar(
    tabla_viajes,
    x="MES",
    y="RECHAZO_%",
    title="Rechazo Viajes",
    text=tabla_viajes["RECHAZO_%"].round(1),
    category_orders={"MES": list(orden_meses)}
)

fig_viajes.update_traces(
    textposition="outside",
    marker_color="#E41A1C"
)

fig_viajes.update_layout(
    yaxis_title="%",
    xaxis_title="Mes",
    height=420,
    plot_bgcolor="white",
    paper_bgcolor="white"
)

fig_viajes.update_xaxes(showgrid=False)
fig_viajes.update_yaxes(showgrid=False)
fig_viajes.update_yaxes(visible=False)

# ======================
# MAPA
# ======================

import json
import plotly.graph_objects as go

with open("amba.geojson", "r", encoding="utf-8") as f:
    geo_amba = json.load(f)

gba_norte = ["Vicente López","San Isidro","San Fernando","Tigre","Escobar","Pilar","Malvinas Argentinas","San Miguel","José C. Paz"]
gba_oeste = ["General San Martín","Tres De Febrero","Morón","Ituzaingó","Hurlingham","La Matanza","Merlo","Moreno"]
gba_sur = ["Avellaneda","Lanús","Quilmes","Lomas De Zamora","Almirante Brown","Florencio Varela","Berazategui","Ezeiza","Esteban Echeverría","San Vicente","Presidente Perón"]

municipios_amba = ["Ciudad Autónoma de Buenos Aires"] + gba_norte + gba_oeste + gba_sur

features_filtradas = [
    f for f in geo_amba["features"]
    if f["properties"]["name"] in municipios_amba
]

geo_amba_filtrado = {
    "type": "FeatureCollection",
    "features": features_filtradas
}

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

cliente_seleccionado = st.selectbox(
    "Seleccionar cliente en mapa",
    ["Todos"] + sorted(df_filtrado["CLIENTE"].dropna().unique())
)
df_map = df_filtrado.dropna(subset=["LATITUD", "LONGITUD"]).copy()

if cliente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["CLIENTE"] == cliente_seleccionado]
    df_map = df_filtrado.dropna(subset=["LATITUD", "LONGITUD"]).copy()

fig_map = px.choropleth_mapbox(
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

fig_map.add_trace(go.Scattermapbox(
    lat=df_map["LATITUD"],
    lon=df_map["LONGITUD"],
    mode="markers",
    marker=dict(size=7, color="black"),
    text=df_map["CLIENTE"],
    name="Clientes"
))

fig_map.update_layout(
    mapbox_style="carto-positron",
    legend_title="Zona"
)

# ======================
# 🟦 FILA 1
# ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Dashboard Operativo")

    k1, k2, k3 = st.columns(3)
    k1.metric("📦 Total Cajas", f"{int(total_cf):,}")
    k2.metric("❌ Rechazo CF", f"{rechazo_cf:.2f}%")
    k3.metric("🚚 Rechazo Viajes", f"{rechazo_viajes:.2f}%")

    g1, g2 = st.columns(2)
    g1.plotly_chart(fig_cf, use_container_width=True)
    g2.plotly_chart(fig_viajes, use_container_width=True)
    
    st.subheader("Top Clientes - Rechazos")
    st.dataframe(top_clientes, use_container_width=True)

with col2:
    st.subheader("🗺️ Mapa de Distribución")
    st.subheader("Geografia - Caracteristicas")
    st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 🟩 FILA 2
# ======================
col3, col4 = st.columns(2)

with col3:
    st.subheader("🚚 Rechazo por interno")
    st.dataframe(tabla_camion.sort_values("RECHAZO_%", ascending=False).head(10), use_container_width=True)
    st.subheader("🚚 Rechazo por chofer")
    st.dataframe(tabla_chofer.sort_values("RECHAZO_%", ascending=False).head(10), use_container_width=True)

with col4:
    st.subheader("📉 Analisis por cadenas")
    st.dataframe(tabla_cadena.sort_values("PART_RECHAZO_%", ascending=False).head(10), use_container_width=True)
    st.subheader("📉 Autorizacion de retorno")
    st.dataframe(tabla_aut.sort_values("PARTICIPACION_%", ascending=False), use_container_width=True)

# ======================
# 🚛 RECHAZO POR TIPO DE CAMIÓN
# ======================

st.subheader("🚛 Rechazo por tipo de camión")

df_camion_tipo = df_filtrado[
    df_filtrado["TIPO_DE_CAMIÓN"].isin(["Chasis", "Semi"])
].copy()

df_camion_tipo["CF_FALLIDAS"] = np.where(
    df_camion_tipo["ES_FALLIDA"] == True,
    df_camion_tipo["CF"],
    0
)

tabla_tipo_camion = (
    df_camion_tipo
    .groupby("TIPO_DE_CAMIÓN")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_tipo_camion["RECHAZO_%"] = (
    tabla_tipo_camion["CF_FALLIDAS"] / tabla_tipo_camion["CF"]
) * 100

st.dataframe(tabla_tipo_camion, use_container_width=False)


# ======================
# 🚚 RECHAZO POR TIPO DE VIAJE
# ======================

st.subheader("🚚 Rechazo por tipo de viaje")

df_viajes_tipo = df_filtrado.copy()

df_viajes_tipo["TIPO_VIAJE"] = np.where(
    df_viajes_tipo["SECUENCIA"] == "1ER VIAJE",
    "1ER VIAJE",
    "RECARGA"
)

df_viajes_tipo["CF_FALLIDAS"] = np.where(
    df_viajes_tipo["ES_FALLIDA"] == True,
    df_viajes_tipo["CF"],
    0
)

tabla_viajes_tipo = (
    df_viajes_tipo
    .groupby("TIPO_VIAJE")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_viajes_tipo["RECHAZO_%"] = (
    tabla_viajes_tipo["CF_FALLIDAS"] / tabla_viajes_tipo["CF"]
) * 100

st.dataframe(tabla_viajes_tipo, use_container_width=False)

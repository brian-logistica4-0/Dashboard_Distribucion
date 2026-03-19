import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Logístico", layout="wide")

st.title("🚚 Control Tower Logística")

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
# FILTROS
# ======================
st.sidebar.header("Filtros")
anio = st.sidebar.selectbox("Año", sorted(tabla_cf["AÑO"].unique()))

df_cf = tabla_cf[tabla_cf["AÑO"] == anio]
df_viajes = tabla_viajes[tabla_viajes["AÑO"] == anio]

# ======================
# CALCULOS BASE
# ======================
rechazo_cf = df_cf["RECHAZO_%"].mean()
rechazo_viajes = df_viajes["RECHAZO_%_VIAJES"].mean()
total_cf = df_cf["CF"].sum()

df_clientes = df.copy()
df_clientes["CF_FALLIDAS"] = np.where(df_clientes["ES_FALLIDA"], df_clientes["CF"], 0)

# ======================
# 🟦 FILA 1
# ======================
col1, col2 = st.columns(2)

# -------- IZQUIERDA: OPERATIVO --------
with col1:
    st.subheader("📊 Dashboard Operativo")

    k1, k2, k3 = st.columns(3)
    k1.metric("📦 Total Cajas", f"{int(total_cf):,}")
    k2.metric("❌ Rechazo CF", f"{rechazo_cf:.2f}%")
    k3.metric("🚚 Rechazo Viajes", f"{rechazo_viajes:.2f}%")

    fig_cf = px.bar(df_cf, x="MES", y="RECHAZO_%", title="Rechazo CF")
    st.plotly_chart(fig_cf, use_container_width=True)

    top_clientes = (
        df_clientes.groupby("CLIENTE")[["CF", "CF_FALLIDAS"]]
        .sum()
        .reset_index()
        .sort_values("CF_FALLIDAS", ascending=False)
        .head(10)
    )

    st.dataframe(top_clientes, use_container_width=True)

# -------- DERECHA: MAPA --------
with col2:
    st.subheader("🗺️ Mapa de Distribución")

    k1, k2 = st.columns(2)
    k1.metric("Rechazos Totales", int(df_clientes["CF_FALLIDAS"].sum()))
    k2.metric("Clientes", df_clientes["CLIENTE"].nunique())

    # ======================
    # GEOJSON
    # ======================
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

    df_map = df.dropna(subset=["LATITUD", "LONGITUD"]).copy()

    if "OBSERVACIONES_y" in df_map.columns:
        df_map["OBSERVACIONES_y"] = df_map["OBSERVACIONES_y"].fillna("Sin observaciones")
    else:
        df_map["OBSERVACIONES_y"] = "Sin observaciones"

    fig_map = px.choropleth_mapbox(
        df_geo,
        geojson=geo_amba_filtrado,
        locations="municipio",
        featureidkey="properties.name",
        color="zona",
        color_discrete_map=color_map,
        opacity=0.3,
        center={"lat": -34.6, "lon": -58.45},
        zoom=8,
        height=600
    )

    fig_map.add_trace(go.Scattermapbox(
        lat=df_map["LATITUD"],
        lon=df_map["LONGITUD"],
        mode="markers",
        marker=dict(size=7, color="black"),
        text=df_map["CLIENTE"],
        customdata=df_map[["HORARIO", "TIPO DE CAMION", "OBSERVACIONES_y"]] if "HORARIO" in df_map.columns else None,
        hovertemplate=
            "<b>%{text}</b><br><br>" +
            "🕒 Horario: %{customdata[0]}<br>" +
            "🚚 Tipo Camión: %{customdata[1]}<br>" +
            "📝 Obs: %{customdata[2]}<br>" if "HORARIO" in df_map.columns else "<b>%{text}</b>",
        name="Clientes"
    ))

    fig_map.update_layout(mapbox_style="carto-positron")

    st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 🟩 FILA 2
# ======================
col3, col4 = st.columns(2)

# -------- IZQUIERDA --------
with col3:
    st.subheader("🚚 Performance Operativa")

    tabla_camion = (
        df_clientes.groupby("CAMION_U")[["CF", "CF_FALLIDAS"]]
        .sum()
        .reset_index()
    )

    tabla_camion["RECHAZO_%"] = tabla_camion["CF_FALLIDAS"] / tabla_camion["CF"] * 100
    tabla_camion = tabla_camion[tabla_camion["CF"] > 1000]

    fig_camion = px.bar(
        tabla_camion.sort_values("RECHAZO_%", ascending=False).head(10),
        x="CAMION_U",
        y="RECHAZO_%",
        title="Top Camiones con Mayor Rechazo"
    )

    st.plotly_chart(fig_camion, use_container_width=True)

    tabla_chofer = (
        df_clientes.groupby("CHOFER")[["CF", "CF_FALLIDAS"]]
        .sum()
        .reset_index()
    )

    tabla_chofer["RECHAZO_%"] = tabla_chofer["CF_FALLIDAS"] / tabla_chofer["CF"] * 100
    tabla_chofer = tabla_chofer[tabla_chofer["CF"] > 1000]

    st.dataframe(tabla_chofer.sort_values("RECHAZO_%", ascending=False).head(10), use_container_width=True)

# -------- DERECHA --------
with col4:
    st.subheader("📉 Análisis de Rechazos")

    tabla_cadena = (
        df_clientes.groupby("CADENA2")[["CF", "CF_FALLIDAS"]]
        .sum()
        .reset_index()
    )

    total = tabla_cadena["CF_FALLIDAS"].sum()
    tabla_cadena["PART_RECHAZO_%"] = tabla_cadena["CF_FALLIDAS"] / total * 100

    fig_cadena = px.pie(
        tabla_cadena,
        names="CADENA2",
        values="PART_RECHAZO_%",
        title="Participación por Cadena"
    )

    st.plotly_chart(fig_cadena, use_container_width=True)

    df_aut = df[df["AUTORIZADO_?"].isin(["CHOFER", "DISTRIBUCION", "GREMIO"])]

    tabla_aut = (
        df_aut.groupby("AUTORIZADO_?")["CF"]
        .sum()
        .reset_index()
    )

    fig_aut = px.bar(
        tabla_aut,
        x="AUTORIZADO_?",
        y="CF",
        title="Causas de Rechazo"
    )

    st.plotly_chart(fig_aut, use_container_width=True)

    fig_viajes = px.line(
        df_viajes,
        x="MES",
        y="RECHAZO_%_VIAJES",
        title="Evolución Rechazo Viajes"
    )

    st.plotly_chart(fig_viajes, use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# ======================
# CONFIG
# ======================
st.set_page_config(page_title="Dashboard Logístico", layout="wide")

st.title("📦 Dashboard de Distribución - Rechazo Logístico")

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
df["FECHA_DE_SALIDA"] = pd.to_datetime(
    df["FECHA_DE_SALIDA"],
    dayfirst=True,
    errors="coerce"
)

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
st.sidebar.header("Filtros")
st.sidebar.subheader("Cliente")

cliente_seleccionado = st.sidebar.selectbox(
    "Seleccionar cliente",
    ["Todos"] + sorted(df["CLIENTE"].dropna().unique())
)

df_filtrado = df.copy()

if cliente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["CLIENTE"] == cliente_seleccionado]

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

# TOTAL CAJAS
total_cf = df_filtrado["CF"].sum()

# CAJAS RECHAZADAS
cf_rech = df_filtrado[df_filtrado["ES_FALLIDA"] == True]["CF"].sum()

# % RECHAZO CAJAS
rechazo_cf = (cf_rech / total_cf) * 100 if total_cf > 0 else 0


# ======================
# VIAJES
# ======================
# TOTAL VIAJES
viajes_total = len(df_filtrado)

# VIAJES FALLIDOS
viajes_rech = df_filtrado["ES_FALLIDA"].sum()

# % RECHAZO VIAJES
rechazo_viajes = (viajes_rech / viajes_total) * 100 if viajes_total > 0 else 0

# ======================
# CLIENTES
# ======================
df_clientes = df_filtrado.copy()
df_clientes["CF_FALLIDAS"] = np.where(df_clientes["ES_FALLIDA"], df_clientes["CF"], 0)
tabla_clientes = (
    df_clientes.groupby("CLIENTE")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)
tabla_clientes["RECHAZO_%"] = (
    tabla_clientes["CF_FALLIDAS"] / tabla_clientes["CF"]
) * 100

top_clientes = tabla_clientes.sort_values("CF_FALLIDAS", ascending=False).head(10)

# ======================
# INTERNO
# ======================

tabla_camion = (
    df_clientes.groupby("CAMIÓN")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_camion["RECHAZO_%"] = tabla_camion["CF_FALLIDAS"] / tabla_camion["CF"] * 100


# ======================
# CHOFER
# ======================
tabla_chofer = (
    df_clientes.groupby("CHOFER")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

tabla_chofer["RECHAZO_%"] = tabla_chofer["CF_FALLIDAS"] / tabla_chofer["CF"] * 100

# ======================
# CADENA
# ======================

tabla_cadena = (
    df_clientes.groupby("CADENA2")[["CF", "CF_FALLIDAS"]]
    .sum()
    .reset_index()
)

total = tabla_cadena["CF_FALLIDAS"].sum()
tabla_cadena["PART_RECHAZO_%"] = tabla_cadena["CF_FALLIDAS"] / total * 100

# ======================
# AUTORIZACION
# ======================
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
# VIAJES POR MES
# ======================

tabla_viajes = (
    df_filtrado
    .groupby("MES")
    .agg(
        VIAJES=("CAMIÓN", "count"),
        VIAJES_FALLIDOS=("ES_FALLIDA", "sum")
    )
    .reset_index()
)

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
    marker=dict(size=8, color="black"),
    text=df_map["CLIENTE"],
    customdata=df_map[["HORARIO", "TIPO DE CAMION", "OBSERVACIONES_y"]].values,
    hovertemplate=
        "<b>%{text}</b><br><br>" +
        "🕒 Horario: %{customdata[0]}<br>" +
        "🚚 Tipo Camión: %{customdata[1]}<br>" +
        "📝 Obs: %{customdata[2]}<br>" +
        "<extra></extra>",
    name="Clientes"
))
df_map["OBSERVACIONES_y"] = df_map["OBSERVACIONES_y"].fillna("Sin observaciones")

fig_map.update_layout(
    mapbox_style="carto-positron",
    legend_title="Zona"
)

# ======================
# 🟦 FILA 1
# ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Evolución interanual (2022–2025)")

    # 🔹 FILA 1 (3 columnas)
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cajas Totales", f"{int(total_cf):,}")
    c2.metric("❌ Cajas Rechazadas", f"{int(cf_rech):,}")
    c3.metric("📉 % Rechazo Cajas", f"{rechazo_cf:.2f}%")

    # 🔹 FILA 2 (3 columnas)
    c4, c5, c6 = st.columns(3)
    c4.metric("🚚 Viajes Movilizados", f"{int(viajes_total):,}")
    c5.metric("🚚 Viajes Rechazados", f"{int(viajes_rech):,}")
    c6.metric("📊 % Rechazo Viajes", f"{rechazo_viajes:.2f}%")

    g1, g2 = st.columns(2)
    g1.plotly_chart(fig_cf, use_container_width=True)
    g2.plotly_chart(fig_viajes, use_container_width=True)
    
    st.subheader(" 🏪 Top Clientes - Rechazos")
    st.dataframe(top_clientes, use_container_width=True)

with col2:
    st.subheader("🗺️ Mapa de Distribución")
    st.subheader("Georreferenciación  y características")
    st.plotly_chart(fig_map, use_container_width=True)

# ======================
# 🟩 FILA 2
# ======================
col3, col4 = st.columns(2)

with col3:
    st.subheader("🚚 Rechazos por vehículos")
    st.dataframe(tabla_camion.sort_values("RECHAZO_%", ascending=False).head(10), use_container_width=True)
    st.subheader("🚚 Rechazos por conductores")
    st.dataframe(tabla_chofer.sort_values("RECHAZO_%", ascending=False).head(10), use_container_width=True)

with col4:
    st.subheader("📉 Análisis  por cadenas")
    st.dataframe(tabla_cadena.sort_values("PART_RECHAZO_%", ascending=False).head(10), use_container_width=True)
    st.subheader("📉 Autorización de retorno")
    st.dataframe(tabla_aut.sort_values("PARTICIPACION_%", ascending=False), use_container_width=True)

# ======================
# 🚚 RECHAZO POR TIPO DE VIAJE
# ======================

st.subheader("🚚 Rechazos por tipo de viaje")

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


# ======================
# FUNCIONES
# ======================
def clasificar_motivo(texto):
    texto = str(texto).lower().strip()
    
# 🔴 1. CASOS MUY ESPECÍFICOS (códigos / frases exactas)
    if "ro9" in texto or "r09" in texto or "orden vencida" in texto:
        return "Problemas con la orden de compra"

    elif "orden cerrada" in texto:
        return "Problemas con la orden de compra"

    elif "ra4" in texto or "no se tiene acceso" in texto:
        return "Problemas para descargar"

    elif "ri3" in texto or "no se pudo descargar" in texto:
        return "Problemas para descargar"

    elif "rk1" in texto or "pedido ya recibido" in texto:
        return "Pedido duplicado"

    elif "duplicado" in texto:
        return "Pedido duplicado"

    elif "rh0" in texto or "no pedido" in texto:
        return "Cliente rechaza el pedido"

    elif "no quiere pedido" in texto or "no estaba pedido" in texto:
        return "Cliente rechaza el pedido"

    # 🔴 2. CLIENTE
    elif "rechaza" in texto or "no lo quiere" in texto or "no quiso" in texto or "inventario" in texto:
        return "Cliente rechaza el pedido"

    elif "cerrado" in texto:
        return "Cliente cerrado"

    # 🔴 3. CAPACIDAD / DESCARGA / ACCESO (ANTES que recepción)
    elif "sin lugar" in texto or "sin espacio" in texto:
        return "Sin lugar para descargar"

    elif "deposito colapsado" in texto:
        return "Sin lugar para descargar"

    elif "no puede descargar" in texto:
        return "Problemas para descargar"

    elif "no ingreso" in texto or "no ingresa" in texto or "no puede ingresar" in texto or "arbol" in texto:
        return "Problemas de acceso al cliente"

    # 🔴 4. OC / DOCUMENTACIÓN
    elif "oc" in texto or "orden de compra" in texto:
        return "Problemas con la orden de compra"

    elif "mal facturado" in texto:
        return "Problemas de facturación"

    # 🔴 5. GREMIAL (ANTES de recepción)
    elif "gremio" in texto or "conflicto" in texto or "desarme" in texto or "delegado" in texto:
        return "Problema gremial"

    # 🔴 6. SISTEMA
    elif "sin sistema" in texto:
        return "Cliente sin sistema"

    elif "sistema" in texto:
        return "Cliente sin sistema"

    # 🔴 7. RECEPCIÓN (más abajo para no interferir)
    elif "recepcion" in texto or "recepcionista" in texto:
        return "Problema recepción"

    elif "sin personal" in texto:
        return "Problema recepción"

    # 🔴 8. OPERATIVO
    elif "demora" in texto:
        return "Demoras"

    elif "camiones" in texto:
        return "Demoras"

    elif "bloqueado" in texto or "2hs" in texto:
        return "Problemas para descargar"

    elif "no se entrego" in texto:
        return "Problemas para descargar"

    elif "fuera de horario" in texto:
        return "Fuera de horario"

    elif "turno" in texto:
        return "Problema de turnado"

    elif "zorra" in texto:
        return "Problemas mecanicos"
        
    elif "camion fuera de servicio" in texto:
        return "Problemas mecanicos"
        
    elif "pala" in texto:
        return "Problemas mecanicos"

    # 🔴 9. MERCADERÍA
    elif "mercaderia" in texto or "producto" in texto or "faltante" in texto:
        return "Problema con mercadería"

    elif "pallet" in texto or "carga caida" in texto:
        return "Problema con carga"

    elif "vencimiento" in texto or "fecha corta" in texto or "corto vencimiento" in texto:
        return "Fecha corta / vencimiento"

    elif "fecha" in texto:
        return "Fecha corta / vencimiento"

    elif "devolucion" in texto or "devulucion" in texto:
        return "Problemas con devolución"

    # 🔴 10. CLIMA
    elif "lluvia" in texto or "inundada" in texto:
        return "Problema climático"

    # 🔴 11. LOGÍSTICA
    elif "ruteado" in texto:
        return "Error de ruteo"

    # 🔴 12. GESTIÓN
    elif "comercial" in texto or "ejecutivo" in texto:
        return "Problema comercial"

    # 🔴 13. SIN MOTIVO
    elif "sin motivo" in texto:
        return "Sin motivo cargado"

    # 🔴 AJUSTES FINALES

    elif "turnado" in texto or "no turnado" in texto:
        return "Problema de turnado"
    
    elif "sin acceso" in texto or "no se puede ingresar" in texto or "no podia ingresar" in texto:
        return "Problemas de acceso al cliente"
    
    elif "orden gremial" in texto or "dele" in texto:
        return "Problema gremial"
    
    elif "mal pedido" in texto or "pedido mal elaborado" in texto or "ra2" in texto:
        return "Pedido mal elaborado"
    
    elif "codigo inhabilitado" in texto or "ra0" in texto:
        return "Cliente sin sistema"
    
    elif "no pueden recibir" in texto or "no recibe" in texto:
        return "Problema recepción"
    
    elif "sin luz" in texto:
        return "Problema operativo"
    
    elif "balance" in texto:
        return "Problema operativo"
    
    elif "sin recepcion" in texto:
        return "Problema recepción"
    
    elif "no podia descargar por espacio" in texto:
        return "Sin lugar para descargar"
    
    elif "no se puede ingresar" in texto:
        return "Problemas de acceso al cliente"
    
    elif "mezclado" in texto:
        return "Error de preparación"
    
    elif "no le reciben la totalidad" in texto:
        return "Problema recepción"
    
    elif "sin orden" in texto:
        return "Problemas con la orden de compra"
    
    elif "motor" in texto:
        return "Problemas mecanicos"
    
    elif "clausurado" in texto:
        return "Problema operativo"
    
    elif "sin aut" in texto:
        return "Problema administrativo"
    
    elif "no quiso pedido" in texto:
        return "Cliente rechaza el pedido"
    
    elif "fuera de hora" in texto:
        return "Fuera de horario"
    
    # 🔴 14. RESTO DE CÓDIGOS (AL FINAL SIEMPRE)
    elif "rk" in texto or "ro" in texto or "rj" in texto or "ri" in texto or "rh" in texto:
        return "Pedido mal elaborado"

    else:
        return "Otros"

import unicodedata

def normalizar(texto):
    texto = str(texto).upper().strip()
    
    # 👇 CLAVE: elimina tildes
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    
    texto = re.sub(r"\s+", " ", texto)
    return texto


def clasificar_otros_exacto(texto):
    texto = normalizar(texto)

    mapa = {
        # RECEPCIÓN
    "SIN RECEPCIÒN SE VUELVE SOLO": "Problema recepción",
    "SIN REEPCIONISTA": "Problema recepción",
    "RECIBEN LA MITAD DEL PEDIDO": "Problema recepción",
    "2 VECES SIN RECIBIR": "Problema recepción",

    # ACCESO
    "MARANTON - NO PUEDE INGRSAR": "Problemas de acceso al cliente",
    "NO PUEDE ESTACIONAR DOBLE FILA": "Problemas de acceso al cliente",
    "NO PUEDE ESTACIONAR": "Problemas de acceso al cliente",
    "NO PODIA ESTACIONAR": "Problemas de acceso al cliente",
    "NO PUDO INGRESAR CON EL CAMION": "Problemas de acceso al cliente",
    "AUTO ESTACIONADO EN LA PUERTA": "Problemas de acceso al cliente",
    "AUTO ESTACIONADOS / NO SE PUEDE MANIOBRAR": "Problemas de acceso al cliente",
    "AUTOS MAL ESTACIONADOS": "Problemas de acceso al cliente",
    "LAPOLICIA NO LO DEJO ESTACIONAR": "Problemas de acceso al cliente",
    "MULTA POLICIAL": "Problemas de acceso al cliente",
    "NO PUEDE ESATCIONAR/EENTRADA TAPADA POR AUTO": "Problemas de acceso al cliente",
    "CALLE CORTADA": "Problemas de acceso al cliente",

    # GREMIAL
    "SE VUELVE SIN AVISO/DELAGADO": "Problema gremial",
    "SE VUELVE POR DELGADO/LE PASAN CAMIONETAS ANTES": "Problema gremial",
    "REUNION GREMIAL EN COTO": "Problema gremial",
    "NO DESARMA": "Problema gremial",
    "CORTE GREMIAL DE PER COTO": "Problema gremial",
    "MANIFESTACION/ MUNDIAL": "Problema gremial",
    "EL DELGADO LO DIJO QUE SE VUELVA DESCONFORME CON LA CARGA": "Problema gremial",

    # OPERATIVO
    "SE VOLVIO SOLO": "Problema operativo",
    "SE VUELVE SOLO": "Problema operativo",
    "SE VUELVE DEL MERCADO": "Problema operativo",
    "SE VULVE NO ESPERA , SE ANULO TIENE NUEVO PEDIDO": "Problema operativo",
    "NO ES DIA DE ENTREGA/FIRMAN BOLETA": "Problema operativo",

    # DEMORA
    "DMEORA": "Demoras",
    "SE VUELVE SOLO 01:41 ESPERA": "Demoras",

    # CLIENTE
    "RECHAZO MERCADO": "Cliente rechaza el pedido",
    "NO QUSO PEDIDO/ NORECARGO": "Cliente rechaza el pedido",
    "NO  ESTABA PEDIDO": "Cliente rechaza el pedido",
    "NO QUIERE EL PEDIDO": "Cliente rechaza el pedido",

    # DUPLICADOS
    "PEDIDO YA ENTREGADO": "Pedido duplicado",
    "LO RECIBIO AYER": "Pedido duplicado",
    "ORDEN REPETIDA": "Pedido duplicado",

    # LOGÍSTICA
    "MAL LA RUTA": "Error de ruteo",
    "MERC EN TRANSITO": "Error de ruteo",

    # DESCARGA
    "NO DESCARGA EN DOBLE FILA": "Problemas para descargar",
    "NO DESCARGA DOBLE FILA": "Problemas para descargar",
    "NO DESCARGA EN BICISENDA": "Problemas para descargar",
    "NO PUDO DESCARGAR BICISENDA": "Problemas para descargar",
    "NO QUIZO BAJARLO": "Problemas para descargar",
    "NO PUEDE BAJAR MERC / PECHO DEL CAMION": "Problemas para descargar",

    # MECÁNICO
    "VTV VENCIDA DEL CAMION": "Problemas mecanicos",
    "SE DESCOMPUSO EL CHOFER": "Problemas mecanicos",

    # SISTEMA / CARGA
    "NO SE PUEDE REPLICAR": "Problemas con la orden de compra",
    "NO SE PUDO CARGAR LAS ORDENES": "Problemas con la orden de compra",

    # ADMIN / COMERCIAL
    "SIN BOLETA": "Problemas de facturación",
    "PARA EL LUNES/FIRMAN BOLETA": "Sin lugar para descargar",
    "LO QUIEREN  MAÑANA": "Sin lugar para descargar",
    "ENVIAR MAÑANA (MARANDO)": "Sin lugar para descargar",
    "EL EJEC AVISA Q LO RECIBE DESPUES DE LAS 2": "Problema comercial",

    # PEDIDO / DATOS
    "MAL GRABADO": "Pedido mal elaborado",
    "TIENE MAL GRABADA LA O/C": "Problemas con la orden de compra",

    # MERCADERÍA
    "ESTABA CARGADO AL REVES": "Problema con mercadería",

    # CAPACIDAD
    "FALTA DE LUGAR": "Sin lugar para descargar",

    # SISTEMA CLIENTE
    "SIN SITEMA NO LO RECIBE EL MERCADO": "Cliente sin sistema",

    # ADMIN / DOCUMENTACIÓN
    "R14/ FIRMA Y SELLO DE LA CADENA": "Problema administrativo",
    "SIN BOLETA DE CAMBIOS": "Problemas de facturación",
    "FIRMAN BOLETA/NQPEDIDO": "Problema administrativo",

    # LOGÍSTICA / RUTEO
    "DOS MERCADOS CON MISMA RUTA  Y TR": "Error de ruteo",
    "DISTANCIA ENTRE MERCADO": "Error de ruteo",

    # CLIENTE
    "PEDIDO NO SOLICITADO": "Cliente rechaza el pedido",
    "RECHAZO EL PEDIDO POR QUE ERA UN FORZADA": "Cliente rechaza el pedido",

    # MERCADERÍA
    "CARGA VOLCADA": "Problema con mercaderia",
    "MAL CARGADO": "Problema con mercaderia",

    # OPERATIVO / DESCARGA
    "SIN CIEGO": "Problemas para descargar",
    "NO ENTRA CAMI+ON": "Problemas de acceso al cliente",
    "NO PUDO DESCARGAR": "Problemas para descargar",
    "DOBLE FILA / NO PUEDE BAJAR NI MANIOBRAR": "Problemas para descargar",
    "NO SE PUEDE DESCARGAR AUTOELEVADOR": "Problemas para descargar",

    # GREMIAL
    "REUNION SINDICAL EN EL LUGAR / SE VUELVE": "Problema gremial",
    "MANIFESTACIÓN": "Problema gremial",

    # TIEMPOS / DEMORA
    "30 MIN  DE ESPERA": "Demoras",
    "DEMOA": "Demoras",

    # REPROGRAMACIÓN
    "QUEDA CARGADO SE ENTREGA MAÑANA 15-04": "Sin lugar para descargar",
    "PIDEN ENVIARLO MAÑANA": "Sin lugar para descargar",
    "NO TIENE LUGAR RECIBE EL  MARTES": "Sin lugar para descargar",

    # CAPACIDAD / RECEPCIÓN
    "RECIBE 1 CAMION POR DIA": "Problema recepción",
    "NO  HAY LUGAR NO LE DAN RESPUESTA AL AJECUTIVO": "Sin lugar para descargar",

    # VEHÍCULO / MECÁNICO
    "CAMIÓN DE 10": "Problemas mecanicos",
    "VUELVE A INGRESAR/SIN FRENOS/VUELVE A SALIR": "Problemas mecanicos",

    # DUPLICADOS
    "PEDIDO REPETIDO": "Pedido duplicado",
    "ORDEN RECIBIDA": "Pedido duplicado",

    # ACCESO / ENTORNO
    "OBRAS EN LA CALLE": "Problemas de acceso al cliente",
    "ZONA CERRADA/ INCENDIO AL REDEDORES DEL MARCADO": "Problema climático",

    # OPERATIVO GENERAL
    "SALE DE RECARGA": "Problema operativo",
    
    # ACCESO
    "NO ENTRA EL CAMION": "Problemas de acceso al cliente",
    "TRANSITO NO DEJA ESTACIONAR": "Problemas de acceso al cliente",
    "NO PUEDE LLEGAR AL CD": "Problemas de acceso al cliente",
    "DOBLE FILA": "Problemas de acceso al cliente",
    "RA1  CAMINO ACCIDENTADO": "Problemas de acceso al cliente",

    # CLIENTE
    "NO LO QUISO POR PICKE/SE ENVIO TARDE/FIRMO BOLETA": "Cliente rechaza el pedido",
    "SE RECHAZO POR FALTA SIN CARGO": "Cliente rechaza el pedido",

    # MECÁNICO
    "CAMION DESCOMPUESTO": "Problemas mecanicos",
    "FALLO MECANICO": "Problemas mecanicos",
    "DESCOMPUESTO AYUDANTE": "Problemas mecanicos",

    # GREMIAL
    "R07 DESARMO BOD": "Problema gremial",
    "PERMISO GREMIAL CHOFER - NO RECARGA": "Problema gremial",

    # DUPLICADOS
    "EL PEDIDO LO RECIBIO EL SABADO": "Pedido duplicado",

    # CLIMA / OPERATIVO
    "DARSENA INHUNDADA": "Problema climático",
    "TOMA LA DECISIÓN DE VOLVER PQ LLUEVE/ ESTUVO 40MIN": "Problema climático",

    # LOGÍSTICA / CARGA
    "ORDENES CRUZADAS": "Problemas con la orden de compra",
    "NO CARGADO POR BODEGA SIN CARGO": "Pedido mal elaborado",

    # DESCARGA
    "NO LO PUEDE DESCARGAR POR EL 1ER VIAJE ADELANTE ( PECHO DEL CAMION)": "Problemas para descargar",
    "FIRMA BOLETA NO TIENE CLARCK PARA DESCARGAR EL CAMION": "Problemas para descargar",

    # RECEPCIÓN
    "SE VUELVE PORQUE NO LO ATIENDEN": "Problema recepción",
    "RECIBE HASTA LAS 12:00 HS": "Problema recepción",

    # OC
    "ORDEN COMPRA CERRADA - SOLO ENTREGO 15 CAJAS DEL TOTAL": "Problemas con la orden de compra",

    # OPERATIVO
    "NO RECARGA": "Problemas para descargar",
    "SE VUELVE DEL MERCADO NO ESPERA RESPUESTA": "Problemas para descargar",
    "REPACION DE INGRESO DE MERCADO": "Problemas para descargar",
    "SE LE CAYO 1 PLANCHA Y VOLVIO": "Problemas para descargar",
    "FUE Y VOLVIO - ENTREGO COMO RECARGA": "Problemas para descargar",

    # CAPACIDAD
    "NO TIENE LUGAR - EJEC PIDE  ENVIAR SABADO": "Sin lugar para descargar",
    "FALTA DE ESPACIO": "Sin lugar para descargar",

    # COMERCIAL / GESTIÓN
    "PIDEN ABASTAR": "Problema comercial",

    # SEGURIDAD / CONTROL
    "INSPECCION DEL GOBIERNO": "Problemas para descargar",

    # REPROGRAMACIÓN
    "LO QUIERE MAÑANA": "Cliente rechaza el pedido",

    # CALIDAD / CARGA
    "CHOFER NO QUIERE VOLVER A PASAR POR ESTAR MAL CARGADO EL CAMIION": "Problema con carga"
        
    }

    mapa_normalizado = {normalizar(k): v for k, v in mapa.items()}

    for k, v in mapa_normalizado.items():
        if k in texto:
            return v
    return "Otros"

# ======================
# PROCESAMIENTO (CACHEADO)
# ======================
@st.cache_data
def procesar_datos(df):

        # crear columna auxiliar
    df["texto_clasificar"] = df["OBSERVACIONES_x"]
    
    # completar vacíos con código
    df.loc[
        df["texto_clasificar"].isna() |
        (df["texto_clasificar"].astype(str).str.strip().isin(["", "nan","none","NaN"])),
        "texto_clasificar"
    ] = df["MOTIVO_-_CÓDIGO"]
    
    # clasificar
    df["grupo_motivo"] = df["texto_clasificar"].apply(clasificar_motivo)
    
    mask = df["grupo_motivo"] == "Otros"
    df.loc[mask, "grupo_motivo"] = df.loc[mask, "texto_clasificar"].apply(clasificar_otros_exacto)
    
    return df

df_filtrado = procesar_datos(df_filtrado)
    
# ======================
# FILTRO FALLIDAS
# ======================
df_fallidas = df_filtrado[df_filtrado["ES_FALLIDA"] == True]

# ======================
# RANKING
# ======================
ranking = (
    df_fallidas
    .groupby("grupo_motivo")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="cantidad")
)

ranking["%"] = ranking["cantidad"] / ranking["cantidad"].sum() * 100


# ======================
# KPIs
# ======================
col1, col2 = st.columns(2)

col1.metric("Total rechazos", len(df_fallidas))
col2.metric("Motivo principal", ranking.iloc[0]["grupo_motivo"])

# ======================
# GRÁFICO
# ======================
st.subheader("📊 Ranking de motivos")

fig = px.bar(
    ranking,
    x="cantidad",
    y="grupo_motivo",
    orientation="h",
    text="cantidad"
)
fig.update_traces(marker_color="#6C757D")
fig.update_layout(yaxis={'categoryorder': 'total ascending'})

st.plotly_chart(fig, use_container_width=True)

# ======================
# PARETO
# ======================
st.subheader("📈 Pareto")

ranking = ranking.sort_values(by="cantidad", ascending=False)
ranking["acumulado_%"] = ranking["cantidad"].cumsum() / ranking["cantidad"].sum() * 100

fig2 = go.Figure()

fig2.add_bar(
    x=ranking["grupo_motivo"],
    y=ranking["cantidad"],
    marker_color="#6C757D"
)
fig2.add_scatter(x=ranking["grupo_motivo"], y=ranking["acumulado_%"], yaxis="y2")

fig2.update_layout(
    yaxis=dict(title="Cantidad"),
    yaxis2=dict(title="% acumulado", overlaying="y", side="right"),
    xaxis=dict(tickangle=45)
)

st.plotly_chart(fig2, use_container_width=True)

# ======================
# TABLA
# ======================
st.subheader("📋 Detalle")

st.dataframe(ranking)

# ======================
# 🔥 MAPA DE CALOR DE RECHAZOS
# ======================
motivos = ["Todos"] + sorted(df_filtrado["grupo_motivo"].dropna().unique())

motivo_sel = st.selectbox("Filtrar mapa por motivo", motivos)

st.subheader("🔥 Mapa de calor de rechazos")

df_heat = df_filtrado[
    (df_filtrado["ES_FALLIDA"] == True)
].copy()

if motivo_sel != "Todos":
    df_heat = df_heat[df_heat["grupo_motivo"] == motivo_sel]

df_heat = df_heat.dropna(subset=["LATITUD", "LONGITUD"])

# 🔥 CLUSTERS
df_heat["lat_bin"] = df_heat["LATITUD"].round(2)
df_heat["lon_bin"] = df_heat["LONGITUD"].round(2)

clusters = (
    df_heat
    .groupby(["lat_bin", "lon_bin"])
    .size()
    .reset_index(name="cantidad")
)

fig_heat = go.Figure()

z_values = df_heat.groupby(["LATITUD", "LONGITUD"])["LATITUD"].transform("count")

z_norm = (z_values - z_values.min()) / (z_values.max() - z_values.min())

fig_heat.add_trace(go.Densitymapbox(
    lat=df_heat["LATITUD"],
    lon=df_heat["LONGITUD"],
    z=df_heat.groupby(["LATITUD", "LONGITUD"])["LATITUD"].transform("count"),
    radius=18,
    opacity=0.6,
    colorscale=[
    [0, "green"],
    [0.4, "yellow"],
    [0.7, "orange"],
    [1, "red"]
],
    showscale=True
))

fig_heat.add_trace(go.Scattermapbox(
    lat=df_heat["LATITUD"],
    lon=df_heat["LONGITUD"],
    mode="markers",
    marker=dict(size=4, color="black", opacity=0.5),
    text=df_heat["CLIENTE"],
    customdata=df_heat[["grupo_motivo"]],
    hovertemplate=
        "<b>%{text}</b><br>" +
        "⚠️ %{customdata[0]}" +
        "<extra></extra>"
))

fig_heat.update_layout(
    mapbox_style="carto-positron",
    mapbox=dict(center={"lat": -34.6, "lon": -58.45}, zoom=8),
    height=600,
    margin=dict(l=0, r=0, t=0, b=0)
)

st.plotly_chart(fig_heat, use_container_width=True)

## TOP ZONAS CRITICAS 

st.subheader("📍 Zonas más críticas")

top_zonas = clusters.sort_values("cantidad", ascending=False).head(5)

st.dataframe(top_zonas, use_container_width=True)





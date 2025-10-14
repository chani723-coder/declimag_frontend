
import os
import folium
from folium.plugins import Geocoder, Fullscreen,MiniMap,FloatImage
import streamlit as st
from streamlit_folium import st_folium
from pyproj import Transformer
import utm
import requests
from streamlit_lottie import st_lottie
from pygeomag import GeoMag
from datetime import datetime
from streamlit.components.v1 import html

# --------------------------------------------------------------------
# Config inicial
# --------------------------------------------------------------------
CENTER_START = [-12.6832, -74.8169]
ZOOM_START = 6

if "center_X" not in st.session_state:
    st.session_state["center_X"] = CENTER_START
if "zoom_X" not in st.session_state:
    st.session_state["zoom_X"] = ZOOM_START

st.session_state.setdefault("puntos_X", [])

# --------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------
def crear_mapa_con_plugins(locacion: list[float], zoom_inicio: int) -> folium.Map:
    m = folium.Map(location=locacion, zoom_start=zoom_inicio, control_scale=True)
    google_tiles = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr='&copy; <a href="https://www.google.com/maps">Google Maps</a>',
        name="Google Satélite",
        show=False
    )
    google_tiles.add_to(m)
    Fullscreen(position="topright", title="Expandir", title_cancel="Salir",
               force_separate_button=True).add_to(m)
    m.add_child(folium.LatLngPopup())
    Geocoder().add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    FloatImage("https://www.oceansandrivers.pe/wp-content/uploads/2024/09/O_R_gota-removebg-preview.png", bottom=40, left=90,width='100px').add_to(m)
    return m

def convertidor_utm_geo(zona: int, banda: str, este: float, norte: float):
    crs_origen = {17: "EPSG:32717", 18: "EPSG:32718"}.get(zona, "EPSG:32719")
    transformer = Transformer.from_crs(crs_origen, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(este, norte)
    return lon, lat

def build_fg_punto(row: dict) -> folium.FeatureGroup:
    fg = folium.FeatureGroup(name=row["nombre"], show=True)
    # Icono (con fallback si no existe el archivo)
    icon = None
    icon_path = "./img/iconoUbicacion.png"
    if os.path.exists(icon_path):
        icon = folium.CustomIcon(icon_path, icon_size=(25, 41),
                                 icon_anchor=(12.5, 41), popup_anchor=(0, -30))
    else:
        icon = folium.Icon(icon="info-sign")
    folium.Marker([row["lat"], row["lon"]],
                  popup=folium.Popup(row["popup"]),
                  icon=icon).add_to(fg)
    return fg


def cargar_lottieurl(url:str):
    r=requests.get(url)
    if r.status_code !=200:
        return None
    return r.json()


def give_declimag(row:dict)->str:
    geo_mag = GeoMag()
    latitud = row["lat"] 
    longitud =row["lon"]
    nombre =row["nombre"]   
    altitud = 0  
    fecha=row["fecha"]
    formato = "%Y-%m-%d"
    fecha_objeto = datetime.strptime(fecha,formato)
    tiempo=fecha_objeto.year + fecha_objeto.timetuple().tm_yday/365.0 
    resultado = geo_mag.calculate(glat=latitud, glon=longitud, alt=altitud, time=tiempo)
    st.write(f"{nombre}  :material/arrow_right_alt: Declinación magnética: {resultado.d:.4f} grados")

    
# --------------------------------------------------------------------
# UI
# --------------------------------------------------------------------


st.set_page_config(layout="wide",page_title="Oceans & Rivers - Ingeniería de Recursos Hídricos",page_icon="./img/favicon.ico")

color_fondo="""<style>

MainMenu {
visibility:hidden;}

footer {
visibility:hidden;}

[data-testid="stHeader"] {
visibility:hidden !important;
background:transparent;

}
"""


st.markdown(color_fondo,unsafe_allow_html=True)


with st.sidebar:

    campoMagnetico=cargar_lottieurl("https://lottie.host/e89a2a34-6145-4e84-a420-306f5e3e1c82/uweHazdwLH.json")
    nombre,logo=st.columns([0.7,1],gap="small",vertical_alignment="center")
    nombre.subheader(":green[OR]-declimag v0.0.1")
    with logo:
        st_lottie(campoMagnetico,height=150,speed=8)

    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">

<div style="
    background: rgba(240, 248, 255, 0.6);
    border-left: 5px solid black;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    font-size: 1rem;
    line-height: 1.6;
    color: #0f172a;
">
<h2 style="display: flex; align-items: center; gap: 0.5rem;">
    <span class="material-symbols-outlined" style="font-size: 1.6rem; color: #1E3A8A;">explore</span>
    <b>Cálculo de la Declinación Magnética</b>
</h2>

<p>
Este software calcula la <b>declinación magnética</b>, que es la <b>diferencia angular entre el norte geográfico (verdadero) y el norte magnético</b>.<br>
Este ángulo <b>varía según la ubicación y el tiempo</b>, ya que el campo magnético terrestre cambia constantemente.
</p>

<hr style="border: 1px solid rgba(30,58,138,0.2);">

<h3 style="display: flex; align-items: center; gap: 0.4rem;">
    <span class="material-symbols-outlined" style="font-size: 1.4rem; color: #1E3A8A;">calculate</span>
    <b>Modelos Utilizados</b>
</h3>
<p>El software emplea <b>el modelo WMM2025</b> para realizar los cálculos:</p>

<ul>
<li><span class="material-symbols-outlined" style="vertical-align: middle; color:#1E3A8A;">public</span> 
    <b>WMM (World Magnetic Model):</b> estándar global para la navegación militar y civil. Proporciona <b>predicciones precisas</b> del campo magnético para los próximos cinco años(hasta finales de 2029).</li>

</ul>

<hr style="border: 1px solid rgba(30,58,138,0.2);">

<h3 style="display: flex; align-items: center; gap: 0.4rem;">
    <span class="material-symbols-outlined" style="font-size: 1.4rem; color: #1E3A8A;">settings</span>
    <b>Usos y Aplicaciones</b>
</h3>

<ul>
<li><span class="material-symbols-outlined" style="vertical-align: middle; color:#1E3A8A;">navigation</span> 
    <b>Navegación en cuerpos de agua:</b> Convierte lecturas de brújula magnética en <b>rumbos verdaderos</b> para mapas.</li>
<li><span class="material-symbols-outlined" style="vertical-align: middle; color:#1E3A8A;">flight</span> 
    <b>Aviación:</b> Fundamental para los sistemas de navegación y rumbo en aeronaves.</li>
<li><span class="material-symbols-outlined" style="vertical-align: middle; color:#1E3A8A;">map</span> 
    <b>Cartografía:</b> Permite incorporar la <b>declinación magnética correcta</b> en mapas topográficos.</li>
</ul>
</div>
""", unsafe_allow_html=True)


col1,col2=st.columns([0.4,10])

with col1:

    with st.popover(":material/add_location_alt:"):
        nombre = st.text_input("Nombre del punto", placeholder="pc1, pc2, ...")
        zona = int(st.selectbox("Elija la zona:", ("17", "18", "19")))
        banda = st.selectbox("Elija la banda:", ("M", "L", "K"))
        este = st.number_input("Este (mE)", value=0.0)
        norte = st.number_input("Norte (mN)", value=0.0)
        fecha=st.date_input("Fecha")

        if st.button("Agregar punto", type="primary", use_container_width=True):
            try:
                lon, lat = convertidor_utm_geo(zona, banda, este, norte)
                if not nombre:
                    st.warning("Asigna un nombre al punto antes de agregarlo.")
                else:
                    st.session_state["puntos_X"].append(
                        {"nombre": nombre, "lat": lat, "lon": lon, "popup": nombre,"fecha":str(fecha)}
                    )
                    st.success(f"Agregado: {nombre}")
            except Exception as e:
                st.error(f"No se pudo convertir UTM→WGS84: {e}")

    with st.popover(":material/delete_forever:"):
        nombres_existentes = [r["nombre"] for r in st.session_state.get("puntos_X", [])]
        PUNTO = st.selectbox(
            "Seleccione punto para borrar",
            nombres_existentes if nombres_existentes else ["(sin puntos)"],
        )

        if st.button("Borrar punto", use_container_width=True, disabled=not nombres_existentes):
            st.session_state["puntos_X"] = [r for r in st.session_state["puntos_X"] if r["nombre"] != PUNTO]
            st.info(f"Borrado: {PUNTO}")

with col2:

    with st.container(height=600):
        m = crear_mapa_con_plugins(CENTER_START, ZOOM_START)
        layers = [build_fg_punto(row) for row in st.session_state.get("puntos_X", [])]
        a = st_folium(
            m,
            center=st.session_state["center_X"],
            zoom=st.session_state["zoom_X"],
            key="map_main",  # key fijo: sin parpadeo
            feature_group_to_add=layers,
            height=560,
            width=800,
            use_container_width=True,
            layer_control=folium.LayerControl(collapsed=False, position="topright"),
            returned_objects=["last_clicked"],
        )

    iz,centro,der=st.columns(3)

    with der:
        if a.get("last_clicked"):
            E, N, Z, B = utm.from_latlon(a["last_clicked"]["lat"], a["last_clicked"]["lng"])
            st.caption(f":blue[**Rastreo de coordenadas: {round(E,2)} mE | {round(N,2)} mN | {Z}{B}**]")


    with st.expander("Vea la declinación :material/explore:",expanded=True):
        for i in st.session_state.get("puntos_X", []):
            give_declimag(i)

    st.code("""Powered by: Copyright © 2025 Oceans & Rivers IT""")


html("""
<script>
window.top.document.querySelectorAll(`[href*="streamlit.io"]`).forEach(e => e.setAttribute("style", "display: none;"));
</script>
     """)
import pandas as pd
import plotly.express as px
import streamlit as st

URL = st.secrets["https://docs.google.com/spreadsheets/d/e/2PACX-1vTfx9MDCxIQjOM00aL90GD9F7SzYP23Yq-mwljbBeXfaL-TyZd0-zuz4hBNgBO6noOIn80GzNHGEjrT/pubhtml?gid=28556863&single=true"]  

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Tablero de exámenes privados",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .stApp { background-color: #f8f9fa; }
    .kpi-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        text-align: center;
        padding-bottom: 12px;
        margin-bottom: 10px;
        border: 1px solid #e9ecef;
    }
    .kpi-header {
        color: white;
        font-weight: 600;
        padding: 8px;
        border-radius: 8px 8px 0 0;
        font-size: 15px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        color: #1e293b;
        margin-top: 8px;
    }
    .kpi-sub {
        font-size: 12px;
        color: #64748b;
    }
    .chart-box {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. CONFIGURACIÓN DE COLUMNAS DE TU EXCEL
# ==========================================
# Ajusta estos nombres si en tu Excel están escritos diferente:
ARCHIVO_EXCEL = "datosPriv.xlsx"
COL_CARRERA = "Carrera"
COL_TIPO_EXAMEN = "Examen"
COL_CARNET = "Reg. Académico"
COL_FECHA = "Fecha solicitada"
# Lista de columnas donde aparecen los examinadores de la terna:
COLS_EXAMINADORES = [
    "Examinador 1",
    "Examinador 2",
    "Examinador 3",
    "Examinador 4",
]


# ==========================================
# 3. CARGA Y LIMPIEZA DE DATOS
# ==========================================
def cargar_datos():
    df = pd.read_excel(ARCHIVO_EXCEL)
    df.columns = df.columns.str.strip()  # Limpia espacios extra en encabezados

    # Extraer Año de ingreso de los primeros 4 dígitos del carnet
    df["Año_Ingreso"] = (
        df[COL_CARNET].astype(str).str.strip().str[:4]
    )
    # Limpiar posibles decimales si Excel leyó el carnet como número (ej. 201901.0)
    df["Año_Ingreso"] = df["Año_Ingreso"].str.replace(".0", "", regex=False)

    # Procesar fechas para Mes y Semana (lunes de cada semana)
    df["Fecha_dt"] = pd.to_datetime(df[COL_FECHA], errors="coerce")

    meses_es = {
        1: "01 - Enero",
        2: "02 - Febrero",
        3: "03 - Marzo",
        4: "04 - Abril",
        5: "05 - Mayo",
        6: "06 - Junio",
        7: "07 - Julio",
        8: "08 - Agosto",
        9: "09 - Septiembre",
        10: "10 - Octubre",
        11: "11 - Noviembre",
        12: "12 - Diciembre",
    }
    df["Mes_Solicitado"] = df["Fecha_dt"].dt.month.map(meses_es)

    # Calcular el lunes de cada semana (formato día/mes)
    lunes_semana = df["Fecha_dt"] - pd.to_timedelta(
        df["Fecha_dt"].dt.weekday, unit="D"
    )
    df["Semana_Lunes"] = lunes_semana.dt.strftime("%d/%m")
    df["Semana_Orden"] = lunes_semana  # Para ordenar cronológicamente

    return df


try:
    df_raw = cargar_datos()
except Exception as e:
    st.error(
        f"Error al leer '{ARCHIVO_EXCEL}'. Verifica que esté en la misma carpeta y tenga las columnas correctas. Detalle: {e}"
    )
    st.stop()

# ==========================================
# 4. ENCABEZADO Y BARRA DE FILTROS
# ==========================================
col_logo, col_t1, col_t2 = st.columns([1.8, 3.2, 1])

with col_logo:
    st.image("logo.png", width="stretch")

with col_t1:
    st.title("Tablero de exámenes privados")

with col_t2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar Excel", width="stretch"):
        st.rerun()


# Inicializar estado de filtros para el botón "Quitar filtros"
if "f_carrera" not in st.session_state:
    st.session_state.f_carrera = "Todas"
if "f_examen" not in st.session_state:
    st.session_state.f_examen = "Todos"
if "f_mes" not in st.session_state:
    st.session_state.f_mes = "Todos"


def limpiar_filtros():
    st.session_state.f_carrera = "Todas"
    st.session_state.f_examen = "Todos"
    st.session_state.f_mes = "Todos"


f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
with f1:
    opciones_carrera = ["Todas"] + sorted(
        df_raw[COL_CARRERA].dropna().unique().tolist()
    )
    sel_carrera = st.selectbox("Carrera", opciones_carrera, key="f_carrera")
with f2:
    opciones_examen = ["Todos"] + sorted(
        df_raw[COL_TIPO_EXAMEN].dropna().unique().tolist()
    )
    sel_examen = st.selectbox(
        "Tipo de examen", opciones_examen, key="f_examen"
    )
with f3:
    opciones_mes = ["Todos"] + sorted(
        df_raw["Mes_Solicitado"].dropna().unique().tolist()
    )
    sel_mes = st.selectbox("Mes solicitado", opciones_mes, key="f_mes")
with f4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button(
        "Quitar filtros", on_click=limpiar_filtros, use_container_width=True
    )

# Aplicar filtros al DataFrame
df = df_raw.copy()
if sel_carrera != "Todas":
    df = df[df[COL_CARRERA] == sel_carrera]
if sel_examen != "Todos":
    df = df[df[COL_TIPO_EXAMEN] == sel_examen]
if sel_mes != "Todos":
    df = df[df["Mes_Solicitado"] == sel_mes]

st.divider()

# ==========================================
# 5. FILA SUPERIOR: TARJETAS KPI POR CARRERA
# ==========================================
conteo_carreras = df[COL_CARRERA].value_counts()
colores = ["#1d4ed8", "#d97706", "#059669", "#7c3aed", "#0f172a"]
cols_kpi = st.columns(min(len(conteo_carreras) + 1, 5))

with cols_kpi[0]:
    st.markdown(
        f"""
    <div class="kpi-card">
        <div class="kpi-header" style="background-color: #334155;">Total Exámenes</div>
        <div class="kpi-value">{len(df)}</div>
        <div class="kpi-sub">100% de la selección</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

for i, (carr, cant) in enumerate(conteo_carreras.items()):
    if i + 1 < len(cols_kpi):
        pct = (cant / len(df) * 100) if len(df) > 0 else 0
        color = colores[i % len(colores)]
        with cols_kpi[i + 1]:
            st.markdown(
                f"""
            <div class="kpi-card">
                <div class="kpi-header" style="background-color: {color};">{carr}</div>
                <div class="kpi-value">{cant}</div>
                <div class="kpi-sub">{pct:.1f}% del total</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

# ==========================================
# 6. FILA 1 DE GRÁFICAS: CARRERA Y TIPO DE EXAMEN
# ==========================================
g1, g2 = st.columns(2)

with g1:
    st.subheader("Alumnos por carrera")
    st.caption("Cantidad y porcentaje del total.")
    df_carr = df[COL_CARRERA].value_counts().reset_index()
    df_carr.columns = ["Carrera", "Cantidad"]
    fig1 = px.pie(
        df_carr,
        names="Carrera",
        values="Cantidad",
        hole=0.55,
        color_discrete_sequence=colores,
    )
    fig1.update_traces(textinfo="value+percent", textposition="outside")
    fig1.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader("Tipo de examen por carrera")
    st.caption(
        "Examen general privado frente a examen general privado de EPS."
    )
    df_tipo = (
        df.groupby([COL_CARRERA, COL_TIPO_EXAMEN])
        .size()
        .reset_index(name="Cantidad")
    )
    fig2 = px.bar(
        df_tipo,
        x=COL_CARRERA,
        y="Cantidad",
        color=COL_TIPO_EXAMEN,
        barmode="group",
        text_auto=True,
        template="plotly_white",
    )
    fig2.update_layout(
        height=340,
        xaxis_title="",
        yaxis_title="Alumnos",
        legend_title="",
        margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# 7. FILA 2 DE GRÁFICAS: AÑO DE INGRESO (EXCLUYENDO "90")
# ==========================================
st.subheader("Alumnos por año de ingreso")
st.caption("Año en que ingresó cada alumno, separado por carrera.")

# Filtrar el error de captura "90" (o años que empiecen con 90)
df_ingreso = df[~df["Año_Ingreso"].str.startswith("90", na=False)]
df_anio = (
    df_ingreso.groupby(["Año_Ingreso", COL_CARRERA])
    .size()
    .reset_index(name="Cantidad")
)
df_anio = df_anio.sort_values("Año_Ingreso")

fig3 = px.bar(
    df_anio,
    x="Año_Ingreso",
    y="Cantidad",
    color=COL_CARRERA,
    text_auto=True,
    template="plotly_white",
    color_discrete_sequence=colores,
)
fig3.update_layout(
    height=320,
    xaxis_title="Año de ingreso",
    yaxis_title="Cantidad de alumnos",
    legend_title="Carrera",
    margin=dict(t=20, b=20, l=20, r=20),
)
st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# 8. FILA 3 DE GRÁFICAS: MES Y SEMANA
# ==========================================
g3, g4 = st.columns(2)

with g3:
    st.subheader("Exámenes solicitados por mes")
    st.caption("Cantidad de alumnos según el mes de la fecha solicitada.")
    df_mes = df["Mes_Solicitado"].value_counts().reset_index()
    df_mes.columns = ["Mes", "Cantidad"]
    df_mes = df_mes.sort_values("Mes")
    fig4 = px.bar(
        df_mes,
        x="Mes",
        y="Cantidad",
        text_auto=True,
        template="plotly_white",
        color_discrete_sequence=["#1d4ed8"],
    )
    fig4.update_layout(
        height=320,
        xaxis_title="",
        yaxis_title="Exámenes",
        margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig4, use_container_width=True)


with g4:
    st.subheader("Exámenes solicitados por semana")
    st.caption(
        "Cada punto es una semana, identificada por la fecha de su lunes (día/mes)."
    )
    df_sem = (
        df.dropna(subset=["Semana_Orden"])
        .groupby(["Semana_Orden", "Semana_Lunes"])
        .size()
        .reset_index(name="Cantidad")
    )
    df_sem = df_sem.sort_values("Semana_Orden")
    fig5 = px.line(
        df_sem,
        x="Semana_Lunes",
        y="Cantidad",
        markers=True,
        text="Cantidad",
        template="plotly_white",
        color_discrete_sequence=["#d97706"],
    )
    fig5.update_traces(textposition="top center")
    fig5.update_layout(
        height=320,
        xaxis_title="Lunes de la semana",
        yaxis_title="Exámenes",
        margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig5, use_container_width=True)

# ==========================================
# 9. FILA 4: PARTICIPACIONES POR EXAMINADOR
# ==========================================
st.subheader("Participaciones por examinador")
st.caption(
    "Número de exámenes en los que cada docente integra la terna de examinadores."
)

cols_existentes = [c for c in COLS_EXAMINADORES if c in df.columns]

if cols_existentes:
    serie_examinadores = df[cols_existentes].melt(value_name="Examinador")[
        "Examinador"
    ]
    serie_examinadores = serie_examinadores.dropna().astype(str).str.strip()
    serie_examinadores = serie_examinadores[
        ~serie_examinadores.isin(["", "nan", "None", "0", "-"])
    ]

    df_exam = serie_examinadores.value_counts().reset_index()
    df_exam.columns = ["Examinador", "Participaciones"]
    df_exam = df_exam.sort_values("Participaciones", ascending=True)

    fig6 = px.bar(
        df_exam,
        x="Participaciones",
        y="Examinador",
        orientation="h",
        text_auto=True,
        template="plotly_white",
        color_discrete_sequence=["#059669"],
    )
    fig6.update_layout(
        height=max(300, len(df_exam) * 28),
        xaxis_title="Cantidad de ternas",
        yaxis_title="",
        margin=dict(t=20, b=20, l=20, r=20),
    )
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info(
        "Ajusta los nombres en 'COLS_EXAMINADORES' al inicio del código para mostrar la carga docente."
    )

# ==========================================
# 10. NOTA DE PRIVACIDAD AL PIE
# ==========================================
st.divider()
st.caption(
    "🔒 Este tablero solo usa datos agrupados: no incluye nombres de estudiantes, CUI ni registro académico. El año de ingreso “90” del archivo parece un error de captura y no se muestra en el gráfico de ingreso."
)

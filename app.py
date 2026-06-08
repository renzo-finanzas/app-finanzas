import streamlit as st
import gspread
from datetime import datetime
import pytz

st.set_page_config(page_title="Ingeniería de Vida - Finanzas", layout="centered")
st.title("💸 Control de Flujo")

@st.cache_resource
def init_connection():
    cred_dict = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(cred_dict)
    return gc

client = init_connection()

try:
    # REEMPLAZA ESTO CON EL ID REAL DE TU EXCEL
    spreadsheet = client.open_by_key("17npLm-020o05haLr6ieTIMB5mBOuz4JJh7Sep5Z30JA")
    sheet_registros = spreadsheet.worksheet("Hoja 1")
    sheet_maestro = spreadsheet.worksheet("Maestro_Categorias")
except Exception as e:
    st.error("Error conectando a la base de datos.")
    st.stop()

# 1. Leer la matriz dinámica
registros_maestro = sheet_maestro.get_all_records()

# 2. Extraer opciones únicas para los menús
macros = list(dict.fromkeys([str(r["Macro"]).strip() for r in registros_maestro if str(r["Macro"]).strip()]))
medios_pago = list(dict.fromkeys([str(r.get("Medio_Pago", "")).strip() for r in registros_maestro if str(r.get("Medio_Pago", "")).strip()]))

# 3. Interfaz gráfica (Filtros en cascada)
macro_sel = st.selectbox("1. Bolsillo (Macro)", macros)

categorias = list(dict.fromkeys([str(r["Categoria"]).strip() for r in registros_maestro if str(r["Macro"]).strip() == macro_sel and str(r["Categoria"]).strip()]))
cat_sel = st.selectbox("2. Destino (Categoría)", categorias)

conceptos = list(dict.fromkeys([str(r["Concepto"]).strip() for r in registros_maestro if str(r["Macro"]).strip() == macro_sel and str(r["Categoria"]).strip() == cat_sel and str(r["Concepto"]).strip()]))
concepto_sel = st.selectbox("3. Naturaleza (Concepto)", conceptos)

# --- BUSQUEDA DINÁMICA DE LA REFERENCIA ---
referencia_visual = ""
for r in registros_maestro:
    if str(r.get("Macro", "")).strip() == macro_sel and \
       str(r.get("Categoria", "")).strip() == cat_sel and \
       str(r.get("Concepto", "")).strip() == concepto_sel:
        referencia_visual = str(r.get("Referencia (Ayuda / Glosa)", "")).strip()
        break

# Campo informativo deshabilitado (Solo lectura, cambia según el concepto)
st.text_input("Guía de Asignación (Referencia)", value=referencia_visual, disabled=True)
# ------------------------------------------

if medios_pago:
    medio_sel = st.selectbox("4. Cuenta / Medio de Pago", medios_pago)
else:
    st.error("No se encontraron Medios de Pago en la columna E de tu Excel.")
    st.stop()

# Ajuste de etiqueta solicitado
glosa = st.text_input("Detalle Extra - Opcional")
monto = st.number_input("Monto (S/)", min_value=0.0, step=1.0, format="%.2f")

# 4. Registro con estructura optimizada (7 columnas netas, sin redundancia de Tipo)
if st.button("Registrar Movimiento"):
    if monto > 0:
        zona_horaria = pytz.timezone("America/Lima")
        fecha_actual = datetime.now(zona_horaria).strftime("%Y-%m-%d %H:%M:%S")
        
        fila_nueva = [fecha_actual, macro_sel, cat_sel, concepto_sel, medio_sel, glosa, monto]
        sheet_registros.append_row(fila_nueva)
        st.success(f"✅ S/ {monto} registrado desde {medio_sel}.")
    else:
        st.error("⚠️ El monto debe ser mayor a 0.")

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
    sheet_registros = spreadsheet.worksheet("Registros")
    sheet_maestro = spreadsheet.worksheet("Maestro_Categorias")
except Exception as e:
    st.error("Error conectando a la base de datos.")
    st.stop()

# 1. Leer matrices
registros_maestro = sheet_maestro.get_all_records()
medios_pago = list(dict.fromkeys([str(r.get("Medio_Pago", "")).strip() for r in registros_maestro if str(r.get("Medio_Pago", "")).strip()]))

# --- INTERRUPTOR DE ARQUITECTURA ---
tipo_operacion = st.radio("Tipo de Movimiento", ["Flujo Regular", "Transferencia Interna"], horizontal=True)
st.markdown("---")

# 2. LÓGICA DE FLUJO REGULAR (INGRESOS/GASTOS)
if tipo_operacion == "Flujo Regular":
    macros = list(dict.fromkeys([str(r["Macro"]).strip() for r in registros_maestro if str(r["Macro"]).strip()]))
    macro_sel = st.selectbox("1. Bolsillo (Macro)", macros)

    categorias = list(dict.fromkeys([str(r["Categoria"]).strip() for r in registros_maestro if str(r["Macro"]).strip() == macro_sel and str(r["Categoria"]).strip()]))
    cat_sel = st.selectbox("2. Destino (Categoría)", categorias)

    conceptos = list(dict.fromkeys([str(r["Concepto"]).strip() for r in registros_maestro if str(r["Macro"]).strip() == macro_sel and str(r["Categoria"]).strip() == cat_sel and str(r["Concepto"]).strip()]))
    concepto_sel = st.selectbox("3. Naturaleza (Concepto)", conceptos)

    referencia_visual = ""
    for r in registros_maestro:
        if str(r.get("Macro", "")).strip() == macro_sel and str(r.get("Categoria", "")).strip() == cat_sel and str(r.get("Concepto", "")).strip() == concepto_sel:
            referencia_visual = str(r.get("Referencia (Ayuda / Glosa)", "")).strip()
            break
    st.text_input("Guía de Asignación", value=referencia_visual, disabled=True)

    medio_sel = st.selectbox("4. Cuenta / Medio de Pago", medios_pago)
    glosa = st.text_input("Detalle Extra - Opcional")
    monto = st.number_input("Monto (S/)", min_value=0.0, step=1.0, format="%.2f")

    if st.button("Registrar Movimiento"):
        if monto > 0:
            zona_horaria = pytz.timezone("America/Lima")
            fecha_actual = datetime.now(zona_horaria).strftime("%Y-%m-%d %H:%M:%S")
            # Signos: Ingreso(+) o Movimiento Interno(+) / Otros(-)
            monto_final = monto if (macro_sel.startswith("1.") or macro_sel.startswith("0.")) else -monto
            fila = [fecha_actual, macro_sel, cat_sel, concepto_sel, medio_sel, glosa, monto_final]
            sheet_registros.append_row(fila)
            st.success(f"✅ S/ {monto_final} registrado.")

# 3. LÓGICA DE TRANSFERENCIA (PARTIDA DOBLE)
else:
    origen_sel = st.selectbox("Cuenta Origen (Sale dinero)", medios_pago)
    destino_sel = st.selectbox("Cuenta Destino (Entra dinero)", medios_pago)
    glosa = st.text_input("Motivo")
    monto = st.number_input("Monto (S/)", min_value=0.0, step=1.0, format="%.2f")

    if st.button("Ejecutar Transferencia"):
        if monto > 0 and origen_sel != destino_sel:
            zona_horaria = pytz.timezone("America/Lima")
            fecha_actual = datetime.now(zona_horaria).strftime("%Y-%m-%d %H:%M:%S")
            fila_salida = [fecha_actual, "0. Movimiento Interno", "Transferencia", f"Hacia {destino_sel}", origen_sel, glosa, -monto]
            fila_ingreso = [fecha_actual, "0. Movimiento Interno", "Transferencia", f"Desde {origen_sel}", destino_sel, glosa, monto]
            sheet_registros.append_rows([fila_salida, fila_ingreso])
            st.success(f"✅ Transferencia: -S/ {monto} a +S/ {monto}")

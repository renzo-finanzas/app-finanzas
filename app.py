import streamlit as st
import gspread
from datetime import datetime
import pytz

# Configuración básica de la pantalla del celular
st.set_page_config(page_title="Ingeniería de Vida - Finanzas", layout="centered")
st.title("💸 Control de Flujo")

# Conexión segura a la base de datos (Google Sheets)
@st.cache_resource
def init_connection():
    # Extraemos la llave desde la bóveda de Streamlit (la configuraremos luego)
    cred_dict = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(cred_dict)
    return gc

client = init_connection()

# Conectar con tu archivo de Excel exacto
try:
    sheet = client.open("BD_Finanzas_Renzo").sheet1
except Exception as e:
    st.error("Error conectando a la base de datos. Verifica el nombre del archivo.")

# Maestro de Categorías (Nivel 2 y Nivel 3)
categorias = {
    "1. Ingresos": ["Sueldo fijo", "Utilidades / Bonos", "Reembolsos operativos", "Ventas de segunda mano / Otros"],
    "2. Ahorro e Inversión (Transferencias)": ["Fondo Inicial Departamento", "Fondo Auto (2027)", "Fondo Terreno (Tingo María)", "Fondo Proyecto Bebé (2030)", "Fondo de Emergencia"],
    "3. Vivienda e Infraestructura": ["Alquiler / Mantenimiento", "Servicios (Luz, Agua, Internet)", "Plan Celular", "Proyectos DIY / Materiales para muebles", "Artículos de limpieza / Hogar"],
    "4. Alimentación y Despensa": ["Supermercado / Mercado (Comida en casa)", "Suplementos deportivos (Proteína, etc.)"],
    "5. Salud y Desarrollo": ["Membresía de Gimnasio", "Educación (Cursos Python, Inglés)", "Libros (Manuales técnicos, Literatura clásica)", "Salud (Consultas, farmacia, seguro)"],
    "6. Estilo de Vida y Ocio": ["Entretenimiento (Juegos PS5, Mobile Legends)", "Suscripciones (PS Plus, Streaming, Apps)", "Alimentación fuera (Antojos, delivery, cafés)", "Cuidado personal (Barbería, aseo)", "Ropa y Calzado"],
    "7. Pareja": ["Citas y salidas", "Regalos y detalles", "Apoyo logístico / Universitario"],
    "8. Familia": ["Apoyo mensual a padres", "Regalos / Cumpleaños / Eventos familiares"],
    "9. Transporte": ["Transporte público regular", "Taxis (Aplicativos)"],
    "10. Trabajo (Viáticos y Rendiciones)": ["Movilidad a CEDIs (Lima y Provincia)", "Alimentación en ruta", "Hospedaje de trabajo"],
    "11. Obligaciones Financieras": ["Comisiones bancarias", "Intereses de tarjetas de crédito (Solo si aplica)"]
}

# Diseño del formulario en pantalla
with st.form("registro_form"):
    categoria_sel = st.selectbox("Categoría Macro (Flujo)", list(categorias.keys()))
    subcategoria_sel = st.selectbox("Detalle 1 (Subcategoría específica)", categorias[categoria_sel])
    glosa = st.text_input("Detalle 2 (Glosa / Contexto) - Solo si es necesario")
    monto = st.number_input("Monto (S/)", min_value=0.0, step=1.0, format="%.2f")
    
    submit_button = st.form_submit_button(label="Registrar Movimiento")

# Lógica de inserción de datos
if submit_button:
    if monto > 0:
        # Determinar el tipo de flujo automáticamente para no ensuciar el reporte
        if categoria_sel.startswith("1."):
            tipo = "Ingreso"
        elif categoria_sel.startswith("2."):
            tipo = "Transferencia"
        else:
            tipo = "Salida"
        
        # Ajuste horario
        zona_horaria = pytz.timezone("America/Lima")
        fecha_actual = datetime.now(zona_horaria).strftime("%Y-%m-%d %H:%M:%S")
        
        # Estructurar fila y enviarla a Sheets
        fila_nueva = [fecha_actual, tipo, categoria_sel, subcategoria_sel, glosa, monto]
        sheet.append_row(fila_nueva)
        st.success(f"✅ S/ {monto} registrado exitosamente como {tipo}.")
    else:
        st.error("⚠️ El monto debe ser mayor a 0.")

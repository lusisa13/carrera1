import json
import os
import io
import pandas as pd
import streamlit as st
from fpdf import FPDF

# Filepath del archivo de respaldo local
ARCHIVO_LOCAL = "datos_caja_enduro.json"

# Configuración de la página
st.set_page_config(page_title="Sistema de Caja - Enduro", page_icon="🏎️", layout="wide")

# Lista general de categorías
CATEGORIAS = [
    "Sénior A", "Senior B", "Júnior A", "Junior B", "Master A", "Master B", 
    "Master C", "Master D", "Master Principiantes", "Master Leyenda", 
    "Principiantes A1", "Principiantes A2", "Principiantes B", "Sub17", 
    "Infantiles A", "Infantiles B", "Mini", "Damas", "Otra"
]

# ==========================================
# INICIALIZACIÓN DEL ESTADO (SESSION STATE)
# ==========================================
if "pilotos" not in st.session_state:
    st.session_state.pilotos = []

if "gastos" not in st.session_state:
    st.session_state.gastos = []

if "historial" not in st.session_state:
    st.session_state.historial = []

# Cargar datos guardados previamente en el disco al iniciar la aplicación
if os.path.exists(ARCHIVO_LOCAL) and "cargado" not in st.session_state:
    try:
        with open(ARCHIVO_LOCAL, "r", encoding="utf-8") as f:
            datos_guardados = json.load(f)
            st.session_state.pilotos = datos_guardados.get("pilotos", [])
            st.session_state.gastos = datos_guardados.get("gastos", [])
            st.session_state.historial = datos_guardados.get("historial", [])
        st.session_state.cargado = True
    except Exception:
        pass


def guardar_autoguardado():
    """Guarda los datos en el archivo local del sistema."""
    datos = {
        "pilotos": st.session_state.pilotos,
        "gastos": st.session_state.gastos,
        "historial": st.session_state.historial
    }
    with open(ARCHIVO_LOCAL, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)


# ==========================================
# FUNCIONES DE IMPORTACIÓN Y EXPORTACIÓN MULTIFORMATO
# ==========================================
def exportar_excel():
    """Genera un archivo Excel (.xlsx) con pestañas separadas para Pilotos, Gastos e Historial."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pilotos = pd.DataFrame(st.session_state.pilotos) if st.session_state.pilotos else pd.DataFrame(columns=["nombre", "placa", "categoria", "monto", "medio", "destinatario", "situacion"])
        df_gastos = pd.DataFrame(st.session_state.gastos) if st.session_state.gastos else pd.DataFrame(columns=["descripcion", "monto"])
        df_historial = pd.DataFrame({"log": st.session_state.historial}) if st.session_state.historial else pd.DataFrame(columns=["log"])
        
        df_pilotos.to_excel(writer, sheet_name="Pilotos", index=False)
        df_gastos.to_excel(writer, sheet_name="Gastos", index=False)
        df_historial.to_excel(writer, sheet_name="Historial", index=False)
    return output.getvalue()


def exportar_csv_pilotos():
    """Genera un archivo CSV codificado en UTF-8 con la lista de pilotos."""
    df_pilotos = pd.DataFrame(st.session_state.pilotos) if st.session_state.pilotos else pd.DataFrame(columns=["nombre", "placa", "categoria", "monto", "medio", "destinatario", "situacion"])
    return df_pilotos.to_csv(index=False).encode('utf-8-sig')


def procesar_importacion(archivo_subido):
    """Detecta la extensión del archivo (JSON, Excel o CSV) y restaura la base de datos."""
    nombre = archivo_subido.name.lower()
    
    if nombre.endswith(".json"):
        datos = json.load(archivo_subido)
        st.session_state.pilotos = datos.get("pilotos", [])
        st.session_state.gastos = datos.get("gastos", [])
        st.session_state.historial = datos.get("historial", [])

    elif nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        xls = pd.read_excel(archivo_subido, sheet_name=None)
        if "Pilotos" in xls:
            st.session_state.pilotos = xls["Pilotos"].fillna("-").to_dict(orient="records")
        elif len(xls.keys()) > 0:
            # Si no tiene pestañas nombradas, toma la primera como pilotos
            primera_hoja = list(xls.keys())[0]
            st.session_state.pilotos = xls[primera_hoja].fillna("-").to_dict(orient="records")
            
        if "Gastos" in xls:
            st.session_state.gastos = xls["Gastos"].fillna("").to_dict(orient="records")
        if "Historial" in xls and "log" in xls["Historial"]:
            st.session_state.historial = xls["Historial"]["log"].dropna().tolist()

    elif nombre.endswith(".csv"):
        df = pd.read_csv(archivo_subido).fillna("-")
        st.session_state.pilotos = df.to_dict(orient="records")
        
    guardar_autoguardado()


# Funciones auxiliares
def resolver_situacion(opcion_sit, dia_mes=None, monto_custom=0.0, medio_op="Efectivo", dest_op="Mercedes", tarifa_manual=110000.0):
    if opcion_sit == "Pagó Tarifa":
        if dia_mes is not None:
            if dia_mes <= 12:
                monto = 110000.0
            elif dia_mes <= 17:
                monto = 130000.0
            else:
                monto = 140000.0
        else:
            monto = float(tarifa_manual)
        return monto, medio_op, dest_op, "Pagado"

    elif opcion_sit == "Solo Seguro":
        return 35000.0, medio_op, dest_op, "Solo Seguro"

    elif opcion_sit == "Monto Personalizado":
        return float(monto_custom), medio_op, dest_op, "Personalizado"

    elif opcion_sit == "Indistinto / Nulo":
        return 0.0, "Ninguno", "Ninguno", "Indistinto/Nulo"

    elif opcion_sit == "Adeuda":
        return 0.0, "Ninguno", "Ninguno", "Adeuda"

    else: # Gratis
        return 0.0, "Ninguno", "Ninguno", "Gratis"


def limpiar_texto(texto):
    """Limpia caracteres especiales para compatibilidad con FPDF."""
    if not isinstance(texto, str):
        texto = str(texto)
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', '°': 'o'
    }
    for orig, repl in replacements.items():
        texto = texto.replace(orig, repl)
    return texto.encode('latin-1', 'replace').decode('latin-1')


def generar_pdf(pilotos, tipo_reporte):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado principal
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, limpiar_texto("Sistema de Caja - Enduro"), ln=True, align="C")
    pdf.set_font("Helvetica", "I", 11)

    # ----------------------------------------------------
    # REPORTE COMPLETO
    # ----------------------------------------------------
    if tipo_reporte == "Completo":
        pdf.cell(0, 8, limpiar_texto("Reporte Completo de Pilotos"), ln=True, align="C")
        pdf.ln(5)
        
        # Ordenar por Categoría respetando el orden oficial
        pilotos_ordenados = sorted(
            pilotos, 
            key=lambda x: CATEGORIAS.index(x["categoria"]) if x.get("categoria") in CATEGORIAS else 999
        )

        widths = [10, 45, 20, 30, 25, 20, 20, 20]
        headers = ["#", "Nombre", "Placa", "Categoria", "Situacion", "Monto", "Medio", "Destino"]

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(220, 220, 220)
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 8, limpiar_texto(h), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for idx, p in enumerate(pilotos_ordenados, 1):
            row = [
                str(idx),
                p["nombre"],
                p.get("placa", "-"),
                p.get("categoria", "-"),
                p["situacion"],
                f"${p['monto']:,.0f}",
                p["medio"],
                p["destinatario"]
            ]
            for i, val in enumerate(row):
                align = "C" if i in [0, 2] else ("R" if i == 5 else "L")
                pdf.cell(widths[i], 7, limpiar_texto(val), border=1, align=align)
            pdf.ln()

    # ----------------------------------------------------
    # REPORTE: NOMBRE COMPLETO CON PLACA Y CATEGORÍA (AGRUPADO)
    # ----------------------------------------------------
    elif tipo_reporte == "Nombre completo con placa y categoría":
        pdf.cell(0, 8, limpiar_texto("Reporte de Pilotos Agrupados por Categoria"), ln=True, align="C")
        pdf.ln(5)

        global_idx = 1
        for cat in CATEGORIAS:
            pilotos_cat = [p for p in pilotos if p.get("categoria") == cat]
            if not pilotos_cat:
                continue

            # Título de Categoría
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(200, 220, 240)
            pdf.cell(0, 7, limpiar_texto(f" CATEGORIA: {cat.upper()} ({len(pilotos_cat)} pilotos)"), border=1, ln=True, fill=True)

            # Encabezados de Tabla
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(240, 240, 240)
            widths = [15, 120, 55]
            headers = ["#", "Nombre Completo", "Placa / Dorsal"]
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 7, limpiar_texto(h), border=1, align="C", fill=True)
            pdf.ln()

            # Filas de Pilotos por Categoría
            pdf.set_font("Helvetica", "", 9)
            for p in pilotos_cat:
                pdf.cell(widths[0], 7, str(global_idx), border=1, align="C")
                pdf.cell(widths[1], 7, limpiar_texto(p["nombre"]), border=1, align="L")
                pdf.cell(widths[2], 7, limpiar_texto(p.get("placa", "-")), border=1, align="C")
                pdf.ln()
                global_idx += 1
            pdf.ln(3)

    # ----------------------------------------------------
    # REPORTE: NOMBRE Y DATOS DE PAGO (SEPARADO POR MEDIO / DESTINATARIO)
    # ----------------------------------------------------
    else:
        pdf.cell(0, 8, limpiar_texto("Reporte de Datos de Pago Separados por Medio y Destinatario"), ln=True, align="C")
        pdf.ln(5)

        secciones = [
            ("Efectivo", lambda p: p.get("medio") == "Efectivo"),
            ("Transferencia a Mercedes", lambda p: p.get("medio") == "Transferencia" and p.get("destinatario") == "Mercedes"),
            ("Transferencia a Marcelo", lambda p: p.get("medio") == "Transferencia" and p.get("destinatario") == "Marcelo"),
            ("Otras Transferencias / Sin Pago", lambda p: not (
                p.get("medio") == "Efectivo" or 
                (p.get("medio") == "Transferencia" and p.get("destinatario") in ["Mercedes", "Marcelo"])
            ))
        ]

        global_idx = 1
        for titulo_sec, filtro in secciones:
            pilotos_sec = [p for p in pilotos if filtro(p)]
            if not pilotos_sec:
                continue

            total_sec = sum(p.get("monto", 0.0) for p in pilotos_sec)

            # Título de Sección
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(220, 235, 220)
            pdf.cell(0, 7, limpiar_texto(f" {titulo_sec.upper()} ({len(pilotos_sec)} registros) - Total: ${total_sec:,.0f}"), border=1, ln=True, fill=True)

            # Encabezados
            widths = [10, 65, 45, 35, 35]
            headers = ["#", "Nombre Completo", "Categoria", "Situacion", "Monto ($)"]
            
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(240, 240, 240)
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 7, limpiar_texto(h), border=1, align="C", fill=True)
            pdf.ln()

            # Filas
            pdf.set_font("Helvetica", "", 8)
            for p in pilotos_sec:
                pdf.cell(widths[0], 7, str(global_idx), border=1, align="C")
                pdf.cell(widths[1], 7, limpiar_texto(p["nombre"]), border=1, align="L")
                pdf.cell(widths[2], 7, limpiar_texto(p.get("categoria", "-")), border=1, align="L")
                pdf.cell(widths[3], 7, limpiar_texto(p.get("situacion", "-")), border=1, align="C")
                pdf.cell(widths[4], 7, limpiar_texto(f"${p.get('monto', 0):,.0f}"), border=1, align="R")
                pdf.ln()
                global_idx += 1
            pdf.ln(4)

    # Exportación robusta a bytes
    out = pdf.output()
    if isinstance(out, str):
        return out.encode('latin1')
    elif isinstance(out, bytearray):
        return bytes(out)
    return out


# ==========================================
# INTERFAZ Y NAVEGACIÓN
# ==========================================
st.title("🏎️ Sistema de Caja - Enduro")
st.caption("Gestión de inscripciones, pagos, gastos y reportes de la organización")

# --- SECCIÓN EN LA BARRA LATERAL: RESPALDO MULTIFORMATO Y BASE DE DATOS ---
with st.sidebar.expander("💾 Copia de Seguridad / Base de Datos", expanded=True):
    st.markdown("### 📥 Importar Respaldo")
    archivo_subido = st.file_uploader(
        "Subir copia (.json, .xlsx, .csv):", 
        type=["json", "xlsx", "xls", "csv"]
    )
    if archivo_subido is not None:
        if st.button("Restaurar Datos", type="primary"):
            try:
                procesar_importacion(archivo_subido)
                st.success("¡Base de datos restaurada correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al importar archivo: {e}")

    st.markdown("---")
    st.markdown("### 📤 Exportar Respaldo")
    formato_export = st.selectbox(
        "Selecciona el formato de copia:",
        ["JSON (.json)", "Excel (.xlsx)", "CSV (.csv)", "PDF (.pdf)"]
    )

    if formato_export == "JSON (.json)":
        datos_json = json.dumps(
            {
                "pilotos": st.session_state.pilotos,
                "gastos": st.session_state.gastos,
                "historial": st.session_state.historial
            },
            ensure_ascii=False,
            indent=4
        )
        st.download_button(
            label="💾 Descargar copia JSON",
            data=datos_json,
            file_name="respaldo_caja_enduro.json",
            mime="application/json"
        )
    elif formato_export == "Excel (.xlsx)":
        excel_bytes = exportar_excel()
        st.download_button(
            label="💾 Descargar copia Excel",
            data=excel_bytes,
            file_name="respaldo_caja_enduro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif formato_export == "CSV (.csv)":
        csv_bytes = exportar_csv_pilotos()
        st.download_button(
            label="💾 Descargar CSV Pilotos",
            data=csv_bytes,
            file_name="pilotos_caja_enduro.csv",
            mime="text/csv"
        )
    elif formato_export == "PDF (.pdf)":
        if st.session_state.pilotos:
            pdf_bytes = generar_pdf(st.session_state.pilotos, "Completo")
            st.download_button(
                label="💾 Descargar PDF Completo",
                data=pdf_bytes,
                file_name="reporte_completo_enduro.pdf",
                mime="application/pdf"
            )
        else:
            st.info("No hay datos para generar el PDF.")

st.sidebar.markdown("---")

opciones_menu = [
    "1. Registrar Piloto",
    "2. Modificar / Eliminar Piloto",
    "3. Balance de Caja y Seguro",
    "4. Clasificación por Montos",
    "5. Gastos Extra",
    "6. Historial de Cambios",
    "7. Exportar PDF"
]
menu = st.sidebar.radio("Menú Principal", opciones_menu)

# ------------------------------------------
# 1. REGISTRAR PILOTO
# ------------------------------------------
if menu == "1. Registrar Piloto":
    st.header("📝 Registrar Nuevo Piloto")

    opciones_situacion = ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado", "Indistinto / Nulo", "Adeuda", "Gratis"]
    situacion_op = st.selectbox("Seleccione la Situación del Piloto:", opciones_situacion, key="reg_situacion_op")

    with st.form("form_registro", clear_on_submit=True):
        col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
        with col_n1:
            nombre = st.text_input("Nombre y Apellido del piloto:")
        with col_n2:
            placa = st.text_input("Placa / Dorsal:", value="")
        with col_n3:
            categoria = st.selectbox("Categoría:", CATEGORIAS)

        col1, col2 = st.columns(2)
        
        dia_pago = None
        tarifa_manual = 110000.0
        monto_personalizado = 0.0

        with col1:
            if situacion_op == "Pagó Tarifa":
                usar_fecha = st.checkbox("Ingresar día para calcular tarifa según la fecha", value=False)
                if usar_fecha:
                    dia_pago = st.number_input("Día del mes (1-31):", min_value=1, max_value=31, value=7)
                else:
                    tarifas_fijas = [110000.0, 130000.0, 140000.0]
                    tarifa_manual = st.selectbox("Seleccionar Tarifa Fija:", tarifas_fijas, format_func=lambda x: f"${x:,.0f}")
            elif situacion_op == "Monto Personalizado":
                monto_personalizado = st.number_input("Ingrese el Monto Personalizado ($):", min_value=0.0, value=0.0, step=1000.0)
            elif situacion_op == "Solo Seguro":
                st.info("Monto fijo retenido por seguro: **$35.000**")
            elif situacion_op == "Indistinto / Nulo":
                st.info("Monto sin especificar o nulo: **$0**")
            else:
                st.info("Monto asignado: **$0**")

        with col2:
            if situacion_op in ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado"]:
                medio = st.selectbox("Medio de pago:", ["Efectivo", "Transferencia"])
                destinatario = st.selectbox("Destinatario del pago:", ["Mercedes", "Marcelo", "Lourdes"])
            else:
                medio = "Ninguno"
                destinatario = "Ninguno"

        enviado = st.form_submit_button("Registrar Piloto")

        if enviado:
            if len(nombre.strip()) < 3:
                st.error("Error: El nombre debe tener al menos 3 caracteres.")
            else:
                monto, medio_pago, dest, sit_texto = resolver_situacion(
                    situacion_op, dia_pago, monto_personalizado, medio, destinatario, tarifa_manual
                )

                st.session_state.pilotos.append({
                    "nombre": nombre,
                    "placa": placa if placa.strip() else "-",
                    "categoria": categoria,
                    "monto": monto,
                    "medio": medio_pago,
                    "destinatario": dest,
                    "situacion": sit_texto
                })

                log = f"ALTA PILOTO: {nombre} | Placa: {placa} | Cat: {categoria} | Situación: {sit_texto} | Monto: ${monto}"
                st.session_state.historial.append(log)
                
                guardar_autoguardado()
                st.success(f"¡Piloto {nombre} registrado con éxito!")


# ------------------------------------------
# 2. MODIFICAR / ELIMINAR PILOTO
# ------------------------------------------
elif menu == "2. Modificar / Eliminar Piloto":
    st.header("✏️ Modificar o Eliminar Piloto")

    if not st.session_state.pilotos:
        st.info("No hay pilotos registrados.")
    else:
        nombres_lista = [f"{i+1}. {p['nombre']} (Placa: {p.get('placa','-')}) - ${p['monto']}" for i, p in enumerate(st.session_state.pilotos)]
        seleccion = st.selectbox("Seleccione el piloto:", range(len(nombres_lista)), format_func=lambda x: nombres_lista[x])

        piloto_actual = st.session_state.pilotos[seleccion]

        st.subheader(f"Datos actuales de: {piloto_actual['nombre']}")
        col_a, col_b = st.columns(2)
        col_a.write(f"**Placa / Dorsal:** {piloto_actual.get('placa', '-')}")
        col_a.write(f"**Categoría:** {piloto_actual.get('categoria', '-')}")
        col_a.write(f"**Situación:** {piloto_actual['situacion']}")
       col_b.write(f"**Monto:** ${piloto_actual['monto']}")

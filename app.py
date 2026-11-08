import csv
import io
import json
import os
import re
import unicodedata

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

    else:  # Gratis
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
# RESPALDO: DESCARGAR E IMPORTAR (JSON, Excel, CSV, Word)
# ==========================================
CAMPOS_PILOTO = ["nombre", "placa", "categoria", "situacion", "monto", "medio", "destinatario"]
CAMPOS_GASTO = ["descripcion", "monto"]


def _clave(t):
    t = unicodedata.normalize("NFD", str(t))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.strip().lower()


def _num(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _norm_piloto(d):
    return {
        "nombre": str(d.get("nombre", "") or "").strip(),
        "placa": str(d.get("placa", "-") or "-").strip(),
        "categoria": str(d.get("categoria", "Otra") or "Otra").strip(),
        "monto": _num(d.get("monto")),
        "medio": str(d.get("medio", "Ninguno") or "Ninguno").strip(),
        "destinatario": str(d.get("destinatario", "Ninguno") or "Ninguno").strip(),
        "situacion": str(d.get("situacion", "Gratis") or "Gratis").strip(),
    }


def _norm_gasto(d):
    return {
        "descripcion": str(d.get("descripcion", "") or "").strip(),
        "monto": _num(d.get("monto")),
    }


def _armar(pilotos, gastos, historial):
    return {
        "pilotos": [_norm_piloto(p) for p in pilotos if str(p.get("nombre", "") or "").strip()],
        "gastos": [_norm_gasto(g) for g in gastos if str(g.get("descripcion", "") or "").strip()],
        "historial": [str(h) for h in historial if str(h).strip()],
    }


def _clasificar(tablas):
    """tablas: lista de (encabezados, filas). Detecta qué es cada tabla."""
    pilotos, gastos, historial = [], [], []
    for headers, filas in tablas:
        hs = [_clave(h) for h in headers]
        dicts = [dict(zip(hs, f)) for f in filas]
        if "nombre" in hs:
            pilotos += dicts
        elif "descripcion" in hs:
            gastos += dicts
        elif "registro" in hs:
            historial += [d.get("registro", "") for d in dicts]
    return _armar(pilotos, gastos, historial)


def leer_respaldo(archivo):
    nombre = archivo.name.lower()
    raw = archivo.getvalue()

    if nombre.endswith(".json"):
        d = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(d, dict):
            raise ValueError("El JSON no tiene el formato esperado.")
        datos = _armar(d.get("pilotos", []), d.get("gastos", []), d.get("historial", []))

    elif nombre.endswith((".xlsx", ".xlsm")):
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise ValueError("Falta agregar 'openpyxl' al requirements.txt")
        wb = load_workbook(io.BytesIO(raw), data_only=True)
        tablas = []
        for ws in wb.worksheets:
            filas = [list(r) for r in ws.iter_rows(values_only=True)
                     if any(c not in (None, "") for c in r)]
            if filas:
                tablas.append((filas[0], filas[1:]))
        datos = _clasificar(tablas)

    elif nombre.endswith(".csv"):
        texto = raw.decode("utf-8-sig", errors="replace")
        try:
            dialecto = csv.Sniffer().sniff(texto[:2000], delimiters=",;\t")
        except csv.Error:
            dialecto = csv.excel
        filas = [f for f in csv.reader(io.StringIO(texto), dialecto) if any(f)]
        datos = _clasificar([(filas[0], filas[1:])]) if filas else _armar([], [], [])

    elif nombre.endswith(".docx"):
        try:
            from docx import Document
        except ImportError:
            raise ValueError("Falta agregar 'python-docx' al requirements.txt")
        doc = Document(io.BytesIO(raw))
        tablas = []
        for t in doc.tables:
            filas = [[c.text for c in r.cells] for r in t.rows]
            if filas:
                tablas.append((filas[0], filas[1:]))
        datos = _clasificar(tablas)

    else:
        raise ValueError("Formato no soportado. Usá JSON, Excel (.xlsx), CSV o Word (.docx). "
                         "El PDF es solo de lectura y no se puede importar.")

    if not (datos["pilotos"] or datos["gastos"] or datos["historial"]):
        raise ValueError("No encontré datos reconocibles en el archivo.")
    return datos


def exportar_excel(datos):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Pilotos"
    ws.append(CAMPOS_PILOTO)
    for p in datos["pilotos"]:
        ws.append([p.get(c, "") for c in CAMPOS_PILOTO])
    ws = wb.create_sheet("Gastos")
    ws.append(CAMPOS_GASTO)
    for g in datos["gastos"]:
        ws.append([g.get(c, "") for c in CAMPOS_GASTO])
    ws = wb.create_sheet("Historial")
    ws.append(["registro"])
    for h in datos["historial"]:
        ws.append([h])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def exportar_word(datos):
    from docx import Document
    doc = Document()
    doc.add_heading("Respaldo - Sistema de Caja Enduro", level=1)

    def tabla(titulo, campos, filas):
        doc.add_heading(titulo, level=2)
        t = doc.add_table(rows=1, cols=len(campos))
        t.style = "Table Grid"
        for i, c in enumerate(campos):
            t.rows[0].cells[i].text = c
        for fila in filas:
            celdas = t.add_row().cells
            for i, v in enumerate(fila):
                celdas[i].text = str(v)

    tabla("Pilotos", CAMPOS_PILOTO,
          [[p["monto"] if c == "monto" else p.get(c, "") for c in CAMPOS_PILOTO]
           for p in datos["pilotos"]])
    tabla("Gastos", CAMPOS_GASTO, [[g["descripcion"], g["monto"]] for g in datos["gastos"]])
    tabla("Historial", ["registro"], [[h] for h in datos["historial"]])
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ==========================================
# INTERFAZ Y NAVEGACIÓN
# ==========================================
st.title("🏎️ Sistema de Caja - Enduro")
st.caption("Gestión de inscripciones, pagos, gastos y reportes de la organización")

# --- SECCIÓN EN LA BARRA LATERAL: RESPALDO Y BASE DE DATOS ---
st.sidebar.header("📂 Respaldo de datos")

datos_resp = _armar(st.session_state.pilotos, st.session_state.gastos, st.session_state.historial)

formato = st.sidebar.selectbox(
    "Descargar copia en:",
    ["JSON", "Excel (.xlsx)", "Word (.docx)", "PDF (solo lectura)"],
    key="formato_respaldo",
)
try:
    if formato == "JSON":
        data_d = json.dumps(datos_resp, ensure_ascii=False, indent=4).encode("utf-8")
        nom_d, mime_d = "copia_de_seguridad_caja.json", "application/json"
    elif formato.startswith("Excel"):
        data_d = exportar_excel(datos_resp)
        nom_d = "copia_de_seguridad_caja.xlsx"
        mime_d = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif formato.startswith("Word"):
        data_d = exportar_word(datos_resp)
        nom_d = "copia_de_seguridad_caja.docx"
        mime_d = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        data_d = generar_pdf(st.session_state.pilotos, "Completo")
        nom_d, mime_d = "copia_de_seguridad_caja.pdf", "application/pdf"
    st.sidebar.download_button("💾 Descargar copia de seguridad", data=data_d,
                               file_name=nom_d, mime=mime_d)
except Exception as e:
    st.sidebar.error(f"No se pudo generar la copia: {e}")

st.sidebar.markdown("---")

archivo_subido = st.sidebar.file_uploader(
    "Importar copia de seguridad",
    type=["json", "xlsx", "xlsm", "csv", "docx"],
    key="uploader_respaldo",
)
if archivo_subido is not None:
    try:
        nuevos = leer_respaldo(archivo_subido)
    except Exception as e:
        st.sidebar.error(f"No se pudo leer el archivo: {e}")
    else:
        st.sidebar.info(
            f"Archivo leído: {len(nuevos['pilotos'])} pilotos, "
            f"{len(nuevos['gastos'])} gastos, {len(nuevos['historial'])} registros."
        )
        if st.sidebar.button("✅ Reemplazar datos actuales con este archivo"):
            st.session_state.pilotos = nuevos["pilotos"]
            st.session_state.gastos = nuevos["gastos"]
            st.session_state.historial = nuevos["historial"]
            guardar_autoguardado()
            st.sidebar.success("¡Datos restaurados!")

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
        col_b.write(f"**Medio:** {piloto_actual['medio']}")
        col_b.write(f"**Para:** {piloto_actual['destinatario']}")

        accion = st.radio("Acción a realizar:", ["Modificar", "Eliminar"], horizontal=True)

        if accion == "Eliminar":
            if st.button("🔴 Confirmar Eliminar", type="primary"):
                p_borrado = st.session_state.pilotos.pop(seleccion)
                log = f"BAJA PILOTO: {p_borrado['nombre']} | Placa: {p_borrado.get('placa','-')}"
                st.session_state.historial.append(log)

                guardar_autoguardado()
                st.success("Piloto eliminado correctamente.")
                st.rerun()

        else:
            opciones_situacion = ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado", "Indistinto / Nulo", "Adeuda", "Gratis"]
            nueva_sit = st.selectbox("Nueva situación:", opciones_situacion, key="mod_situacion_op")

            with st.form("form_modificar"):
                col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
                nuevo_nombre = col_m1.text_input("Nuevo nombre:", value=piloto_actual['nombre'])
                nueva_placa = col_m2.text_input("Nueva placa:", value=piloto_actual.get('placa', ''))

                cat_actual = piloto_actual.get('categoria', 'Sénior A')
                idx_cat = CATEGORIAS.index(cat_actual) if cat_actual in CATEGORIAS else 0
                nueva_cat = col_m3.selectbox("Nueva categoría:", CATEGORIAS, index=idx_cat)

                dia_pago = None
                tarifa_manual = 110000.0
                monto_custom = 0.0

                if nueva_sit == "Pagó Tarifa":
                    usar_fecha_mod = st.checkbox("Ingresar día para calcular tarifa según la fecha", value=False)
                    if usar_fecha_mod:
                        dia_pago = st.number_input("Día del mes (1-31):", min_value=1, max_value=31, value=7)
                    else:
                        tarifas_fijas = [110000.0, 130000.0, 140000.0]
                        tarifa_manual = st.selectbox("Seleccionar Tarifa Fija:", tarifas_fijas, format_func=lambda x: f"${x:,.0f}")
                elif nueva_sit == "Monto Personalizado":
                    monto_custom = st.number_input("Monto personalizado ($):", min_value=0.0, value=float(piloto_actual['monto']), step=1000.0)

                if nueva_sit in ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado"]:
                    medio = st.selectbox("Medio de pago:", ["Efectivo", "Transferencia"])
                    destinatario = st.selectbox("Destinatario:", ["Mercedes", "Marcelo", "Lourdes"])
                else:
                    medio = "Ninguno"
                    destinatario = "Ninguno"

                guardar = st.form_submit_button("Guardar Cambios")

                if guardar:
                    if len(nuevo_nombre.strip()) < 3:
                        st.error("El nombre debe tener al menos 3 caracteres.")
                    else:
                        monto, medio_pago, dest, sit_texto = resolver_situacion(
                            nueva_sit, dia_pago, monto_custom, medio, destinatario, tarifa_manual
                        )

                        log = f"MODIFICACIÓN PILOTO: {piloto_actual['nombre']} -> {nuevo_nombre}"
                        st.session_state.historial.append(log)

                        st.session_state.pilotos[seleccion] = {
                            "nombre": nuevo_nombre,
                            "placa": nueva_placa if nueva_placa.strip() else "-",
                            "categoria": nueva_cat,
                            "monto": monto,
                            "medio": medio_pago,
                            "destinatario": dest,
                            "situacion": sit_texto
                        }

                        guardar_autoguardado()
                        st.success("Piloto actualizado con éxito.")
                        st.rerun()


# ------------------------------------------
# 3. BALANCE DE CAJA Y SEGURO
# ------------------------------------------
elif menu == "3. Balance de Caja y Seguro":
    st.header("📊 Estadísticas y Cierre de Caja")

    total_pilotos = len(st.session_state.pilotos)

    if total_pilotos == 0:
        st.info("No hay pilotos registrados.")
    else:
        situaciones = [p["situacion"] for p in st.session_state.pilotos]
        pagados = situaciones.count("Pagado")
        solo_seg = situaciones.count("Solo Seguro")
        personal = situaciones.count("Personalizado")
        indistinto = situaciones.count("Indistinto/Nulo")
        adeuda = situaciones.count("Adeuda")
        gratis = situaciones.count("Gratis")

        recaudacion_bruta = sum(p["monto"] for p in st.session_state.pilotos)
        retencion_seguro = total_pilotos * 35000.0
        neto_antes_gastos = recaudacion_bruta - retencion_seguro
        total_gastos = sum(g["monto"] for g in st.session_state.gastos)
        neto_final = neto_antes_gastos - total_gastos

        porcentaje_seguro = (retencion_seguro / recaudacion_bruta * 100) if recaudacion_bruta > 0 else 0.0

        st.subheader("Resumen de Pilotos")
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        c1.metric("Tarifa Fija", pagados)
        c2.metric("Solo Seguro", solo_seg)
        c3.metric("Personalizado", personal)
        c4.metric("Indistinto/Nulo", indistinto)
        c5.metric("Adeudan", adeuda)
        c6.metric("Gratis", gratis)
        c7.metric("TOTAL PILOTOS", total_pilotos)

        st.markdown("---")
        st.subheader("Balance Financiero")

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Recaudación Bruta", f"${recaudacion_bruta:,.2f}")
        col_m2.metric("Retención Seguro ($35k/u)", f"${retencion_seguro:,.2f}")
        col_m3.metric("Neto Antes de Gastos", f"${neto_antes_gastos:,.2f}")

        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Total Gastos Extra", f"${total_gastos:,.2f}")
        col_m5.metric("FONDO NETO ORGANIZACIÓN", f"${neto_final:,.2f}")
        col_m6.metric("Impacto del Seguro", f"{porcentaje_seguro:.2f}%")


# ------------------------------------------
# 4. CLASIFICACIÓN POR MONTOS
# ------------------------------------------
elif menu == "4. Clasificación por Montos":
    st.header("📋 Clasificación y Auditoría de Pilotos")

    if not st.session_state.pilotos:
        st.info("No hay pilotos registrados.")
    else:
        grupos = [
            ("Tramo 1: Del 7 al 12 ($110.000)", 110000.0, "Pagado"),
            ("Tramo 2: Del 13 al 17 ($130.000)", 130000.0, "Pagado"),
            ("Tramo 3: Del 18 al 19 ($140.000)", 140000.0, "Pagado"),
            ("Solo Seguro ($35.000)", 35000.0, "Solo Seguro"),
            ("Monto Personalizado", None, "Personalizado"),
            ("Indistinto / Nulo ($0)", 0.0, "Indistinto/Nulo"),
            ("Deudores ($0)", None, "Adeuda"),
            ("Gratis ($0)", None, "Gratis"),
        ]

        for titulo, monto_grp, sit_grp in grupos:
            with st.expander(f"Grupo: {titulo}", expanded=False):
                filtrados = [
                    p for p in st.session_state.pilotos
                    if p["situacion"] == sit_grp and (monto_grp is None or p["monto"] == monto_grp)
                ]
                if filtrados:
                    st.dataframe(filtrados, use_container_width=True)
                else:
                    st.write("Sin pilotos en este grupo.")


# ------------------------------------------
# 5. GASTOS EXTRA
# ------------------------------------------
elif menu == "5. Gastos Extra":
    st.header("💸 Gastos Extra de la Organización")

    tab1, tab2 = st.tabs(["Agregar Gasto", "Ver y Modificar Gastos"])

    with tab1:
        with st.form("form_gasto", clear_on_submit=True):
            descripcion = st.text_input("Descripción del gasto:")
            monto_gasto = st.number_input("Monto del gasto ($):", min_value=0.1, value=1000.0)
            btn_gasto = st.form_submit_button("Registrar Gasto")

            if btn_gasto:
                if len(descripcion.strip()) < 2:
                    st.error("La descripción debe tener al menos 2 caracteres.")
                else:
                    st.session_state.gastos.append({"descripcion": descripcion, "monto": monto_gasto})
                    st.session_state.historial.append(f"GASTO AGREGADO: '{descripcion}' | ${monto_gasto}")

                    guardar_autoguardado()
                    st.success("Gasto registrado con éxito.")

    with tab2:
        if not st.session_state.gastos:
            st.info("No hay gastos registrados.")
        else:
            st.table(st.session_state.gastos)
            st.write(f"**TOTAL GASTOS EXTRA:** ${sum(g['monto'] for g in st.session_state.gastos):,.2f}")


# ------------------------------------------
# 6. HISTORIAL DE CAMBIOS
# ------------------------------------------
elif menu == "6. Historial de Cambios":
    st.header("📜 Historial de Cambios en la Sesión")

    if not st.session_state.historial:
        st.info("No se registraron cambios en esta sesión.")
    else:
        for idx, item in enumerate(reversed(st.session_state.historial), 1):
            st.text(f"{idx}. {item}")


# ------------------------------------------
# 7. EXPORTAR PDF
# ------------------------------------------
elif menu == "7. Exportar PDF":
    st.header("📄 Exportar Reporte PDF")

    if not st.session_state.pilotos:
        st.info("No hay pilotos registrados para generar el PDF.")
    else:
        st.write("Selecciona el tipo de informe que deseas generar:")

        opciones_pdf = [
            "Completo",
            "Nombre completo con placa y categoría",
            "Nombre y datos de pago"
        ]
        opcion_pdf = st.radio("Opciones de Información del Reporte:", opciones_pdf)

        st.markdown("---")

        try:
            pdf_bytes = generar_pdf(st.session_state.pilotos, opcion_pdf)

            st.download_button(
                label="📥 Descargar Reporte PDF",
                data=pdf_bytes,
                file_name=f"reporte_pilotos_{opcion_pdf.lower().replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error al generar el PDF: {e}")

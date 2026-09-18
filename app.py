import streamlit as st
import streamlit.components.v1 as components
import json
import os
import base64
from fpdf import FPDF

# Configuración de la página
st.set_page_config(page_title="Sistema de Caja - Enduro", page_icon="🏎️", layout="wide")

# Archivo de persistencia local para no perder datos al refrescar
DATA_FILE = "datos_caja.json"

# Lista general de categorías
CATEGORIAS = [
    "Sénior A", "Senior B", "Júnior A", "Junior B", "Master A", "Master B", 
    "Master C", "Master D", "Master Principiantes", "Master Leyenda", 
    "Principiantes A1", "Principiantes A2", "Principiantes B", "Sub17", 
    "Infantiles A", "Infantiles B", "Mini", "Damas", "Otra"
]

# ==========================================
# GESTIÓN DE PERSISTENCIA (GUARDADO Y CARGA)
# ==========================================
def cargar_datos_disco():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"pilotos": [], "gastos": [], "historial": []}

def guardar_datos_disco():
    data = {
        "pilotos": st.session_state.pilotos,
        "gastos": st.session_state.gastos,
        "historial": st.session_state.historial
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Inicialización de Session State desde archivo local
if "datos_inicializados" not in st.session_state:
    datos_guardados = cargar_datos_disco()
    st.session_state.pilotos = datos_guardados.get("pilotos", [])
    st.session_state.gastos = datos_guardados.get("gastos", [])
    st.session_state.historial = datos_guardados.get("historial", [])
    st.session_state.datos_inicializados = True


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
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
        return 40000.0, medio_op, dest_op, "Solo Seguro"

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
    pdf.set_font("Helvetica", "B", 16)
   
    # Encabezado
    pdf.cell(0, 10, limpiar_texto("Sistema de Caja - Enduro"), ln=True, align="C")
    pdf.set_font("Helvetica", "I", 11)
   
    if tipo_reporte == "Completo":
        pdf.cell(0, 8, limpiar_texto("Reporte Completo de Pilotos (Agrupado por Categoria)"), ln=True, align="C")
    elif tipo_reporte == "Nombre completo con placa y categoría":
        pdf.cell(0, 8, limpiar_texto("Reporte de Pilotos: Nombre, Placa y Categoria"), ln=True, align="C")
    elif tipo_reporte == "Nombre y datos de pago (por Categoria)":
        pdf.cell(0, 8, limpiar_texto("Reporte de Datos de Pago (Agrupado por Categoria)"), ln=True, align="C")
    else:
        pdf.cell(0, 8, limpiar_texto("Reporte de Datos de Pago (Separado por Medio y Destinatario)"), ln=True, align="C")
       
    pdf.ln(4)

    # -------------------------------------------------------------
    # CASO 1: SEPARADO POR MEDIO Y DESTINATARIO (Efectivo / Transferencias)
    # -------------------------------------------------------------
    if tipo_reporte == "Nombre y datos de pago (por Medio/Destinatario)":
        grupos_pago = {
            "Efectivo": [],
            "Transferencia - Mercedes": [],
            "Transferencia - Marcelo": [],
            "Transferencia - Lourdes": [],
            "Otros / Sin Pago": []
        }

        for p in pilotos:
            medio = p.get("medio", "Ninguno")
            dest = p.get("destinatario", "Ninguno")

            if medio == "Efectivo":
                grupos_pago["Efectivo"].append(p)
            elif medio == "Transferencia" and dest == "Mercedes":
                grupos_pago["Transferencia - Mercedes"].append(p)
            elif medio == "Transferencia" and dest == "Marcelo":
                grupos_pago["Transferencia - Marcelo"].append(p)
            elif medio == "Transferencia" and dest == "Lourdes":
                grupos_pago["Transferencia - Lourdes"].append(p)
            else:
                grupos_pago["Otros / Sin Pago"].append(p)

        widths = [10, 50, 25, 35, 30, 30]
        headers = ["#", "Nombre Completo", "Placa", "Categoria", "Situacion", "Monto ($)"]

        idx_global = 1
        for nombre_grupo, lista in grupos_pago.items():
            if not lista:
                continue

            # Encabezado del grupo de pago
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(200, 215, 235)
            pdf.cell(0, 7, limpiar_texto(f" GRUPO: {nombre_grupo.upper()} ({len(lista)} pilotos)"), border=1, ln=True, align="L", fill=True)

            # Encabezados de tabla
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(230, 230, 230)
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 6, limpiar_texto(h), border=1, align="C", fill=True)
            pdf.ln()

            # Filas
            pdf.set_font("Helvetica", "", 8)
            subtotal = 0.0
            for p in lista:
                row = [
                    str(idx_global),
                    p["nombre"],
                    p.get("placa", "-"),
                    p.get("categoria", "-"),
                    p["situacion"],
                    f"${p['monto']:,.0f}"
                ]
                subtotal += p["monto"]

                for i, val in enumerate(row):
                    align = "C" if i in [0, 2] else ("R" if i == 5 else "L")
                    pdf.cell(widths[i], 6, limpiar_texto(val), border=1, align=align)
                pdf.ln()
                idx_global += 1

            # Subtotal del grupo
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(sum(widths[:5]), 6, limpiar_texto(f"Subtotal {nombre_grupo}:"), border=1, align="R")
            pdf.cell(widths[5], 6, limpiar_texto(f"${subtotal:,.0f}"), border=1, align="R")
            pdf.ln()
            pdf.ln(3)

    # -------------------------------------------------------------
    # CASO 2: AGRUPADO POR CATEGORÍA (Conserva orden de ingreso)
    # -------------------------------------------------------------
    else:
        pilotos_por_cat = {}
        for p in pilotos:
            cat = p.get("categoria", "Sin Categoria")
            if cat not in pilotos_por_cat:
                pilotos_por_cat[cat] = []
            pilotos_por_cat[cat].append(p)

        if tipo_reporte == "Completo":
            widths = [10, 45, 20, 30, 25, 20, 20, 20]
            headers = ["#", "Nombre", "Placa", "Categoria", "Situacion", "Monto", "Medio", "Destino"]
        elif tipo_reporte == "Nombre completo con placa y categoría":
            widths = [15, 95, 35, 45]
            headers = ["#", "Nombre Completo", "Placa / Dorsal", "Categoria"]
        else: # Nombre y datos de pago (por Categoría)
            widths = [10, 55, 35, 30, 30, 30]
            headers = ["#", "Nombre Completo", "Situacion", "Monto ($)", "Medio Pago", "Destinatario"]

        idx_global = 1
        for cat, lista_pilotos in pilotos_por_cat.items():
            # Encabezado de Categoría
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(200, 215, 235)
            pdf.cell(0, 7, limpiar_texto(f" CATEGORIA: {cat.upper()} ({len(lista_pilotos)} pilotos)"), border=1, ln=True, align="L", fill=True)

            # Encabezados de tabla
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(230, 230, 230)
            for i, h in enumerate(headers):
                pdf.cell(widths[i], 6, limpiar_texto(h), border=1, align="C", fill=True)
            pdf.ln()

            # Filas ordenadas según ingreso
            pdf.set_font("Helvetica", "", 8)
            for p in lista_pilotos:
                if tipo_reporte == "Completo":
                    row = [
                        str(idx_global),
                        p["nombre"],
                        p.get("placa", "-"),
                        p.get("categoria", "-"),
                        p["situacion"],
                        f"${p['monto']:,.0f}",
                        p["medio"],
                        p["destinatario"]
                    ]
                elif tipo_reporte == "Nombre completo con placa y categoría":
                    row = [
                        str(idx_global),
                        p["nombre"],
                        p.get("placa", "-"),
                        p.get("categoria", "-")
                    ]
                else:
                    row = [
                        str(idx_global),
                        p["nombre"],
                        p["situacion"],
                        f"${p['monto']:,.0f}",
                        p["medio"],
                        p["destinatario"]
                    ]

                for i, val in enumerate(row):
                    align = "C" if i in [0, 2] else "L"
                    if tipo_reporte == "Completo" and i == 5:
                        align = "R"
                    elif tipo_reporte == "Nombre y datos de pago (por Categoria)" and i == 3:
                        align = "R"
                    pdf.cell(widths[i], 6, limpiar_texto(val), border=1, align=align)
                pdf.ln()
                idx_global += 1

            pdf.ln(3)

    # Generación limpia y compatible de bytes del PDF
    try:
        out = pdf.output()
        if out is None:
            out = pdf.output(dest='S')
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        elif isinstance(out, str):
            return out.encode('latin-1')
        return bytes(out)
    except Exception:
        out = pdf.output(dest='S')
        if isinstance(out, str):
            return out.encode('latin-1')
        return bytes(out)


# ==========================================
# INTERFAZ Y NAVEGACIÓN
# ==========================================
st.title("🏎️ Sistema de Caja - Enduro")
st.caption("Gestión de inscripciones, pagos, gastos y reportes de la organización")

opciones_menu = [
    "1. Registrar Piloto",
    "2. Modificar / Eliminar Piloto",
    "3. Balance de Caja y Seguro",
    "4. Clasificación por Montos",
    "5. Gastos Extra",
    "6. Historial de Cambios",
    "7. Exportar / Ver PDF"
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
                st.info("Monto fijo retenido por seguro: **$40.000**")
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
                guardar_datos_disco()
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
                guardar_datos_disco()
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

                        st.session_state.pilotos[seleccion] =
                            "nombre": nuevo_nombre,
                            "placa": nueva_placa if nueva_placa.strip() else "-",
                            "categoria": nueva_cat,
                            "monto": monto,
                            "medio": medio_pago,
                            "destinatario": dest,
                            "situacion": sit_te

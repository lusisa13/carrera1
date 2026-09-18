# Configuración de la página
st.set_page_config(page_title="Sistema de Caja - Enduro", page_icon="🏍️", layout="wide")

# ==========================================
# INICIALIZACIÓN DEL ESTADO (SESSION STATE)
# ==========================================
if "pilotos" not in st.session_state:
    st.session_state.pilotos = []
    # Pre-cargamos los 110 pilotos de muestra igual que en tu script original
    for i in range(1, 111):
        nombre = f"Piloto {i}"
        if i % 3 == 0:
            monto = 80000.0
            situacion = "Pagado"
            medio = "Efectivo"
            dest = "Mercedes"
        elif i % 3 == 1:
            monto = 0.0
            situacion = "Adeuda"
            medio = "Ninguno"
            dest = "Ninguno"
        else:
            monto = 0.0
            situacion = "Gratis"
            medio = "Ninguno"
            dest = "Ninguno"

        st.session_state.pilotos.append({
            "nombre": nombre,
            "monto": monto,
            "medio": medio,
            "destinatario": dest,
            "situacion": situacion
        })

if "gastos" not in st.session_state:
    st.session_state.gastos = []

if "historial" not in st.session_state:
    st.session_state.historial = []


# Funciones auxiliares
def resolver_situacion(opcion_sit, dia_mes=1, monto_custom=0.0, medio_op="Efectivo", dest_op="Mercedes"):
    if opcion_sit == "Pagó Tarifa":
        if dia_mes <= 10:
            monto = 80000.0
        elif dia_mes <= 25:
            monto = 100000.0
        else:
            monto = 120000.0
        return monto, medio_op, dest_op, "Pagado"

    elif opcion_sit == "Solo Seguro":
        return 40000.0, medio_op, dest_op, "Solo Seguro"

    elif opcion_sit == "Monto Personalizado":
        return float(monto_custom), medio_op, dest_op, "Personalizado"

    elif opcion_sit == "Adeuda":
        return 0.0, "Ninguno", "Ninguno", "Adeuda"

    else: # Gratis
        return 0.0, "Ninguno", "Ninguno", "Gratis"


# ==========================================
# INTERFAZ Y NAVEGACIÓN
# ==========================================
st.title("🏍️ Sistema de Caja - Enduro")
st.caption("Gestión de inscripciones, pagos, gastos y reportes de la organización")

menu = st.sidebar.radio(
    "Menú Principal",
    [
        "1. Registrar Piloto",
        "2. Modificar / Eliminar Piloto",
        "3. Balance de Caja y Seguro",
        "4. Clasificación por Montos",
        "5. Gastos Extra",
        "6. Historial de Cambios"
    ]
)

# ------------------------------------------
# 1. REGISTRAR PILOTO
# ------------------------------------------
if menu == "1. Registrar Piloto":
    st.header("📝 Registrar Nuevo Piloto")

    with st.form("form_registro", clear_on_submit=True):
        nombre = st.text_input("Nombre y Apellido del piloto:")
        situacion_op = st.selectbox(
            "Situación del piloto:",
            ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado", "Adeuda", "Gratis"]
        )

        col1, col2 = st.columns(2)
        with col1:
            dia_pago = st.number_input("Día del mes en que abona (1-31):", min_value=1, max_value=31, value=1)
            monto_personalizado = st.number_input("Monto personalizado ($):", min_value=0.0, value=0.0)

        with col2:
            medio = st.selectbox("Medio de pago:", ["Efectivo", "Transferencia"])
            destinatario = st.selectbox("Destinatario del pago:", ["Mercedes", "Marcelo", "Lourdes"])

        enviado = st.form_submit_button("Registrar Piloto")

        if enviado:
            if len(nombre.strip()) < 3:
                st.error("Error: El nombre debe tener al menos 3 caracteres.")
            else:
                monto, medio_pago, dest, sit_texto = resolver_situacion(
                    situacion_op, dia_pago, monto_personalizado, medio, destinatario
                )

                st.session_state.pilotos.append({
                    "nombre": nombre,
                    "monto": monto,
                    "medio": medio_pago,
                    "destinatario": dest,
                    "situacion": sit_texto
                })

                log = f"ALTA PILOTO: {nombre} | Situación: {sit_texto} | Monto: ${monto} | Medio: {medio_pago} | Para: {dest}"
                st.session_state.historial.append(log)
                st.success(f"¡Piloto {nombre} registrado con éxito!")


# ------------------------------------------
# 2. MODIFICAR / ELIMINAR PILOTO
# ------------------------------------------
elif menu == "2. Modificar / Eliminar Piloto":
    st.header("✏️ Modificar o Eliminar Piloto")

    if not st.session_state.pilotos:
        st.info("No hay pilotos registrados.")
    else:
        nombres_lista = [f"{i+1}. {p['nombre']} (${p['monto']} - {p['situacion']})" for i, p in enumerate(st.session_state.pilotos)]
        seleccion = st.selectbox("Seleccione el piloto:", range(len(nombres_lista)), format_func=lambda x: nombres_lista[x])

        piloto_actual = st.session_state.pilotos[seleccion]

        st.subheader(f"Datos actuales de: {piloto_actual['nombre']}")
        col_a, col_b = st.columns(2)
        col_a.write(f"**Situación:** {piloto_actual['situacion']}")
        col_a.write(f"**Monto:** ${piloto_actual['monto']}")
        col_b.write(f"**Medio:** {piloto_actual['medio']}")
        col_b.write(f"**Para:** {piloto_actual['destinatario']}")

        accion = st.radio("Acción a realizar:", ["Modificar", "Eliminar"], horizontal=True)

        if accion == "Eliminar":
            if st.button("🔴 Confirmar Eliminar", type="primary"):
                p_borrado = st.session_state.pilotos.pop(seleccion)
                log = f"BAJA PILOTO: {p_borrado['nombre']} | Situación: {p_borrado['situacion']} | Monto: ${p_borrado['monto']}"
                st.session_state.historial.append(log)
                st.success("Piloto eliminado correctamente.")
                st.rerun()

        else:
            with st.form("form_modificar"):
                nuevo_nombre = st.text_input("Nuevo nombre:", value=piloto_actual['nombre'])
                nueva_sit = st.selectbox(
                    "Nueva situación:",
                    ["Pagó Tarifa", "Solo Seguro", "Monto Personalizado", "Adeuda", "Gratis"]
                )
                dia_pago = st.number_input("Día del mes (1-31):", min_value=1, max_value=31, value=1)
                monto_custom = st.number_input("Monto personalizado ($):", min_value=0.0, value=piloto_actual['monto'])
                medio = st.selectbox("Medio de pago:", ["Efectivo", "Transferencia"])
                destinatario = st.selectbox("Destinatario:", ["Mercedes", "Marcelo", "Lourdes"])

                guardar = st.form_submit_button("Guardar Cambios")

                if guardar:
                    if len(nuevo_nombre.strip()) < 3:
                        st.error("El nombre debe tener al menos 3 caracteres.")
                    else:
                        monto, medio_pago, dest, sit_texto = resolver_situacion(
                            nueva_sit, dia_pago, monto_custom, medio, destinatario
                        )

                        log = f"MODIFICACIÓN PILOTO: {piloto_actual['nombre']} -> {nuevo_nombre} | Monto: ${piloto_actual['monto']} -> ${monto}"
                        st.session_state.historial.append(log)

                        st.session_state.pilotos[seleccion] = {
                            "nombre": nuevo_nombre,
                            "monto": monto,
                            "medio": medio_pago,
                            "destinatario": dest,
                            "situacion": sit_texto
                        }
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
        adeuda = situaciones.count("Adeuda")
        gratis = situaciones.count("Gratis")

        recaudacion_bruta = sum(p["monto"] for p in st.session_state.pilotos)
        retencion_seguro = total_pilotos * 40000.0
        neto_antes_gastos = recaudacion_bruta - retencion_seguro
        total_gastos = sum(g["monto"] for g in st.session_state.gastos)
        neto_final = neto_antes_gastos - total_gastos

        porcentaje_seguro = (retencion_seguro / recaudacion_bruta * 100) if recaudacion_bruta > 0 else 0.0

        st.subheader("Resumen de Pilotos")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Tarifa Fija", pagados)
        c2.metric("Solo Seguro", solo_seg)
        c3.metric("Personalizado", personal)
        c4.metric("Adeudan", adeuda)
        c5.metric("Gratis", gratis)
        c6.metric("TOTAL PILOTOS", total_pilotos)

        st.markdown("---")
        st.subheader("Balance Financiero")

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Recaudación Bruta", f"${recaudacion_bruta:,.2f}")
        col_m2.metric("Retención Seguro ($40k/u)", f"${retencion_seguro:,.2f}")
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
            ("Anticipada ($80.000)", 80000.0, None),
            ("Normal ($100.000)", 100000.0, None),
            ("Tardía ($120.000)", 120000.0, None),
            ("Solo Seguro ($40.000)", 40000.0, None),
            ("Deudores ($0)", None, "Adeuda"),
            ("Gratis ($0)", None, "Gratis"),
        ]

        for titulo, monto_grp, sit_grp in grupos:
            with st.expander(f"Grupo: {titulo}", expanded=False):
                filtrados = [
                    p for p in st.session_state.pilotos
                    if (monto_grp is not None and p["monto"] == monto_grp) or
                       (sit_grp is not None and p["situacion"] == sit_grp)
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

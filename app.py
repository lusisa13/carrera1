"""SISTEMA DE CAJA - ENDURO
================================
Gestión de inscripciones, pagos, gastos y reportes
para la organización de carreras de enduro."""
lista_nombres = []
lista_montos = []
lista_medios = []
lista_destinados = []
lista_situaciones= []
lista_gastos = []
historial_cambios = []

def pedir_validar(mensaje, minimo, maximo):
    """Pide un entero entre minimo y maximo, repite si hay error."""
    error = True
    while error:
        try:
            valor = int(input(mensaje))
            while valor < minimo or valor > maximo:
                print("\033[91mValor fuera de rango. Debe estar entre", minimo, "y", maximo, "\033[0m")
                valor = int(input("Reingrese: "))
            error = False
        except:
            print("\033[91mError: ingrese un número entero válido.\033[0m")
    return valor

def pedir_float_positivo(mensaje):
    """Pide un número decimal mayor a 0."""
    while True:
        try:
            valor = float(input(mensaje))
            if valor > 0:
                return valor
            else:
                print("\033[91mDebe ser un valor mayor a cero.\033[0m")
        except:
            print("\033[91mError: ingrese un número válido.\033[0m")

def pedir_nombre():
    """Pide y valida un nombre (no numérico, al menos 3 caracteres)."""
    nombre = input("Nombre y Apellido del piloto: ")
    while True:
        try:
            float(nombre)
            nombre = input("\033[91mNombre inválido (no puede ser número). Reingrese: \033[0m")
        except:
            if len(nombre) >= 3:
                return nombre
            else:
                nombre = input("\033[91mNombre demasiado corto (mínimo 3 caracteres). Reingrese: \033[0m")

def calcular_porcentaje(parte, total):
    """Devuelve qué porcentaje representa 'parte' de 'total'."""
    if total > 0:
        return parte / total * 100
    return 0.0

def pedir_destinatario():
    """Muestra el menú de destinatarios y devuelve el elegido."""
    print(" ¿A quién va destinado el pago?")
    print(" 1. Mercedes")
    print(" 2. Marcelo")
    print(" 3. Lourdes")
    opcion = pedir_validar(" Seleccione (1-3): ", 1, 3)
    if opcion == 1:
        return "Mercedes"
    elif opcion == 2:
        return "Marcelo"
    else:
        return "Lourdes"

def pedir_medio_y_destinatario():
    """Pide medio de pago y destinatario, devuelve ambos."""
    medio_op = pedir_validar("Medio de pago (1-Efectivo, 2-Transferencia): ", 1, 2)
    medio = "Efectivo" if medio_op == 1 else "Transferencia"
    destinatario = pedir_destinatario()
    return medio, destinatario

def resolver_situacion(opcion_sit):
    """
    Dado un número de situación (1 al 5), pide los datos necesarios
    y devuelve: monto, medio, destinatario, texto_situacion
    """
    if opcion_sit == 1:
        dia = pedir_validar("Día del mes en que abona (1-31): ", 1, 31)
        if dia <= 10:
            monto = 80000.0
        elif dia <= 25:
            monto = 100000.0
        else:
            monto = 120000.0
        medio, dest = pedir_medio_y_destinatario()
        return monto, medio, dest, "Pagado"

    elif opcion_sit == 2:
        monto = 40000.0
        medio, dest = pedir_medio_y_destinatario()
        return monto, medio, dest, "Solo Seguro"

    elif opcion_sit == 3:
        monto = pedir_float_positivo("Monto personalizado: $")
        medio, dest = pedir_medio_y_destinatario()
        return monto, medio, dest, "Personalizado"

    elif opcion_sit == 4:
        return 0.0, "Ninguno", "Ninguno", "Adeuda"

    else:
        return 0.0, "Ninguno", "Ninguno", "Gratis"

def registrar_piloto():
    """Registra un nuevo piloto con su situación y monto."""
    print("\n--- REGISTRAR NUEVO PILOTO ---")
    nombre = pedir_nombre()

    opcion = pedir_validar(
        "Situación (1-Pagó Tarifa, 2-Solo Seguro, 3-Monto Personalizado, 4-Adeuda, 5-Gratis): ",
        1, 5
    )
    monto, medio, dest, situacion = resolver_situacion(opcion)

    lista_nombres.append(nombre)
    lista_montos.append(monto)
    lista_medios.append(medio)
    lista_destinados.append(dest)
    lista_situaciones.append(situacion)

    historial_cambios.append(
        "ALTA PILOTO: " + nombre +
        " | Situación: " + situacion +
        " | Monto: $" + str(monto) +
        " | Medio: " + medio +
        " | Para: " + dest
    )
    print("\033[92mPiloto registrado con éxito.\033[0m")

def modificar_o_eliminar():
    """Permite editar o borrar un piloto ya registrado."""
    if len(lista_nombres) == 0:
        print("No hay pilotos registrados.")
        return

    print("\n--- MODIFICAR / ELIMINAR PILOTO ---")
    for i in range(len(lista_nombres)):
        print(" ", i + 1, "-", lista_nombres[i],
              "| Situación:", lista_situaciones[i],
              "| Monto: $", lista_montos[i],
              "| Medio:", lista_medios[i],
              "| Para:", lista_destinados[i])

    indice = pedir_validar("Seleccione el número del piloto: ", 1, len(lista_nombres)) - 1

    #todos los valores originales para el historial
    nom_orig = lista_nombres[indice]
    mont_orig = lista_montos[indice]
    sit_orig = lista_situaciones[indice]
    med_orig = lista_medios[indice]
    dest_orig = lista_destinados[indice]

    accion = pedir_validar("¿Qué desea hacer? (1-Modificar, 2-Eliminar): ", 1, 2)

    if accion == 2:
        lista_nombres.pop(indice)
        lista_montos.pop(indice)
        lista_medios.pop(indice)
        lista_destinados.pop(indice)
        lista_situaciones.pop(indice)
        historial_cambios.append(
            "BAJA PILOTO: " + nom_orig +
            " | Situación: " + sit_orig +
            " | Monto: $" + str(mont_orig) +
            " | Medio: " + med_orig +
            " | Para: " + dest_orig
        )
        print("\033[92mPiloto eliminado.\033[0m")

    else:
        print("Deje en blanco y presione Enter para conservar el valor actual.")

        nuevo_nombre = input("Nuevo nombre [" + nom_orig + "]: ")
        if nuevo_nombre == "":
            nuevo_nombre = nom_orig
        else:
            while len(nuevo_nombre) < 3:
                nuevo_nombre = input("\033[91mMínimo 3 caracteres. Reingrese: \033[0m")

        opcion = pedir_validar(
            "Nueva situación (1-Pagado, 2-Solo Seguro, 3-Personalizado, 4-Adeuda, 5-Gratis): ",
            1, 5
        )
        nuevo_monto, nuevo_medio, nuevo_dest, nueva_sit = resolver_situacion(opcion)

        historial_cambios.append(
            "MODIFICACIÓN PILOTO: " + nom_orig + " -> " + nuevo_nombre +
            " | Situación: " + sit_orig + " -> " + nueva_sit +
            " | Monto: $" + str(mont_orig) + " -> $" + str(nuevo_monto) +
            " | Medio: " + med_orig + " -> " + nuevo_medio +
            " | Para: " + dest_orig + " -> " + nuevo_dest
        )

        lista_nombres[indice] = nuevo_nombre
        lista_montos[indice] = nuevo_monto
        lista_medios[indice] = nuevo_medio
        lista_destinados[indice] = nuevo_dest
        lista_situaciones[indice] = nueva_sit

        print("\033[92mPiloto modificado con éxito.\033[0m")

def menu_gastos():
    """Submenú completo para agregar, modificar, eliminar y ver gastos."""
    while True:
        print("\n--- GASTOS EXTRA ---")
        print("1. Agregar gasto")
        print("2. Modificar / Eliminar gasto")
        print("3. Ver resumen de gastos")
        print("4. Volver al menú principal")

        opcion = pedir_validar("Seleccione (1-4): ", 1, 4)

        if opcion == 1:
            agregar_gasto()
        elif opcion == 2:
            modificar_o_eliminar_gasto()
        elif opcion == 3:
            ver_resumen_gastos()
        else:
            break


def agregar_gasto():
    """Agrega un nuevo gasto a la lista."""
    descripcion = input("Descripción del gasto: ")
    while len(descripcion) < 2:
        descripcion = input("\033[91mDescripción muy corta. Reingrese: \033[0m")
    monto_gasto = pedir_float_positivo("Monto del gasto: $")
    lista_gastos.append([descripcion, monto_gasto])
    historial_cambios.append(
        "GASTO AGREGADO: \"" + descripcion + "\" | $" + str(monto_gasto)
    )
    print("\033[92mGasto registrado.\033[0m")


def modificar_o_eliminar_gasto():
    """Permite editar o borrar un gasto ya registrado."""
    if len(lista_gastos) == 0:
        print("No hay gastos registrados.")
        return

    print("\nGastos registrados:")
    for i in range(len(lista_gastos)):
        print(" ", i + 1, "-", lista_gastos[i][0], "-> $", lista_gastos[i][1])

    indice = pedir_validar("Seleccione el número del gasto: ", 1, len(lista_gastos)) - 1

    desc_orig = lista_gastos[indice][0]
    monto_orig = lista_gastos[indice][1]

    accion = pedir_validar("¿Qué desea hacer? (1-Modificar, 2-Eliminar): ", 1, 2)

    if accion == 2:
        lista_gastos.pop(indice)
        historial_cambios.append(
            "GASTO ELIMINADO: \"" + desc_orig + "\" | $" + str(monto_orig)
        )
        print("\033[92mGasto eliminado.\033[0m")

    else:
        print("Deje en blanco y presione Enter para conservar el valor actual.")

        nueva_desc = input("Nueva descripción [" + desc_orig + "]: ")
        if nueva_desc == "":
            nueva_desc = desc_orig
        else:
            while len(nueva_desc) < 2:
                nueva_desc = input("\033[91mMínimo 2 caracteres. Reingrese: \033[0m")

        print("Monto actual: $", monto_orig)
        cambiar_monto = pedir_validar("¿Desea cambiar el monto? (1-Sí, 2-No): ", 1, 2)
        if cambiar_monto == 1:
            nuevo_monto = pedir_float_positivo("Nuevo monto: $")
        else:
            nuevo_monto = monto_orig

        historial_cambios.append(
            "GASTO MODIFICADO: \"" + desc_orig + "\" -> \"" + nueva_desc + "\"" +
            " | $" + str(monto_orig) + " -> $" + str(nuevo_monto)
        )

        lista_gastos[indice][0] = nueva_desc
        lista_gastos[indice][1] = nuevo_monto

        print("\033[92mGasto modificado con éxito.\033[0m")


def ver_resumen_gastos():
    """Muestra el detalle de todos los gastos ingresados."""
    if len(lista_gastos) == 0:
        print("No hay gastos registrados.")
        return

    print("\n======= RESUMEN DE GASTOS EXTRA =======")
    total_gastos = 0.0
    for i in range(len(lista_gastos)):
        print(" -", lista_gastos[i][0], "-> $", lista_gastos[i][1])
        total_gastos = total_gastos + lista_gastos[i][1]
    print("TOTAL GASTOS: $", total_gastos)
    print("========================================")

def mostrar_reporte_financiero():
    """Calcula y muestra el balance completo incluyendo gastos."""
    total = len(lista_montos)
    if total == 0:
        print("No hay pilotos registrados.")
        return

    pagados = lista_situaciones.count("Pagado")
    solo_seg = lista_situaciones.count("Solo Seguro")
    personal = lista_situaciones.count("Personalizado")
    adeuda = lista_situaciones.count("Adeuda")
    gratis = lista_situaciones.count("Gratis")
    bruto = sum(lista_montos)

    retencion_seguro = total * 40000.0
    neto_antes_gastos = bruto - retencion_seguro

    total_gastos = 0.0
    for g in lista_gastos:
        total_gastos = total_gastos + g[1]

    neto_final = neto_antes_gastos - total_gastos
    porcentaje_seguro = calcular_porcentaje(retencion_seguro, bruto)

    print("\n====== ESTADÍSTICAS Y CIERRE DE CAJA ======")
    print("Pilotos:")
    print(" Tarifa fija :", pagados)
    print(" Solo seguro :", solo_seg)
    print(" Personalizado :", personal)
    print(" Adeudan :", adeuda)
    print(" Gratis :", gratis)
    print(" TOTAL :", total)
    print("--------------------------------------------")
    print("Recaudación Bruta : $", bruto)
    print("Retención Seguro (x piloto): $", retencion_seguro)
    print("Neto antes de gastos : $", neto_antes_gastos)
    print("Total Gastos Extra : $", total_gastos)
    print("FONDO NETO ORGANIZACIÓN : $", neto_final)
    print("Impacto del seguro :", round(porcentaje_seguro, 2), "%")
    print("============================================")

def auditar_por_montos():
    """Agrupa y muestra los pilotos según su monto/situación."""
    if len(lista_nombres) == 0:
        print("No hay pilotos para clasificar.")
        return

    montos_fijos = [0.0, 40000.0, 80000.0, 100000.0, 120000.0]
    montos_personalizados = []
    for m in lista_montos:
        if m not in montos_fijos and m not in montos_personalizados:
            montos_personalizados.append(m)

    print("\n\033[1m======= CLASIFICACIÓN DE PILOTOS =======\033[0m")

    grupos = [
        ("Anticipada ($80.000)", 80000.0, None),
        ("Normal ($100.000)", 100000.0, None),
        ("Tardía ($120.000)", 120000.0, None),
        ("Solo Seguro ($40.000)", 40000.0, None),
        ("Deudores ($0)", None, "Adeuda"),
        ("Gratis ($0)", None, "Gratis"),
    ]

    for titulo, monto_grupo, sit_grupo in grupos:
        print("\n--- Grupo:", titulo)
        hubo = False
        for i in range(len(lista_nombres)):
            coincide_monto = (monto_grupo is not None and lista_montos[i] == monto_grupo)
            coincide_sit = (sit_grupo is not None and lista_situaciones[i] == sit_grupo)
            if coincide_monto or coincide_sit:
                if lista_montos[i] > 0:
                    print(" •", lista_nombres[i],
                          "| Vía:", lista_medios[i],
                          "| Para:", lista_destinados[i])
                else:
                    print(" •", lista_nombres[i])
                hubo = True
        if not hubo:
            print(" Sin pilotos en este grupo.")

    for monto_p in montos_personalizados:
        print("\n--- Grupo: Monto Personalizado ($" + str(monto_p) + ")")
        for i in range(len(lista_nombres)):
            if lista_montos[i] == monto_p:
                print(" •", lista_nombres[i],
                      "| Vía:", lista_medios[i],
                      "| Para:", lista_destinados[i])

def ver_historial():
    """Muestra todos los cambios registrados en la sesión."""
    if len(historial_cambios) == 0:
        print("No se registraron cambios en esta sesión.")
        return

    print("\n====== HISTORIAL DE CAMBIOS ======")
    for i in range(len(historial_cambios)):
        print(" ", i + 1, "->", historial_cambios[i])
    print("==================================")

def principal():
    lista_nombres.clear()
    lista_montos.clear()
    lista_medios.clear()
    lista_destinados.clear()
    lista_situaciones.clear()
    for i in range(1, 111):
        lista_nombres.append("Piloto " + str(i))
        if i % 3 == 0:
            lista_montos.append(80000.0)
            lista_situaciones.append("Pagado")
            lista_medios.append("Efectivo")
            lista_destinados.append("Mercedes")
        elif i % 3 == 1:
            lista_montos.append(0.0)
            lista_situaciones.append("Adeuda")
            lista_medios.append("Ninguno")
            lista_destinados.append("Ninguno")
        else:
            lista_montos.append(0.0)
            lista_situaciones.append("Gratis")
            lista_medios.append("Ninguno")
            lista_destinados.append("Ninguno")
    while True:
        print("\n\033[1m=== MENÚ DE TESORERÍA - ENDURO ===\033[0m")
        print("1. Registrar piloto")
        print("2. Modificar / Eliminar piloto")
        print("3. Ver balance de caja y seguro")
        print("4. Ver listas agrupadas por monto")
        print("5. Gastos extra de la organización")
        print("6. Historial de cambios")
        print("7. Salir")

        opcion = pedir_validar("Seleccione una opción (1-7): ", 1, 7)

        if opcion == 1:
            registrar_piloto()
        elif opcion == 2:
            modificar_o_eliminar()
        elif opcion == 3:
            mostrar_reporte_financiero()
        elif opcion == 4:
            auditar_por_montos()
        elif opcion == 5:
            menu_gastos()
        elif opcion == 6:
            ver_historial()
        elif opcion == 7:
            print("Sistema cerrado. ¡Éxitos en la carrera!")
            break
        
principal()

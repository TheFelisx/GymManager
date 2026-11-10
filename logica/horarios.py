"""Reglas de horario de los planes y validación de planes nuevos."""
from datetime import datetime

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"] 

# Valida y estandariza un texto de hora al formato HH:MM, devolviendo None si es inválido.
def parsear_hora(texto: str):
    
    texto_limpio = (texto or "").strip()
    try:
        objeto_hora = datetime.strptime(texto_limpio, "%H:%M")
        hora_estandarizada = objeto_hora.strftime("%H:%M")
        return hora_estandarizada
    except ValueError:
        return None

# Convierte un texto de días separados por comas en una lista ordenada de números enteros.
def _lista_dias(dias_texto: str):
    
    dias_limpios = dias_texto or ""
    partes = dias_limpios.split(",")
    
    lista_numeros = []
    for parte in partes:
        parte_limpia = parte.strip()
        if parte_limpia.isdigit():
            lista_numeros.append(int(parte_limpia))
            
    return sorted(lista_numeros)

# Traduce los números de los días a un texto legible (ej: 'Todos los días', 'Lun–Vie' o 'Lun, Mié').
def formato_dias(dias_texto: str) -> str:
    
    lista_indices = _lista_dias(dias_texto)
    
    if len(lista_indices) == 7:
        return "Todos los días"
        
    if len(lista_indices) > 2:
        primer_dia = lista_indices[0]
        ultimo_dia = lista_indices[-1]
        rango_esperado = list(range(primer_dia, ultimo_dia + 1))
        
        if lista_indices == rango_esperado:
            return f"{DIAS[primer_dia]}–{DIAS[ultimo_dia]}"
            
    lista_nombres = []
    for indice in lista_indices:
        lista_nombres.append(DIAS[indice])
        
    return ", ".join(lista_nombres)

# Genera un resumen limpio combinando las horas y los días permitidos del plan.
def resumen_horario(plan) -> str:
    
    hora_inicio = plan["hora_inicio"]
    hora_fin = plan["hora_fin"]
    
    if hora_inicio == "00:00" and hora_fin == "23:59":
        texto_horas = "Todo el día"
    else:
        texto_horas = f"{hora_inicio}–{hora_fin}"
        
    texto_dias = formato_dias(plan["dias"])
    return f"{texto_horas} · {texto_dias}"


# Verifica si la fecha y hora actual permiten el ingreso del socio según las reglas de su plan.
def dentro_de_horario(plan, ahora=None):
    
    if ahora is None:
        ahora = datetime.now()
        
    dia_actual_numero = ahora.weekday()
    dias_permitidos = _lista_dias(plan["dias"])
    
    if dia_actual_numero not in dias_permitidos:
        nombre_dia = DIAS[dia_actual_numero]
        return False, f"Su plan no incluye el día {nombre_dia}"
        
    hora_actual_texto = ahora.strftime("%H:%M")
    hora_inicio_plan = plan["hora_inicio"]
    hora_fin_plan = plan["hora_fin"]
    
    esta_en_rango_horario = hora_inicio_plan <= hora_actual_texto <= hora_fin_plan
    if not esta_en_rango_horario:
        return False, f"Fuera del horario de su plan ({hora_inicio_plan}–{hora_fin_plan})"
        
    return True, ""

# Valida la configuración de un plan nuevo y devuelve la lista de errores o los datos listos para guardar.
def validar_plan(nombre, precio, duracion, hora_inicio, hora_fin, dias_idx):
    
    lista_errores = []
    
    if not nombre.strip():
        lista_errores.append("El nombre del plan es obligatorio.")
        
    precio_limpio = precio.strip()
    if not precio_limpio.isdigit() or int(precio_limpio) <= 0:
        lista_errores.append("El precio debe ser un entero mayor que 0.")
        
    duracion_limpia = duracion.strip()
    if not duracion_limpia.isdigit():
        lista_errores.append("La duración debe ser un número de días entre 1 y 3650.")
    else:
        duracion_dias = int(duracion_limpia)
        if duracion_dias < 1 or duracion_dias > 3650:
            lista_errores.append("La duración debe ser un número de días entre 1 y 3650.")
            
    hora_inicio_ok = parsear_hora(hora_inicio)
    hora_fin_ok = parsear_hora(hora_fin)
    
    if hora_inicio_ok is None or hora_fin_ok is None:
        lista_errores.append("Las horas deben tener formato HH:MM (ej. 06:00).")
    elif hora_inicio_ok >= hora_fin_ok:
        lista_errores.append("La hora de inicio debe ser anterior a la hora de término.")
        
    if not dias_idx:
        lista_errores.append("Selecciona al menos un día.")
        
    if lista_errores:
        return lista_errores, None
        
    lista_dias_texto =[]
    for dia in sorted(dias_idx):
        lista_dias_texto.append(str(dia))
    dias_formateados = ",".join(lista_dias_texto)
    
    datos_plan = {
        "nombre": nombre.strip(),
        "precio": int(precio_limpio),
        "duracion": int(duracion_limpia),
        "hora_inicio": hora_inicio_ok,
        "hora_fin": hora_fin_ok,
        "dias": dias_formateados
    }
    
    return [], datos_plan

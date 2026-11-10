"""Validaciones de negocio (capa lógica). Se usan antes de guardar en la BD."""
import re
from datetime import date, datetime

EDAD_MINIMA = 14

#limpiar rut: ejemplo 21.503.224-1 -> 215032241

def limpiar_rut(rut: str) -> str:
    return re.sub(r"[^0-9kK]", "", rut or "").upper()

# Algoritmo del Modulo 11 n se nesesita un numero entero por eso se crea el limpia rut
def validar_rut(rut: str) -> bool:
    r = limpiar_rut(rut)
    if len(r) < 2 or not r[:-1].isdigit():
        return False
    cuerpo, dv = r[:-1], r[-1]
    suma, mult = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mult
        mult = 2 if mult == 7 else mult + 1
    esperado = 11 - (suma % 11)
    esperado = "0" if esperado == 11 else "K" if esperado == 10 else str(esperado)
    return dv == esperado

#vuelve el rut a su estado original y si no fue escrito haci lo representa haci 215032241-> 21.503.224-1
def formatear_rut(rut: str) -> str:
    rut_limpio = limpiar_rut(rut)
    if len(rut_limpio) < 2:
        return rut_limpio
    cuerpo_plano = rut_limpio[:-1]
    digito_verificador = rut_limpio[-1]
    cuerpo_numerico = int(cuerpo_plano)
    cuerpo_con_comas = f"{cuerpo_numerico:,}"
    cuerpo_con_puntos = cuerpo_con_comas.replace(",", ".")
    rut_formateado = f"{cuerpo_con_puntos}-{digito_verificador}"
    
    return rut_formateado

# Convierte un texto DD/MM/AAAA a fecha real, devolviendo None si el formato es inválido.
def parsear_fecha(texto: str):
    texto_limpio = texto.strip()
    try:
        fecha_con_hora = datetime.strptime(texto_limpio, "%d/%m/%Y")
        return fecha_con_hora.date()
    except ValueError:
        return None

# Calcula la edad exacta comparando la fecha de nacimiento con la fecha actual.
def calcular_edad(fecha_nacimiento: date, fecha_actual: date | None = None) -> int:
    if fecha_actual is None:
        fecha_actual = date.today()
        
    edad_preliminar = fecha_actual.year - fecha_nacimiento.year
    todavia_no_cumple_anios = (fecha_actual.month, fecha_actual.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    
    if todavia_no_cumple_anios:
        return edad_preliminar - 1
    
    return edad_preliminar

# Verifica si el texto tiene una estructura válida de correo electrónico (ejemplo@dominio.com)
def validar_correo(correo: str) -> bool:
    
    correo_limpio = (correo or "").strip()
    patron_correo = r"[\w.+-]+@[\w-]+(\.[\w-]+)+"
    
    coincide = re.fullmatch(patron_correo, correo_limpio)
    return coincide is not None


# Valida números telefónicos de 8 a 12 dígitos, permitiendo un "+" opcional y quitando espacios
def validar_telefono(tel: str) -> bool:
    
    telefono_limpio = (tel or "").replace(" ", "")
    patron_telefono = r"\+?\d{8,12}"
    
    coincide = re.fullmatch(patron_telefono, telefono_limpio)
    return coincide is not None

# Revisa todos los datos de un socio y devuelve una lista con los errores encontrados junto a la fecha procesada.
def validar_socio(rut, nombres, apellidos, fecha_nacimiento, correo, telefono):
   
    lista_errores = []
    
    # 1. Validación del RUT
    if not validar_rut(rut):
        lista_errores.append("RUT inválido.")
        
    # 2. Validación de nombres y apellidos (quitando espacios vacíos)
    nombres_limpios = nombres.strip()
    apellidos_limpios = apellidos.strip()
    if not nombres_limpios or not apellidos_limpios:
        lista_errores.append("Nombres y apellidos son obligatorios.")
        
    # 3. Validación de la fecha de nacimiento y edad
    fecha_parseada = parsear_fecha(fecha_nacimiento)
    if fecha_parseada is None:
        lista_errores.append("Fecha de nacimiento inválida (use DD/MM/AAAA).")
    elif fecha_parseada > date.today():
        lista_errores.append("La fecha de nacimiento no puede ser futura.")
    elif calcular_edad(fecha_parseada) < EDAD_MINIMA:
        lista_errores.append(f"El socio debe tener al menos {EDAD_MINIMA} años.")
        
    # 4. Validación de datos de contacto
    if not validar_correo(correo):
        lista_errores.append("Correo electrónico inválido.")
        
    if not validar_telefono(telefono):
        lista_errores.append("Teléfono inválido (8 a 12 dígitos).")
        
    # Devolvemos el reporte de errores y la fecha lista para usar
    return lista_errores, fecha_parseada

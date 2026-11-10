"""Autenticación y permisos por rol (RBAC)."""
import re
import bcrypt

# permisos para cada rol
PERMISOS = {
    "administrador": ["socios", "enrolar", "pagos", "planes", "usuarios", "totem", "finanzas"],
    "recepcionista": ["socios", "enrolar", "pagos", "totem"],
    "guardia": ["totem"],
}

# Transforma una contraseña de texto en un código encriptado en la base de datos.
def hash_clave(clave_texto: str) -> str:
    
    clave_en_bytes = clave_texto.encode()
    texto_aleatorio = bcrypt.gensalt()
    hash_en_bytes = bcrypt.hashpw(clave_en_bytes, texto_aleatorio)
    
    return hash_en_bytes.decode()

# Compara la contraseña escrita por el empleado con el código seguro de la base de datos.
def verificar_clave(clave_ingresada: str, hash_guardado: str) -> bool:
    
    try:
        clave_bytes = clave_ingresada.encode()
        hash_bytes = hash_guardado.encode()
        
        return bcrypt.checkpw(clave_bytes, hash_bytes)
        
    except ValueError:
        return False

#devuelve los permiso de cada rol

def modulos_permitidos(rol: str):
    return PERMISOS.get(rol, [])

# Los roles que existen en el sistema son las mismas claves de PERMISOS.
# Así los roles se definen en un solo lugar y el formulario siempre muestra los correctos.
ROLES = list(PERMISOS.keys())


# Revisa los datos del formulario "Nuevo usuario", uno por uno.
# Devuelve una lista con los mensajes de error; si la lista viene vacía, todo está bien.
def validar_usuario(nombre_usuario: str, clave: str, clave_repetida: str, rol: str):
    errores = []

    # ---- 1) El nombre de usuario ----
    # Solo se permiten letras, números, punto, guion y guion bajo, con un largo de 3 a 30 caracteres.
    patron_nombre_valido = r"[A-Za-z0-9._-]{3,30}"
    nombre_cumple_el_patron = re.fullmatch(patron_nombre_valido, nombre_usuario)
    if not nombre_cumple_el_patron:
        errores.append("El usuario debe tener de 3 a 30 caracteres: letras, números, punto, guion o guion bajo (sin espacios).")

    # ---- 2) La contraseña ----
    cantidad_de_caracteres = len(clave)
    cantidad_de_bytes = len(clave.encode())  # bcrypt cuenta bytes, no letras
    clave_igual_al_usuario = clave.lower() == nombre_usuario.lower()

    if cantidad_de_caracteres < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres.")
    elif cantidad_de_bytes > 72:
        errores.append("La contraseña es demasiado larga (máximo 72 caracteres).")
    elif clave_igual_al_usuario:
        errores.append("La contraseña no puede ser igual al nombre de usuario.")

    # ---- 3) Que haya escrito la misma contraseña las dos veces ----
    if clave != clave_repetida:
        errores.append("Las contraseñas no coinciden.")

    # ---- 4) El rol ----
    if rol not in ROLES:
        errores.append("Selecciona un rol válido.")

    return errores
"""Fotos de los socios: se validan, se reducen y se guardan en la carpeta fotos/."""
import os
from PIL import Image, ImageOps
from logica.validaciones import limpiar_rut

# Configuración global: define la ruta de guardado y los límites de tamaño y resolución para las fotos.
CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fotos")
MAX_MB = 10
LADO_MAX = 600


# Verifica si el archivo en la ruta es una imagen válida y cumple con el límite de peso permitido.
def validar_imagen(ruta_archivo):
    
    try:
        peso_maximo_en_bytes = MAX_MB * 1024 * 1024
        peso_actual_archivo = os.path.getsize(ruta_archivo)
        
        if peso_actual_archivo > peso_maximo_en_bytes:
            return f"La imagen pesa más de {MAX_MB} MB."
            
        with Image.open(ruta_archivo) as imagen_objeto:
            imagen_objeto.verify()
            
    except OSError:
        return "El archivo no es una imagen válida."
        
    return None


# Procesa, reduce y guarda la foto del socio en formato JPEG usando su RUT limpio como nombre.
def guardar_foto(ruta_origen, rut_socio):
    
    os.makedirs(CARPETA, exist_ok=True)
    
    nombre_archivo = f"{limpiar_rut(rut_socio)}.jpg"
    ruta_destino_completa = os.path.join(CARPETA, nombre_archivo)
    
    with Image.open(ruta_origen) as imagen_original:
        imagen_rotada = ImageOps.exif_transpose(imagen_original)
        imagen_lista = imagen_rotada.convert("RGB")
        
        dimensiones_maximas = (LADO_MAX, LADO_MAX)
        imagen_lista.thumbnail(dimensiones_maximas)
        
        imagen_lista.save(ruta_destino_completa, "JPEG", quality=88)
        
    return nombre_archivo


# Devuelve la ruta física completa de la foto si existe en el disco duro, o None si no se encuentra.
def ruta_foto(nombre_archivo):
    
    if not nombre_archivo:
        return None
        
    nombre_seguro = os.path.basename(nombre_archivo)
    ruta_completa = os.path.join(CARPETA, nombre_seguro)
    
    if os.path.isfile(ruta_completa):
        return ruta_completa
        
    return None

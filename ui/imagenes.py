import customtkinter as ctk
from PIL import Image, ImageOps

# Adapta una imagen de disco a un tamaño cuadrado proporcional para la interfaz sin deformarla.
def miniatura(ruta_archivo, lado_contenedor):
    try:
        with Image.open(ruta_archivo) as imagen_original:
            imagen_rotada = ImageOps.exif_transpose(imagen_original)
            imagen_objeto = imagen_rotada.convert("RGB").copy()
    except OSError:
        return None
        
    ancho_original, alto_original = imagen_objeto.size
    lado_mas_largo = max(ancho_original, alto_original)
    
    escala_proporcional = lado_contenedor / lado_mas_largo
    
    ancho_final = max(1, int(ancho_original * escala_proporcional))
    alto_final = max(1, int(alto_original * escala_proporcional))
    
    imagen_lista = ctk.CTkImage(
        light_image=imagen_objeto, 
        dark_image=imagen_objeto,
        size=(ancho_final, alto_final)
    )
    
    return imagen_lista

# Crea una imagen completamente invisible del tamaño solicitado para limpiar los visores de fotos de forma segura.
def vacia(lado_contenedor):
    imagen_transparente = Image.new("RGBA", (lado_contenedor, lado_contenedor), (0, 0, 0, 0))
    
    imagen_lista = ctk.CTkImage(
        imagen_transparente, 
        size=(lado_contenedor, lado_contenedor)
    )
    
    return imagen_lista

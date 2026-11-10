"""Colores, tema día/noche y estilo común de la interfaz."""
import json
import os
from tkinter import ttk
import customtkinter as ctk

VERDE = "#2e9e5b"
ROJO = "#d64545"
AMARILLO = "#d9a400"
AZUL = "#1f6aa5"
GRIS = "#2b2b2b"

MODO = "dark" 
_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

# Define las paletas de colores verticales para los fondos, textos y estados de socios en modos oscuro y claro.
PALETAS = {
    "dark": {
        "fondo": "#2b2b2b",
        "cabecera": "#1f1f1f",
        "texto": "white",
        "activo": "#5fd38d",
        "vencido": "#ff7b7b",
        "baja": "#9a9a9a"
    },
    "light": {
        "fondo": "#ffffff",
        "cabecera": "#e3e3e3",
        "texto": "#1a1a1a",
        "activo": "#1b7f43",
        "vencido": "#c0392b",
        "baja": "#777777"
    }
}

# Toma un valor numérico bruto y lo convierte en un texto formateado con signo de peso y puntos de miles.
def moneda(monto_numero) -> str:
    monto_entero = int(monto_numero)
    formato_comas = f"{monto_entero:,}"
    formato_puntos = formato_comas.replace(",", ".")
    
    texto_moneda = f"${formato_puntos}"
    return texto_moneda

# Lee el archivo de configuración local para recuperar el modo visual preferido por el usuario.
def cargar_tema() -> str:
    try:
        with open(_CONFIG, "r", encoding="utf-8") as archivo_configuracion:
            datos_leidos = json.load(archivo_configuracion)
            modo_visual = datos_leidos.get("tema", "dark")
            
        if modo_visual in PALETAS:
            return modo_visual
        else:
            return "dark"
            
    except (OSError, ValueError):
        return "dark"

# Cambia en tiempo real el modo de color de la interfaz gráfica y guarda la preferencia en el disco duro.
def aplicar_tema(modo_visual: str):
    global MODO
    MODO = modo_visual
    
    ctk.set_appearance_mode(modo_visual)
    estilo_tabla()
    
    try:
        with open(_CONFIG, "w", encoding="utf-8") as archivo_configuracion:
            json.dump({"tema": modo_visual}, archivo_configuracion)
    except OSError:
        pass

# Configura y aplica los colores del tema actual junto a las tipografías para las tablas de la interfaz.
def estilo_tabla():
    paleta_colores = PALETAS[MODO]
    gestor_estilos = ttk.Style()
    
    gestor_estilos.theme_use("clam")
    
    gestor_estilos.configure(
        "Treeview", 
        background=paleta_colores["fondo"], 
        fieldbackground=paleta_colores["fondo"],
        foreground=paleta_colores["texto"], 
        rowheight=28, 
        borderwidth=0, 
        font=("Segoe UI", 11)
    )
    
    gestor_estilos.configure(
        "Treeview.Heading", 
        background=paleta_colores["cabecera"], 
        foreground=paleta_colores["texto"],
        font=("Segoe UI", 11, "bold"), 
        relief="flat"
    )
    
    gestor_estilos.map(
        "Treeview", 
        background=[("selected", AZUL)], 
        foreground=[("selected", "white")]
    )

# Construye un componente de tabla con su barra de desplazamiento vertical integrada y formateada.
def tabla(componente_padre, lista_columnas, lista_anchos):
    marco_contenedor = ctk.CTkFrame(componente_padre, fg_color="transparent")
    
    tabla_datos = ttk.Treeview(
        marco_contenedor, 
        columns=lista_columnas, 
        show="headings", 
        selectmode="browse"
    )
    
    for nombre_columna, ancho_columna in zip(lista_columnas, lista_anchos):
        tabla_datos.heading(nombre_columna, text=nombre_columna)
        tabla_datos.column(nombre_columna, width=ancho_columna, anchor="w")
        
    barra_desplazamiento = ttk.Scrollbar(
        marco_contenedor, 
        orient="vertical", 
        command=tabla_datos.yview
    )
    
    tabla_datos.configure(yscrollcommand=barra_desplazamiento.set)
    
    tabla_datos.pack(side="left", fill="both", expand=True)
    barra_desplazamiento.pack(side="right", fill="y")
    
    aplicar_tags(tabla_datos)
    
    return marco_contenedor, tabla_datos

# Configura las etiquetas de color para destacar de forma visual a los socios según su estado de vigencia.
def aplicar_tags(tabla_datos):
    paleta_colores = PALETAS[MODO]
    
    tabla_datos.tag_configure("Activo", foreground=paleta_colores["activo"])
    tabla_datos.tag_configure("Vencido", foreground=paleta_colores["vencido"])
    tabla_datos.tag_configure("Baja", foreground=paleta_colores["baja"])

# Busca de forma recursiva todas las tablas abiertas en la pantalla actual para actualizar sus colores en tiempo real.
def recolorear_tablas(componente_raiz):
    for componente_hijo in componente_raiz.winfo_children():
        if isinstance(componente_hijo, ttk.Treeview):
            aplicar_tags(componente_hijo)
            
        recolorear_tablas(componente_hijo)

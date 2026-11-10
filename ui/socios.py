"""Interfaz gráfica para la gestión, registro y edición de socios del gimnasio."""
import customtkinter as ctk
from tkinter import filedialog, messagebox

from db import repositorio as repo
from logica import fotos
from logica.horarios import resumen_horario
from logica.validaciones import validar_correo, validar_telefono
from ui import imagenes
from ui.estilos import ROJO, tabla, moneda

COLUMNAS_TABLA_SOCIOS = ("RUT", "Nombre", "Plan", "Vence", "Estado")

# Clase gráfica que construye el panel principal de administración de socios con búsqueda en tiempo real.
class SociosFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        
        ctk.CTkLabel(
            self, 
            text="Socios", 
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        barra_herramientas = ctk.CTkFrame(self, fg_color="transparent")
        barra_herramientas.pack(fill="x", pady=(0, 10))
        
        self.campo_busqueda = ctk.CTkEntry(
            barra_herramientas, 
            placeholder_text="Buscar por RUT, nombre o apellido…", 
            width=380, 
            height=36
        )
        self.campo_busqueda.pack(side="left")
        
        # Enlaza la soltura de teclas para activar la búsqueda instantánea en la planilla
        self.campo_busqueda.bind("<KeyRelease>", self.detectar_escritura_busqueda)
        
        ctk.CTkButton(
            barra_herramientas, 
            text="Editar", 
            width=100, 
            command=self.editar
        ).pack(side="left", padx=(15, 5))
        
        ctk.CTkButton(
            barra_herramientas, 
            text="Dar de baja", 
            width=110, 
            fg_color=ROJO, 
            hover_color="#a33",
            command=self.baja
        ).pack(side="left")

        # Inicializamos la tabla utilizando los anchos proporcionales para cada columna de información
        anchos_columnas = (140, 280, 120, 120, 100)
        marco_tabla, self.tabla_socios = tabla(self, COLUMNAS_TABLA_SOCIOS, anchos_columnas)
        marco_tabla.pack(fill="both", expand=True)
        
        self.cargar()

    # Captura la soltura de cualquier tecla en el cuadro de texto para filtrar los registros al instante.
    def detectar_escritura_busqueda(self, evento_teclado):
        self.cargar()
    # Limpia la planilla y la vuelve a llenar en tiempo real con los socios que coincidan con la búsqueda.
    def cargar(self):
        # Removemos todos los registros visuales actuales de la tabla para hacer un rellenado limpio
        for registro_visual in self.tabla_socios.get_children():
            self.tabla_socios.delete(registro_visual)
            
        texto_filtro = self.campo_busqueda.get()
        lista_socios_encontrados = repo.buscar_socios(texto_filtro)
        
        for socio in lista_socios_encontrados:
            situacion_membresia = repo.estado_socio(socio)
            nombre_completo = f"{socio['nombres']} {socio['apellidos']}"
            
            valores_fila = (
                socio["rut"], 
                nombre_completo, 
                socio["plan"], 
                socio["fecha_venc"], 
                situacion_membresia
            )
            
            self.tabla_socios.insert(
                "", 
                "end", 
                iid=socio["id"], 
                tags=(situacion_membresia,),
                values=valores_fila
            )

    # Identifica qué fila tiene seleccionada el usuario con el ratón y recupera la ficha completa del socio.
    def _seleccionado(self):
        filas_seleccionadas = self.tabla_socios.selection()
        
        if not filas_seleccionadas:
            messagebox.showinfo("Socios", "Selecciona un socio de la tabla.")
            return None
            
        id_fila_marcada = filas_seleccionadas[0]
        datos_celdas = self.tabla_socios.item(id_fila_marcada)["values"]
        rut_socio_marcado = datos_celdas[0]
        
        return repo.obtener_socio_por_rut(rut_socio_marcado)

    # Procesa la deshabilitación del socio seleccionado desplegando una ventana de confirmación interactiva.
    def baja(self):
        socio_marcado = self._seleccionado()
        
        if socio_marcado:
            nombre_socio = f"{socio_marcado['nombres']} {socio_marcado['apellidos']}"
            pregunta_confirmacion = f"¿Dar de baja a {nombre_socio}?"
            
            if messagebox.askyesno("Dar de baja", pregunta_confirmacion):
                repo.dar_de_baja(socio_marcado["id"])
                self.cargar()


    # Abre una ventana flotante modal que permite modificar la información personal y el plan del socio seleccionado.
    def editar(self):
        socio_marcado = self._seleccionado()
        if not socio_marcado:
            return
            
        ventana_edicion = ctk.CTkToplevel(self)
        ventana_edicion.title("Editar socio")
        ventana_edicion.geometry("480x640")
        ventana_edicion.grab_set()
        
        # Recuperamos los planes vigentes más el plan actual del socio (en caso de que sea un plan antiguo inactivo)
        todos_los_planes = repo.listar_planes(solo_activos=False)
        lista_planes_filtrados = []
        lista_nombres_combobox = []
        
        for plan in todos_los_planes:
            if plan["activo"] or plan["id"] == socio_marcado["plan_id"]:
                lista_planes_filtrados.append(plan)
                
                texto_descriptivo = f"{plan['nombre']} — {moneda(plan['precio'])} · {resumen_horario(plan)}"
                lista_nombres_combobox.append(texto_descriptivo)
                
        diccionario_entradas_edicion = {}
        campos_a_editar = (
            ("nombres", "Nombres"), 
            ("apellidos", "Apellidos"), 
            ("correo", "Correo"), 
            ("telefono", "Teléfono")
        )
        
        for clave, etiqueta_texto in campos_a_editar:
            ctk.CTkLabel(ventana_edicion, text=etiqueta_texto).pack(anchor="w", padx=30, pady=(10, 0))
            campo_entrada = ctk.CTkEntry(ventana_edicion, width=340)
            campo_entrada.insert(0, socio_marcado[clave])
            campo_entrada.pack(padx=30)
            diccionario_entradas_edicion[clave] = campo_entrada
            
        ctk.CTkLabel(ventana_edicion, text="Plan").pack(anchor="w", padx=30, pady=(10, 0))
        campo_plan_edicion = ctk.CTkComboBox(ventana_edicion, width=420, values=lista_nombres_combobox, state="readonly")
        
        # Buscamos de forma humana y clara cuál es el texto que corresponde al plan del socio
        texto_plan_actual = ""
        for texto_opcion, plan in zip(lista_nombres_combobox, lista_planes_filtrados):
            if plan["id"] == socio_marcado["plan_id"]:
                texto_plan_actual = texto_opcion
                break
                
        campo_plan_edicion.set(texto_plan_actual)
        campo_plan_edicion.pack(padx=30)

        # Panel interactivo para el visor y la actualización de la fotografía del socio
        ctk.CTkLabel(ventana_edicion, text="Foto").pack(anchor="w", padx=30, pady=(10, 0))
        
        contenedor_foto_edicion = ctk.CTkFrame(ventana_edicion, fg_color="transparent")
        contenedor_foto_edicion.pack(anchor="w", padx=30)
        
        visor_fotografia_edicion = ctk.CTkLabel(
            contenedor_foto_edicion, 
            text="Sin foto", 
            width=100, 
            height=100, 
            corner_radius=8,
            fg_color=("gray80", "gray25")
        )
        visor_fotografia_edicion.pack(side="left")
        
        # Diccionario para almacenar de forma temporal las referencias de la nueva imagen
        estado_fotografia_temporal = {
            "ruta": None, 
            "img": None
        }

        # Función auxiliar interna para refrescar el recuadro visual de la ventana con la nueva imagen
        def actualizar_visor_imagen(ruta_archivo_imagen):
            imagen_miniatura_lista = imagenes.miniatura(ruta_archivo_imagen, 100)
            if imagen_miniatura_lista:
                estado_fotografia_temporal["img"] = imagen_miniatura_lista
                visor_fotografia_edicion.configure(image=imagen_miniatura_lista, text="")

        # Si el socio ya cuenta con una imagen real en el disco duro, la cargamos por defecto en el visor
        ruta_foto_actual_disco = fotos.ruta_foto(socio_marcado["foto"])
        if ruta_foto_actual_disco:
            actualizar_visor_imagen(ruta_foto_actual_disco)

        # Función auxiliar interna que gestiona la apertura del explorador y la validación de la nueva foto
        def ejecutar_seleccion_nueva_foto():
            tipos_archivos_permitidos = [
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), 
                ("Todos los archivos", "*.*")
            ]
            ruta_nueva_seleccionada = filedialog.askopenfilename(
                title="Foto del socio", 
                filetypes=tipos_archivos_permitidos
            )
            
            if not ruta_nueva_seleccionada:
                return
                
            mensaje_error_peso = fotos.validar_imagen(ruta_nueva_seleccionada)
            if mensaje_error_peso:
                etiqueta_alertas_edicion.configure(text=mensaje_error_peso)
                return
                
            estado_fotografia_temporal["ruta"] = ruta_nueva_seleccionada
            actualizar_visor_imagen(ruta_nueva_seleccionada)

        ctk.CTkButton(
            contenedor_foto_edicion, 
            text="Cambiar foto…", 
            width=130, 
            command=ejecutar_seleccion_nueva_foto
        ).pack(side="left", padx=10)

        # Etiqueta para el despliegue de alertas y botón de confirmación de cambios
        etiqueta_alertas_edicion = ctk.CTkLabel(ventana_edicion, text="", text_color=ROJO)
        etiqueta_alertas_edicion.pack(pady=8)

        # Extrae los datos modificados de las casillas, valida su consistencia y actualiza la base de datos.
        def ejecutar_guardado_cambios_socio():
            datos_modificados = {}
            for clave, campo_entrada in diccionario_entradas_edicion.items():
                datos_modificados[clave] = campo_entrada.get().strip()
                
            if not datos_modificados["nombres"] or not datos_modificados["apellidos"]:
                etiqueta_alertas_edicion.configure(text="Nombres y apellidos son obligatorios.")
                return
                
            if not validar_correo(datos_modificados["correo"]) or not validar_telefono(datos_modificados["telefono"]):
                etiqueta_alertas_edicion.configure(text="Correo o teléfono inválido.")
                return
                
            texto_plan_actual = campo_plan_edicion.get()
            indice_plan_elegido = lista_nombres_combobox.index(texto_plan_actual)
            plan_seleccionado_edicion = lista_planes_filtrados[indice_plan_elegido]
            
            nombre_archivo_foto_nuevo = None
            if estado_fotografia_temporal["ruta"]:
                try:
                    nombre_archivo_foto_nuevo = fotos.guardar_foto(
                        estado_fotografia_temporal["ruta"], 
                        socio_marcado["rut"]
                    )
                except OSError:
                    etiqueta_alertas_edicion.configure(text="No se pudo guardar la foto.")
                    return
                    
            repo.actualizar_socio(
                socio_marcado["id"], 
                datos_modificados["nombres"], 
                datos_modificados["apellidos"], 
                datos_modificados["correo"], 
                datos_modificados["telefono"],
                plan_seleccionado_edicion["id"], 
                nombre_archivo_foto_nuevo
            )
            
            ventana_edicion.destroy()
            self.cargar()

        ctk.CTkButton(
            ventana_edicion, 
            text="Guardar cambios", 
            command=ejecutar_guardado_cambios_socio
        ).pack(pady=5)

"""Interfaz gráfica para la gestión, registro y edición de socios del gimnasio."""
import customtkinter as ctk
from tkinter import filedialog

from db import repositorio as repo
from logica import fotos
from logica.horarios import resumen_horario
from logica.validaciones import formatear_rut, validar_socio, limpiar_rut
from ui import imagenes
from ui.estilos import ROJO, VERDE, moneda

# Modulo visual que construye el formulario estructurado en cuadrícula para la inscripción de socios.
class EnrolamientoFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        self.aplicacion_principal = aplicacion_principal
        self.ruta_foto_origen = None
        self.objeto_imagen_vista = None
        
        ctk.CTkLabel(
            self, 
            text="Enrolar nuevo socio", 
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", pady=(0, 15))

        marco_formulario = ctk.CTkFrame(self)
        marco_formulario.pack(anchor="w", fill="x")
        
        self.lista_planes_disponibles = repo.listar_planes()
        self.diccionario_campos = {}

        # Fila 1: RUT y Nombres
        ctk.CTkLabel(marco_formulario, text="RUT (12.345.678-5)").grid(row=0, column=0, sticky="w", padx=15, pady=(12, 0))
        campo_rut = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_rut.grid(row=1, column=0, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["rut"] = campo_rut

        ctk.CTkLabel(marco_formulario, text="Nombres").grid(row=0, column=1, sticky="w", padx=15, pady=(12, 0))
        campo_nombres = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_nombres.grid(row=1, column=1, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["nombres"] = campo_nombres

        # Fila 2: Apellidos y Fecha de nacimiento
        ctk.CTkLabel(marco_formulario, text="Apellidos").grid(row=2, column=0, sticky="w", padx=15, pady=(12, 0))
        campo_apellidos = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_apellidos.grid(row=3, column=0, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["apellidos"] = campo_apellidos

        ctk.CTkLabel(marco_formulario, text="Fecha de nacimiento (DD/MM/AAAA)").grid(row=2, column=1, sticky="w", padx=15, pady=(12, 0))
        campo_fecha_nacimiento = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_fecha_nacimiento.grid(row=3, column=1, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["fecha_nac"] = campo_fecha_nacimiento

        # Fila 3: Correo electrónico y Teléfono
        ctk.CTkLabel(marco_formulario, text="Correo electrónico").grid(row=4, column=0, sticky="w", padx=15, pady=(12, 0))
        campo_correo = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_correo.grid(row=5, column=0, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["correo"] = campo_correo

        ctk.CTkLabel(marco_formulario, text="Teléfono (+56912345678)").grid(row=4, column=1, sticky="w", padx=15, pady=(12, 0))
        campo_telefono = ctk.CTkEntry(marco_formulario, width=330, height=36)
        campo_telefono.grid(row=5, column=1, padx=15, pady=(2, 0), sticky="w")
        self.diccionario_campos["telefono"] = campo_telefono

        # Vinculación del formateo automático del RUT al salir de la casilla
        self.diccionario_campos["rut"].bind("<FocusOut>", self._formatear_rut)

        # Fila 4: Selección de Plan y Menú desplegable
        ctk.CTkLabel(marco_formulario, text="Plan").grid(row=6, column=0, sticky="w", padx=15, pady=(12, 0))
        
        opciones_planes_formateadas = []
        for plan_iteracion in self.lista_planes_disponibles:
            nombre_plan = plan_iteracion['nombre']
            precio_formateado = moneda(plan_iteracion['precio'])
            horario_resumen = resumen_horario(plan_iteracion)
            
            texto_opcion = f"{nombre_plan} — {precio_formateado} · {horario_resumen}"
            opciones_planes_formateadas.append(texto_opcion)
            
        self.campo_plan = ctk.CTkComboBox(
            marco_formulario, 
            width=460, 
            height=36, 
            state="readonly",
            values=opciones_planes_formateadas
        )
        self.campo_plan.grid(row=7, column=0, padx=15, pady=(2, 18), sticky="w")
        
        primer_plan_disponible = self.campo_plan.cget("values")[0]
        self.campo_plan.set(primer_plan_disponible)

        # Fila 4 (Columna 2): Panel interactivo para la Foto del Socio
        ctk.CTkLabel(marco_formulario, text="Foto del socio (opcional)").grid(row=6, column=1, sticky="w", padx=15, pady=(12, 0))
        
        contenedor_foto = ctk.CTkFrame(marco_formulario, fg_color="transparent")
        contenedor_foto.grid(row=7, column=1, sticky="w", padx=15, pady=(2, 18))
        
        self.visor_fotografia = ctk.CTkLabel(
            contenedor_foto, 
            text="Sin foto", 
            width=90, 
            height=90, 
            corner_radius=8,
            fg_color=("gray80", "gray25")
        )
        self.visor_fotografia.pack(side="left")
        
        ctk.CTkButton(
            contenedor_foto, 
            text="Elegir foto…", 
            width=110, 
            command=self.elegir_foto
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            contenedor_foto, 
            text="Quitar", 
            width=70, 
            fg_color="gray40", 
            hover_color="gray30",
            command=self.quitar_foto
        ).pack(side="left")

        # Bloque inferior: Alertas de errores del formulario y Botón de confirmación de registro
        self.etiqueta_mensajes_formulario = ctk.CTkLabel(self, text="", justify="left", wraplength=700)
        self.etiqueta_mensajes_formulario.pack(anchor="w", pady=10)
        
        ctk.CTkButton(
            self, 
            text="Guardar socio", 
            height=40, 
            width=200, 
            command=self.guardar
        ).pack(anchor="w")

    # ---------- foto ----------

    # Abre el explorador de archivos para seleccionar una foto de perfil, validando su peso e integridad antes de mostrarla.
    def elegir_foto(self):
        tipos_archivos_permitidos = [
            ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), 
            ("Todos los archivos", "*.*")
        ]
        ruta_seleccionada = filedialog.askopenfilename(
            title="Foto del socio", 
            filetypes=tipos_archivos_permitidos
        )
        
        if not ruta_seleccionada:
            return
            
        mensaje_error_peso = fotos.validar_imagen(ruta_seleccionada)
        if mensaje_error_peso:
            self.etiqueta_mensajes_formulario.configure(text=mensaje_error_peso, text_color=ROJO)
            return
            
        imagen_miniatura_lista = imagenes.miniatura(ruta_seleccionada, 90)
        if imagen_miniatura_lista is None:
            self.etiqueta_mensajes_formulario.configure(text="No se pudo abrir la imagen.", text_color=ROJO)
            return
            
        self.ruta_foto_origen = ruta_seleccionada
        self.objeto_imagen_vista = imagen_miniatura_lista
        
        self.visor_fotografia.configure(image=imagen_miniatura_lista, text="")
        self.etiqueta_mensajes_formulario.configure(text="")

    # Remueve la imagen seleccionada del visor y restablece el recuadro a su estado inicial transparente.
    def quitar_foto(self):
        self.ruta_foto_origen = None
        self.objeto_imagen_vista = imagenes.vacia(90)
        
        self.visor_fotografia.configure(image=self.objeto_imagen_vista, text="Sin foto")

    # ---------- formulario ----------

    # Detecta cuando el usuario sale de la casilla y añade automáticamente los puntos y el guion al RUT en pantalla.
    def _formatear_rut(self, evento_foco=None):
        campo_rut_pantalla = self.diccionario_campos["rut"]
        texto_actual_rut = campo_rut_pantalla.get()
            
        if len(limpiar_rut(texto_actual_rut)) > 1:
            rut_perfecto_texto = formatear_rut(texto_actual_rut)
                
            campo_rut_pantalla.delete(0, "end")
            campo_rut_pantalla.insert(0, rut_perfecto_texto)

    # Procesa la inscripción definitiva del socio, valida los campos y almacena su perfil físico y fotográfico de forma segura.
    def guardar(self):
        datos_formulario = {}
        for clave, campo_entrada in self.diccionario_campos.items():
            datos_formulario[clave] = campo_entrada.get().strip()
            
        lista_errores, fecha_parseada = validar_socio(
            datos_formulario["rut"], 
            datos_formulario["nombres"], 
            datos_formulario["apellidos"],
            datos_formulario["fecha_nac"], 
            datos_formulario["correo"], 
            datos_formulario["telefono"]
        )
        
        if lista_errores:
            texto_alerta = "• " + "\n• ".join(lista_errores)
            self.etiqueta_mensajes_formulario.configure(text=texto_alerta, text_color=ROJO)
            return
            
        texto_plan_seleccionado = self.campo_plan.get()
        lista_opciones_combobox = self.campo_plan.cget("values")
        indice_plan_elegido = lista_opciones_combobox.index(texto_plan_seleccionado)
        plan_seleccionado = self.lista_planes_disponibles[indice_plan_elegido]
        
        try:
            rut_formateado_final = formatear_rut(datos_formulario["rut"])
            nombre_usuario_actual = self.aplicacion_principal.usuario
            
            # ... (viene de la parte de arriba)
            id_nuevo_socio = repo.crear_socio(
                rut_formateado_final, 
                datos_formulario["nombres"], 
                datos_formulario["apellidos"], 
                fecha_parseada,
                datos_formulario["correo"], 
                datos_formulario["telefono"], 
                plan_seleccionado["id"],
                nombre_usuario_actual
            )
        except ValueError as error_duplicado:
            self.etiqueta_mensajes_formulario.configure(text=str(error_duplicado), text_color=ROJO)
            return
            
        aviso_fotografia_error = ""
        if self.ruta_foto_origen:
            try:
                nombre_foto_procesada = fotos.guardar_foto(self.ruta_foto_origen, datos_formulario["rut"])
                repo.actualizar_foto(id_nuevo_socio, nombre_foto_procesada)
            except OSError:
                aviso_fotografia_error = " La foto no se pudo guardar; agrégala desde Socios → Editar."
                
        mensaje_exito = f"✔ Socio {datos_formulario['nombres']} {datos_formulario['apellidos']} enrolado con plan {plan_seleccionado['nombre']}.{aviso_fotografia_error}"
        self.etiqueta_mensajes_formulario.configure(text=mensaje_exito, text_color=VERDE)
        
        for campo_entrada in self.diccionario_campos.values():
            campo_entrada.delete(0, "end")
            
        self.quitar_foto()

import customtkinter as ctk
from db import repositorio as repo
from logica import fotos
from logica.validaciones import formatear_rut, validar_rut
from ui import imagenes
from ui.estilos import ROJO, VERDE

LADO_FOTOGRAFIA_TOTEM = 200

# Clase gráfica que construye el quiosco digital o tótem centrado para la validación automática de accesos.
class TotemFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        self.identificador_tiempo_pendiente = None
        self.objeto_imagen_socio = None
        self.imagen_vacia_soporte = imagenes.vacia(LADO_FOTOGRAFIA_TOTEM)
        
        ctk.CTkLabel(
            self, 
            text="Control de acceso", 
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")
        
        marco_central_totem = ctk.CTkFrame(self, fg_color="transparent")
        marco_central_totem.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(marco_central_totem, text="Ingresa tu RUT", font=("Segoe UI", 28)).pack(pady=6)
        
        self.campo_rut_totem = ctk.CTkEntry(
            marco_central_totem, 
            width=420, 
            height=56, 
            font=("Segoe UI", 26), 
            justify="center",
            placeholder_text="12.345.678-5"
        )
        self.campo_rut_totem.pack(pady=6)
        
        # Enlaza la tecla Enter para procesar la marcación de entrada al instante
        self.campo_rut_totem.bind("<Return>", self.detectar_tecla_enter_marcacion)
        self.campo_rut_totem.focus()
        
        self.visor_fotografia_totem = ctk.CTkLabel(
            marco_central_totem, 
            text="", 
            image=self.imagen_vacia_soporte, 
            width=LADO_FOTOGRAFIA_TOTEM, 
            height=LADO_FOTOGRAFIA_TOTEM,
            corner_radius=12, 
            font=("Segoe UI", 16)
        )
        self.visor_fotografia_totem.pack(pady=(10, 0))
        
        self.tarjeta_veredicto_totem = ctk.CTkLabel(
            marco_central_totem, 
            text="", 
            width=520, 
            height=120, 
            corner_radius=14,
            font=("Segoe UI", 26, "bold"), 
            fg_color="transparent", 
            text_color="white"
        )
        self.tarjeta_veredicto_totem.pack(pady=14)

    # Captura la pulsación de la tecla Enter para gatillar el control de acceso en la puerta.
    def detectar_tecla_enter_marcacion(self, evento_teclado):
        self.validar()

    # Evalúa la marcación del cliente, consulta el repositorio de accesos y despliega el veredicto visual en la pantalla del quiosco.
    def validar(self):
        texto_rut_digitado = self.campo_rut_totem.get()
        
        if not validar_rut(texto_rut_digitado):
            self._mostrar("RUT INVÁLIDO", ROJO)
            return
            
        rut_formateado_final = formatear_rut(texto_rut_digitado)
        acceso_aprobado, mensaje_servidor, datos_socio = repo.registrar_acceso(rut_formateado_final)
        
        if acceso_aprobado:
            texto_encabezado_veredicto = "✔ ACCESO PERMITIDO\n"
            color_tarjeta_pantalla = VERDE
        else:
            texto_encabezado_veredicto = "✖ ACCESO DENEGADO\n"
            color_tarjeta_pantalla = ROJO
            
        mensaje_pantalla_completo = f"{texto_encabezado_veredicto}{mensaje_servidor}"
        self._mostrar(mensaje_pantalla_completo, color_tarjeta_pantalla, datos_socio)

    # Dibuja la respuesta con los colores de alerta, carga la foto de identidad del socio y activa el temporizador.
    def _mostrar(self, texto_mensaje, color_alerta, datos_socio=None):
        self.tarjeta_veredicto_totem.configure(text=texto_mensaje, fg_color=color_alerta)
        self.campo_rut_totem.delete(0, "end")
        
        # La foto se muestra siempre que el RUT exista (permitido o denegado), para identificar a la persona
        if datos_socio is not None:
            ruta_foto_disco = fotos.ruta_foto(datos_socio["foto"])
            
            if ruta_foto_disco:
                imagen_miniatura_lista = imagenes.miniatura(ruta_foto_disco, LADO_FOTOGRAFIA_TOTEM)
            else:
                imagen_miniatura_lista = None
                
            if imagen_miniatura_lista:
                self.objeto_imagen_socio = imagen_miniatura_lista
                self.visor_fotografia_totem.configure(
                    image=imagen_miniatura_lista, 
                    text="", 
                    fg_color="transparent"
                )
            else:
                self.visor_fotografia_totem.configure(
                    image=self.imagen_vacia_soporte, 
                    text="Sin foto", 
                    fg_color=("gray80", "gray25")
                )
        else:
            self.visor_fotografia_totem.configure(
                image=self.imagen_vacia_soporte, 
                text="", 
                fg_color="transparent"
            )
            
        # Evita que un resultado viejo borre el nuevo al acumularse marcaciones rápidas en la puerta
        if self.identificador_tiempo_pendiente:
            self.after_cancel(self.identificador_tiempo_pendiente)
            
        # Deja la pantalla visible por 4 segundos (4000 milisegundos) antes de regresar al estado de espera
        self.identificador_tiempo_pendiente = self.after(4000, self._limpiar)

    # Restablece la marquesina de la tarjeta y el visor fotográfico para esperar la marcación del siguiente cliente.
    def _limpiar(self):
        self.identificador_tiempo_pendiente = None
        self.tarjeta_veredicto_totem.configure(text="", fg_color="transparent")
        self.visor_fotografia_totem.configure(image=self.imagen_vacia_soporte, text="", fg_color="transparent")

    # Detiene de forma segura cualquier temporizador activo en segundo plano antes de destruir el componente de pantalla.
    def destroy(self):
        if self.identificador_tiempo_pendiente:
            self.after_cancel(self.identificador_tiempo_pendiente)
            
        super().destroy()

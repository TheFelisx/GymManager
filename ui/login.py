import customtkinter as ctk
from db import repositorio as repo
from logica.auth import verificar_clave
from ui.estilos import ROJO

# Construye la interfaz gráfica y los controles del formulario de acceso seguro para el personal del gimnasio.
class LoginFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, funcion_al_ingresar):
        super().__init__(componente_padre, fg_color="transparent")
        self.funcion_al_ingresar = funcion_al_ingresar
        
        contenedor_formulario = ctk.CTkFrame(self, corner_radius=16)
        contenedor_formulario.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            contenedor_formulario, 
            text="🏋️ GymManager Pro", 
            font=("Segoe UI", 28, "bold")
        ).pack(padx=60, pady=(40, 4))
        
        ctk.CTkLabel(
            contenedor_formulario, 
            text="Inicia sesión para continuar", 
            text_color="gray"
        ).pack(pady=(0, 20))

        self.campo_usuario = ctk.CTkEntry(
            contenedor_formulario, 
            placeholder_text="Usuario", 
            width=280, 
            height=38
        )
        self.campo_usuario.pack(pady=6)
        
        self.campo_clave = ctk.CTkEntry(
            contenedor_formulario, 
            placeholder_text="Contraseña", 
            show="•", 
            width=280, 
            height=38
        )
        self.campo_clave.pack(pady=6)
        
        # Enlaza la tecla Enter para procesar el inicio de sesión de forma rápida
        self.campo_clave.bind("<Return>", self.detectar_tecla_enter)

        self.mensaje_error = ctk.CTkLabel(
            contenedor_formulario, 
            text="", 
            text_color=ROJO
        )
        self.mensaje_error.pack(pady=(6, 0))
        
        ctk.CTkButton(
            contenedor_formulario, 
            text="Ingresar", 
            width=280, 
            height=40, 
            command=self.ingresar
        ).pack(pady=(10, 40), padx=60)
        
        self.campo_usuario.focus()

    # Captura la pulsación de la tecla Enter en la casilla de contraseña para activar el botón de ingreso.
    def detectar_tecla_enter(self, evento):
        self.ingresar()

    # Valida las credenciales escritas contra la base de datos y autoriza el acceso a la aplicación según el rol.
    def ingresar(self):
        nombre_usuario = self.campo_usuario.get().strip()
        contrasena_ingresada = self.campo_clave.get()
        
        if nombre_usuario:
            fila_usuario = repo.obtener_usuario(nombre_usuario)
        else:
            fila_usuario = None
            
        # El acceso se rechaza por cualquiera de estos tres motivos, y siempre con el MISMO mensaje,
        # para que nadie pueda averiguar qué usuarios existen o cuáles están desactivados.
        if fila_usuario is None:
            acceso_permitido = False          # el usuario no existe
        elif not fila_usuario["activo"]:
            acceso_permitido = False          # el usuario existe pero está desactivado
        else:
            acceso_permitido = verificar_clave(contrasena_ingresada, fila_usuario["clave_hash"])

        if not acceso_permitido:
            self.mensaje_error.configure(text="Usuario o contraseña incorrectos.")
            self.campo_clave.delete(0, "end")
            return
            
        self.funcion_al_ingresar(fila_usuario["usuario"], fila_usuario["rol"])


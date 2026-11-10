import customtkinter as ctk

from logica.auth import modulos_permitidos
from ui.enrolamiento import EnrolamientoFrame
from ui import estilos
from ui.estilos import ROJO
from ui.finanzas import FinanzasFrame
from ui.login import LoginFrame
from ui.pagos import PagosFrame
from ui.planes import PlanesFrame
from ui.socios import SociosFrame
from ui.totem import TotemFrame
from ui.usuarios import UsuariosFrame

# Diccionario maestro que mapea las claves del sistema con los textos del menú lateral y sus respectivas clases visuales.
MODULOS = {  # clave: (texto del menú, clase de la pantalla)
    "socios": ("👥  Socios", SociosFrame),
    "enrolar": ("➕  Enrolar socio", EnrolamientoFrame),
    "pagos": ("💳  Pagos", PagosFrame),
    "planes": ("📋  Planes", PlanesFrame),
    "usuarios": ("👤  Usuarios", UsuariosFrame),
    "totem": ("🚪  Control de acceso", TotemFrame),
    "finanzas": ("📊  Finanzas", FinanzasFrame),
}

# Ventana maestra de la aplicación que inicializa el entorno visual, las dimensiones y el arranque del inicio de sesión.
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_default_color_theme("blue")
        estilos.aplicar_tema(estilos.cargar_tema())
        
        self.title("GymManager Pro")
        self.geometry("1150x680")
        self.minsize(980, 600)
        
        self.mostrar_login()

    # Remueve de forma absoluta todos los componentes gráficos activos en la ventana para permitir un refresco de pantalla limpio.
    def _limpiar(self):
        for componente_hijo in self.winfo_children():
            componente_hijo.destroy()

    # Blanquea la interfaz gráfica y despliega el formulario modal de login para la autenticación del personal del gimnasio.
    def mostrar_login(self):
        self._limpiar()
        LoginFrame(self, self.iniciar_sesion).pack(fill="both", expand=True)

    # Construye la interfaz principal con el menú de navegación dinámico según los permisos del rol e inicializa el entorno de trabajo.
    def iniciar_sesion(self, nombre_usuario, rol_usuario):
        self._limpiar()
        
        self.usuario = nombre_usuario
        self.rol = rol_usuario
        
        marco_menu_lateral = ctk.CTkFrame(self, width=230, corner_radius=0)
        marco_menu_lateral.pack(side="left", fill="y")
        marco_menu_lateral.pack_propagate(False)
        
        ctk.CTkLabel(
            marco_menu_lateral, 
            text="🏋️ GymManager", 
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(25, 4))
        
        ctk.CTkLabel(
            marco_menu_lateral, 
            text=f"{nombre_usuario} · {rol_usuario}", 
            text_color="gray"
        ).pack(pady=(0, 20))

        self.marco_contenido_pantalla = ctk.CTkFrame(self, fg_color="transparent")
        self.marco_contenido_pantalla.pack(side="left", fill="both", expand=True, padx=25, pady=20)

        lista_modulos_permitidos = modulos_permitidos(rol_usuario)
        
        # Generamos dinámicamente los botones de las pantallas autorizadas para el rol actual
        for clave_modulo in lista_modulos_permitidos:
            texto_boton, clase_pantalla = MODULOS[clave_modulo]
            
            # Función de soporte para enlazar la clave del módulo con el navegador de pestañas lateral de forma prolija
            def generar_evento_navegacion(clave_destino=clave_modulo):
                self.ir_a(clave_destino)
                
            ctk.CTkButton(
                marco_menu_lateral, 
                text=texto_boton, 
                anchor="w", 
                height=40, 
                fg_color="transparent",
                hover_color=("gray80", "gray25"), 
                text_color=("gray10", "gray90"), 
                command=generar_evento_navegacion
            ).pack(fill="x", padx=12, pady=3)
            
        ctk.CTkButton(
            marco_menu_lateral, 
            text="⏻  Cerrar sesión", 
            fg_color=ROJO, 
            hover_color="#a33", 
            height=38,
            command=self.mostrar_login
        ).pack(side="bottom", fill="x", padx=12, pady=20)
        
        es_modo_oscuro_activo = estilos.MODO == "dark"
        
        if es_modo_oscuro_activo:
            texto_switch_tema = "Modo noche"
        else:
            texto_switch_tema = "Modo día"
            
        self.switch_tema_visual = ctk.CTkSwitch(
            marco_menu_lateral, 
            text=texto_switch_tema, 
            command=self.cambiar_tema
        )
        
        if es_modo_oscuro_activo:
            self.switch_tema_visual.select()
            
        self.switch_tema_visual.pack(side="bottom", padx=20, pady=(0, 4), anchor="w")
        
        # Redirigimos de forma automática a la primera pantalla permitida del listado al entrar
        primer_modulo_autorizado = lista_modulos_permitidos[0]
        self.ir_a(primer_modulo_autorizado)

    # Valida los privilegios del rol, blanquea el espacio de trabajo y monta la pantalla seleccionada a pantalla completa.
    def ir_a(self, clave_modulo_destino):
        # Defensa en la capa lógica de seguridad: bloquea el acceso directo si el rol no tiene permisos
        if clave_modulo_destino not in modulos_permitidos(self.rol):
            return
            
        self.modulo_actual = clave_modulo_destino
        
        # Barremos y removemos los componentes de la pantalla anterior de forma física antes de montar la nueva
        for componente_hijo in self.marco_contenido_pantalla.winfo_children():
            componente_hijo.destroy()
            
        texto_menu, clase_pantalla_grafica = MODULOS[clave_modulo_destino]
        
        # Instanciamos la nueva pantalla pasándole el marco contenedor y la referencia de la aplicación maestra
        pantalla_activa = clase_pantalla_grafica(self.marco_contenido_pantalla, self)
        pantalla_activa.pack(fill="both", expand=True)

    # Altera el tema de color del entorno gráfico y repinta de forma instantánea las tablas abiertas sin recargar la ventana.
    def cambiar_tema(self):
        if self.switch_tema_visual.get():
            modo_visual_nuevo = "dark"
        else:
            modo_visual_nuevo = "light"
            
        estilos.aplicar_tema(modo_visual_nuevo)
        
        if modo_visual_nuevo == "dark":
            texto_switch_nuevo = "Modo noche"
        else:
            texto_switch_nuevo = "Modo día"
            
        self.switch_tema_visual.configure(text=texto_switch_nuevo)
        
        # Los controles de CustomTkinter cambian de color solos; solo hay que repintar de forma recursiva las tablas.
        estilos.recolorear_tablas(self.marco_contenido_pantalla)

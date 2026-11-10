import customtkinter as ctk
from tkinter import messagebox

from db import repositorio as repo
from logica.auth import ROLES, hash_clave, validar_usuario
from ui.estilos import ROJO, VERDE, tabla


# Pantalla exclusiva del administrador: crea usuarios (administradores, recepcionistas y guardias)
# y activa o desactiva su acceso al programa.
class UsuariosFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion):
        super().__init__(componente_padre, fg_color="transparent")
        self.aplicacion = aplicacion  # la ventana principal; sirve para saber quién tiene la sesión iniciada

        titulo = ctk.CTkLabel(self, text="Usuarios del sistema", font=("Segoe UI", 24, "bold"))
        titulo.pack(anchor="w", pady=(0, 10))

        # ---------- Formulario "Nuevo usuario" ----------
        formulario = ctk.CTkFrame(self)
        formulario.pack(fill="x")

        # Los tres campos de texto van uno al lado del otro (columnas 0, 1 y 2).
        self.campo_usuario_nuevo = self._crear_campo_de_texto(formulario, "Usuario", 0, es_contrasena=False)
        self.campo_clave_nueva = self._crear_campo_de_texto(formulario, "Contraseña (mínimo 8)", 1, es_contrasena=True)
        self.campo_clave_repetida = self._crear_campo_de_texto(formulario, "Repetir contraseña", 2, es_contrasena=True)

        # El rol no se escribe: se elige de una lista desplegable (columna 3).
        etiqueta_rol = ctk.CTkLabel(formulario, text="Rol")
        etiqueta_rol.grid(row=0, column=3, sticky="w", padx=15, pady=(12, 0))

        self.campo_rol_nuevo = ctk.CTkComboBox(formulario, values=ROLES, state="readonly", width=170, height=34)
        self.campo_rol_nuevo.set("recepcionista")  # el rol más común queda marcado de antemano
        self.campo_rol_nuevo.grid(row=1, column=3, sticky="w", padx=15)

        # Fila de abajo: el botón para crear y, a su lado, el mensaje de error o de éxito.
        fila_boton = ctk.CTkFrame(formulario, fg_color="transparent")
        fila_boton.grid(row=2, column=0, columnspan=4, sticky="w", padx=15, pady=12)

        boton_crear = ctk.CTkButton(fila_boton, text="Crear usuario", width=150, command=self.crear)
        boton_crear.pack(side="left")

        self.etiqueta_mensajes_usuarios = ctk.CTkLabel(fila_boton, text="", justify="left", wraplength=700)
        self.etiqueta_mensajes_usuarios.pack(side="left", padx=15)

        # ---------- Lista de usuarios existentes ----------
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", pady=(14, 6))

        subtitulo = ctk.CTkLabel(barra, text="Usuarios existentes", font=("Segoe UI", 16, "bold"))
        subtitulo.pack(side="left")

        boton_alternar = ctk.CTkButton(barra, text="Activar / Desactivar", width=160, command=self.alternar)
        boton_alternar.pack(side="right")

        marco_tabla, self.tabla_usuarios = tabla(self, ("Usuario", "Rol", "Estado"), (240, 180, 120))
        marco_tabla.pack(fill="both", expand=True)

        self.cargar()

    # Crea una etiqueta con su campo de texto debajo, en la columna indicada del formulario.
    def _crear_campo_de_texto(self, formulario, titulo, columna, es_contrasena):
        etiqueta = ctk.CTkLabel(formulario, text=titulo)
        etiqueta.grid(row=0, column=columna, sticky="w", padx=15, pady=(12, 0))

        # En los campos de contraseña cada letra se reemplaza por un punto, para que no se vea lo escrito.
        if es_contrasena:
            caracter_oculto = "•"
        else:
            caracter_oculto = ""

        campo = ctk.CTkEntry(formulario, width=220, height=34, show=caracter_oculto)
        campo.grid(row=1, column=columna, sticky="w", padx=15)
        return campo

    # Vuelve a llenar la tabla con los usuarios que hay en la base de datos.
    def cargar(self):
        # Primero se borran las filas que hubiera, para no mostrar datos repetidos.
        filas_actuales = self.tabla_usuarios.get_children()
        self.tabla_usuarios.delete(*filas_actuales)

        for usuario in repo.listar_usuarios():
            if usuario["activo"]:
                texto_estado = "Activo"
                etiqueta_de_color = "Activo"
            else:
                texto_estado = "Inactivo"
                etiqueta_de_color = "Baja"  # reutiliza el color gris que ya tienen las tablas

            self.tabla_usuarios.insert(
                "",
                "end",
                iid=usuario["id"],
                tags=(etiqueta_de_color,),
                values=(usuario["usuario"], usuario["rol"], texto_estado),
            )

    # Valida el formulario, cifra la contraseña y guarda el usuario nuevo.
    def crear(self):
        # 1) Leemos lo que escribió el administrador.
        #    A las contraseñas NO se les quitan los espacios, porque una contraseña puede llevarlos.
        nombre = self.campo_usuario_nuevo.get().strip()
        clave = self.campo_clave_nueva.get()
        clave_repetida = self.campo_clave_repetida.get()
        rol = self.campo_rol_nuevo.get()

        # 2) Pedimos a la capa lógica que revise los datos. Si hay errores, los mostramos y paramos aquí.
        errores = validar_usuario(nombre, clave, clave_repetida, rol)
        if len(errores) > 0:
            texto_errores = "• " + "\n• ".join(errores)
            self.etiqueta_mensajes_usuarios.configure(text=texto_errores, text_color=ROJO)
            return

        # 3) Ciframos la contraseña ANTES de guardarla: la base de datos nunca recibe la clave real.
        clave_cifrada = hash_clave(clave)
        try:
            repo.crear_usuario(nombre, clave_cifrada, rol)
        except ValueError as error_nombre_repetido:
            self.etiqueta_mensajes_usuarios.configure(text=str(error_nombre_repetido), text_color=ROJO)
            return

        # 4) Todo salió bien: avisamos, dejamos limpio el formulario y actualizamos la tabla.
        mensaje_exito = f"✔ Usuario «{nombre}» creado con el rol {rol}."
        self.etiqueta_mensajes_usuarios.configure(text=mensaje_exito, text_color=VERDE)

        self.campo_usuario_nuevo.delete(0, "end")
        self.campo_clave_nueva.delete(0, "end")
        self.campo_clave_repetida.delete(0, "end")
        self.cargar()

    # Activa o desactiva al usuario seleccionado en la tabla.
    # Al desactivar hay dos protecciones, para que nadie se quede sin acceso al sistema.
    def alternar(self):
        # 1) ¿Hay una fila elegida?
        filas_seleccionadas = self.tabla_usuarios.selection()
        if not filas_seleccionadas:
            messagebox.showinfo("Usuarios", "Selecciona un usuario de la tabla.")
            return

        # La tabla entrega una LISTA con las filas elegidas; tomamos la primera y la convertimos en número.
        primera_fila = filas_seleccionadas[0]
        id_usuario = int(primera_fila)

        # 2) Buscamos en la lista de usuarios al que tiene ese número de identificación.
        usuario_elegido = None
        for usuario in repo.listar_usuarios():
            if usuario["id"] == id_usuario:
                usuario_elegido = usuario
                break

        if usuario_elegido is None:  # por si alguien lo eliminó justo antes
            self.cargar()
            return

        # 3) El nuevo estado es el contrario del actual: si estaba activo se desactiva, y al revés.
        if usuario_elegido["activo"]:
            nuevo_estado = False
        else:
            nuevo_estado = True

        # 4) Las protecciones solo se aplican cuando se quiere DESACTIVAR.
        if nuevo_estado is False:
            # Protección 1: nadie puede desactivarse a sí mismo.
            nombre_elegido = usuario_elegido["usuario"].lower()
            nombre_de_la_sesion = str(self.aplicacion.usuario).lower()
            if nombre_elegido == nombre_de_la_sesion:
                messagebox.showinfo("Usuarios", "No puedes desactivar tu propio usuario.")
                return

            # Protección 2: siempre debe quedar al menos un administrador activo.
            es_administrador = usuario_elegido["rol"] == "administrador"
            administradores_activos = repo.contar_administradores_activos()
            if es_administrador and administradores_activos <= 1:
                messagebox.showinfo("Usuarios", "Debe quedar al menos un administrador activo.")
                return

            # Antes de desactivar, pedimos confirmación.
            pregunta = f"«{usuario_elegido['usuario']}» ya no podrá iniciar sesión. ¿Continuar?"
            el_usuario_confirmo = messagebox.askyesno("Desactivar usuario", pregunta)
            if not el_usuario_confirmo:
                return

        # 5) Aplicamos el cambio y actualizamos la tabla.
        repo.cambiar_estado_usuario(id_usuario, nuevo_estado)
        self.cargar()

"""Interfaz gráfica para el registro de recaudaciones y renovación de membresías en la caja."""
import customtkinter as ctk
from db import repositorio as repo
from logica.horarios import resumen_horario
from logica.validaciones import formatear_rut, validar_rut
from ui.estilos import ROJO, VERDE, moneda, tabla

METODOS_PAGO_PERMITIDOS = ["Efectivo", "Débito", "Crédito", "Transferencia"]

# Clase gráfica que construye el panel superior de la caja para buscar socios y registrar transacciones.
class PagosFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        self.aplicacion_principal = aplicacion_principal
        self.socio_encontrado = None
        self.lista_planes_totales = []
        self.lista_nombres_planes_combobox = []
        
        ctk.CTkLabel(
            self, 
            text="Registro de pagos", 
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        fila_busqueda_caja = ctk.CTkFrame(self, fg_color="transparent")
        fila_busqueda_caja.pack(anchor="w")
        
        self.campo_rut_busqueda = ctk.CTkEntry(
            fila_busqueda_caja, 
            placeholder_text="RUT del socio", 
            width=260, 
            height=36
        )
        self.campo_rut_busqueda.pack(side="left")
        
        # Enlaza la tecla Enter para gatillar la búsqueda del socio de forma directa
        self.campo_rut_busqueda.bind("<Return>", self.detectar_tecla_enter_busqueda)
        
        ctk.CTkButton(
            fila_busqueda_caja, 
            text="Registrar pago…", 
            width=140, 
            command=self.buscar
        ).pack(side="left", padx=10)

        # Formulario de entrada dinámica (se visualiza al validar la ficha del socio)
        self.marco_formulario_pago = ctk.CTkFrame(self)
        
        self.etiqueta_informacion_socio = ctk.CTkLabel(
            self.marco_formulario_pago, 
            text="", 
            justify="left", 
            font=("Segoe UI", 14)
        )
        self.etiqueta_informacion_socio.pack(anchor="w", padx=15, pady=(12, 6))
        
        contenedor_campos_pago = ctk.CTkFrame(self.marco_formulario_pago, fg_color="transparent")
        contenedor_campos_pago.pack(anchor="w", padx=10, pady=(0, 12))
        
        self.campo_plan_pago = ctk.CTkComboBox(
            contenedor_campos_pago, 
            width=400, 
            height=34, 
            state="readonly", 
            command=self._plan_cambiado
        )
        self.campo_plan_pago.pack(side="left", padx=5)
        
        self.campo_monto_pago = ctk.CTkEntry(
            contenedor_campos_pago, 
            width=120, 
            height=34, 
            placeholder_text="Monto"
        )
        self.campo_monto_pago.pack(side="left", padx=5)
        
        self.campo_metodo_pago = ctk.CTkComboBox(
            contenedor_campos_pago, 
            values=METODOS_PAGO_PERMITIDOS, 
            state="readonly", 
            width=150, 
            height=34
        )
        self.campo_metodo_pago.set(METODOS_PAGO_PERMITIDOS[0])
        self.campo_metodo_pago.pack(side="left", padx=5)
        
        ctk.CTkButton(
            contenedor_campos_pago, 
            text="Guardar registro", 
            height=34, 
            command=self.pagar
        ).pack(side="left", padx=5)

        # Registro inferior: Alertas globales de la caja y listado histórico de transacciones
        self.etiqueta_mensajes_caja = ctk.CTkLabel(self, text="")
        self.etiqueta_mensajes_caja.pack(anchor="w", pady=4)

        barra_herramientas_historial = ctk.CTkFrame(self, fg_color="transparent")
        barra_herramientas_historial.pack(fill="x", pady=(8, 6))
        
        ctk.CTkLabel(
            barra_herramientas_historial, 
            text="Pagos registrados", 
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")
        
        self.campo_filtro_historial = ctk.CTkEntry(
            barra_herramientas_historial, 
            placeholder_text="Filtrar por RUT o nombre…", 
            width=280, 
            height=32
        )
        self.campo_filtro_historial.pack(side="right")
        
        # Enlaza la soltura de teclas para activar la búsqueda instantánea en la planilla de caja
        self.campo_filtro_historial.bind("<KeyRelease>", self.detectar_escritura_filtro_historial)

        columnas_tabla_pagos = ("Fecha", "Socio", "RUT", "Plan", "Método", "Monto", "Registrado por")
        anchos_columnas_pagos = (95, 220, 115, 150, 110, 100, 130)
        
        marco_tabla_pagos, self.tabla_historial_pagos = tabla(self, columnas_tabla_pagos, anchos_columnas_pagos)
        marco_tabla_pagos.pack(fill="both", expand=True)
        
        self.cargar()

    # Captura la pulsación de la tecla Enter en la casilla del RUT para procesar la búsqueda en caja.
    def detectar_tecla_enter_busqueda(self, evento_teclado):
        self.buscar()

    # Captura la soltura de teclas en el cuadro de filtro para actualizar la planilla de ingresos al instante.
    def detectar_escritura_filtro_historial(self, evento_teclado):
        self.cargar()

    # ---------- tabla ----------

    # Vacía el historial de la caja y lo vuelve a llenar en tiempo real con los pagos que coincidan con el filtro.
    def cargar(self):
        for registro_visual in self.tabla_historial_pagos.get_children():
            self.tabla_historial_pagos.delete(registro_visual)
            
        texto_filtro = self.campo_filtro_historial.get()
        lista_pagos_encontrados = repo.listar_pagos(texto_filtro)
        
        for pago in lista_pagos_encontrados:
            nombre_cajero = pago["registrado_por"] or "—"
            monto_formateado = moneda(pago["monto"])
            
            valores_fila = (
                pago["fecha"], 
                pago["socio"], 
                pago["rut"], 
                pago["plan"], 
                pago["metodo"], 
                monto_formateado, 
                nombre_cajero
            )
            self.tabla_historial_pagos.insert("", "end", values=valores_fila)

    # ---------- formulario ----------

    # Remueve el formulario de cobro de la interfaz gráfica y limpia el registro del socio de la memoria temporal.
    def _ocultar_form(self):
        self.marco_formulario_pago.pack_forget()
        self.socio_encontrado = None

    # Valida el RUT ingresado, busca al socio y precarga sus datos junto a su membresía en el formulario de caja.
    def buscar(self):
        self.etiqueta_mensajes_caja.configure(text="")
        texto_rut_ingresado = self.campo_rut_busqueda.get()
        
        if not validar_rut(texto_rut_ingresado):
            self._ocultar_form()
            self.etiqueta_mensajes_caja.configure(text="RUT inválido.", text_color=ROJO)
            return
            
        rut_formateado_buscar = formatear_rut(texto_rut_ingresado)
        socio_leido = repo.obtener_socio_por_rut(rut_formateado_buscar)
        
        if not socio_leido:
            self._ocultar_form()
            self.etiqueta_mensajes_caja.configure(text="Socio no encontrado.", text_color=ROJO)
            return
            
        if not socio_leido["activo"]:
            self._ocultar_form()
            self.etiqueta_mensajes_caja.configure(
                text="El socio está dado de baja; no se pueden registrar pagos.", 
                text_color=ROJO
            )
            return
            
        self.socio_encontrado = socio_leido
        
        # Obtenemos los planes vigentes más el plan que el socio tiene amarrado actualmente
        todos_los_planes = repo.listar_planes(solo_activos=False)
        self.lista_planes_totales = []
        self.lista_nombres_planes_combobox = []
        
        for plan in todos_los_planes:
            if plan["activo"] or plan["id"] == socio_leido["plan_id"]:
                self.lista_planes_totales.append(plan)
                
                texto_descriptivo = f"{plan['nombre']} — {moneda(plan['precio'])} · {resumen_horario(plan)}"
                self.lista_nombres_planes_combobox.append(texto_descriptivo)
                
        self.campo_plan_pago.configure(values=self.lista_nombres_planes_combobox)
        
        # Buscamos de forma clara el índice del plan actual que tiene el socio
        indice_plan_actual = 0
        for posicion, plan in enumerate(self.lista_planes_totales):
            if plan["id"] == socio_leido["plan_id"]:
                indice_plan_actual = posicion
                break
                
        texto_plan_por_defecto = self.lista_nombres_planes_combobox[indice_plan_actual]
        self.campo_plan_pago.set(texto_plan_por_defecto)
        
        precio_plan_por_defecto = self.lista_planes_totales[indice_plan_actual]["precio"]
        self._poner_monto(precio_plan_por_defecto)
        
        situacion_membresia = repo.estado_socio(socio_leido)
        resumen_cliente_texto = (
            f"{socio_leido['nombres']} {socio_leido['apellidos']}  ·  {socio_leido['rut']}\n"
            f"Vence: {socio_leido['fecha_venc']}  ·  Estado: {situacion_membresia}"
        )
        self.etiqueta_informacion_socio.configure(text=resumen_cliente_texto)
        
        # Empaqueta el componente de forma limpia para que se inyecte en su posición secuencial correcta
        # "before" hace que el formulario aparezca justo antes de la etiqueta de mensajes,
        # es decir, debajo del buscador. Sin esto quedaría al final, debajo de la tabla del historial.
        self.marco_formulario_pago.pack(
            anchor="w",
            fill="x",
            pady=(10, 0),
            before=self.etiqueta_mensajes_caja,
        )

    # Borra la casilla de dinero e inyecta de forma limpia el precio correspondiente en formato de texto.
    def _poner_monto(self, valor_numerico):
        self.campo_monto_pago.delete(0, "end")
        self.campo_monto_pago.insert(0, str(valor_numerico))

    # Detecta el cambio de opción en el menú desplegable y actualiza automáticamente el valor de la membresía en la pantalla.
    def _plan_cambiado(self, texto_plan_seleccionado):
        indice_plan_elegido = self.lista_nombres_planes_combobox.index(texto_plan_seleccionado)
        precio_nuevo_plan = self.lista_planes_totales[indice_plan_elegido]["precio"]
        
        self._poner_monto(precio_nuevo_plan)

    # Valida el monto ingresado, inyecta la renovación en la base de datos y refresca las planillas financieras del mostrador.
    def pagar(self):
        monto_texto_ingresado = self.campo_monto_pago.get().strip()
        
        if not monto_texto_ingresado.isdigit() or int(monto_texto_ingresado) <= 0:
            self.etiqueta_mensajes_caja.configure(
                text="El monto debe ser un entero mayor que 0.", 
                text_color=ROJO
            )
            return
            
        texto_plan_actual = self.campo_plan_pago.get()
        indice_plan_elegido = self.lista_nombres_planes_combobox.index(texto_plan_actual)
        plan_seleccionado_pago = self.lista_planes_totales[indice_plan_elegido]
        
        try:
            id_socio_actual = self.socio_encontrado["id"]
            id_plan_actual = plan_seleccionado_pago["id"]
            monto_pago_final = int(monto_texto_ingresado)
            medio_pago_elegido = self.campo_metodo_pago.get()
            nombre_usuario_cajero = self.aplicacion_principal.usuario
            
            nueva_fecha_vencimiento = repo.registrar_pago(
                id_socio_actual, 
                id_plan_actual, 
                monto_pago_final, 
                medio_pago_elegido, 
                nombre_usuario_cajero
            )
        except ValueError as error_caja:
            self.etiqueta_mensajes_caja.configure(text=str(error_caja), text_color=ROJO)
            return
            
        self.cargar()
        self.buscar()  # Refresca los datos del socio en la cabecera del formulario
        
        mensaje_exito_pago = f"✔ Pago registrado. Nuevo vencimiento: {nueva_fecha_vencimiento}"
        self.etiqueta_mensajes_caja.configure(text=mensaje_exito_pago, text_color=VERDE)

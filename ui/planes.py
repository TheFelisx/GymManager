from datetime import date
import customtkinter as ctk
from tkinter import messagebox

from db import repositorio as repo
from logica.horarios import DIAS, resumen_horario, validar_plan
from ui.estilos import ROJO, VERDE, moneda, tabla

# Clase gráfica que construye el panel de planes mediante pestañas para auditar el rendimiento y crear membresías.
class PlanesFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        self.mes_actual_reporte = date.today().strftime("%Y-%m")
        
        ctk.CTkLabel(
            self, 
            text="Planes del gimnasio", 
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.navegador_pestañas = ctk.CTkTabview(self)
        self.navegador_pestañas.pack(fill="both", expand=True)
        
        # Agregamos y construimos las dos pestañas de administración del módulo
        self._armar_resumen(self.navegador_pestañas.add("Planes"))
        self._armar_formulario(self.navegador_pestañas.add("Nuevo plan"))
        
        self.cargar()

    # ---------- pestaña "Planes": resumen + socios del plan elegido ----------

    # Diseña la estructura gráfica de la pestaña de reportes, configurando las planillas de auditoría financiera y de socios.
    def _armar_resumen(self, pestaña_planes):
        barra_herramientas_reportes = ctk.CTkFrame(pestaña_planes, fg_color="transparent")
        barra_herramientas_reportes.pack(fill="x", pady=(0, 6))
        
        texto_titulo_mes = f"Socios e ingresos por plan  ·  mes {self.mes_actual_reporte}"
        ctk.CTkLabel(
            barra_herramientas_reportes, 
            text=texto_titulo_mes,
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            barra_herramientas_reportes, 
            text="Activar / Desactivar", 
            width=160, 
            command=self.alternar
        ).pack(side="right")

        columnas_tabla_resumen = (
            "Plan", "Precio", "Duración", "Horario", "Estado", 
            "Socios (vigentes/total)", "Generó este mes", "Total generado"
        )
        anchos_columnas_resumen = (130, 80, 80, 190, 70, 150, 115, 115)
        
        marco_tabla_resumen, self.tabla_resumen_planes = tabla(
            pestaña_planes, 
            columnas_tabla_resumen, 
            anchos_columnas_resumen
        )
        self.tabla_resumen_planes.configure(height=6)
        marco_tabla_resumen.pack(fill="x")
        
        # Enlaza la selección de un plan para desplegar automáticamente el listado de socios en la grilla inferior
        self.tabla_resumen_planes.bind("<<TreeviewSelect>>", self.detectar_seleccion_plan)

        self.etiqueta_detalle_socios = ctk.CTkLabel(
            pestaña_planes, 
            text="Selecciona un plan para ver quiénes están en él.",
            font=("Segoe UI", 13, "bold"), 
            anchor="w", 
            justify="left", 
            wraplength=850
        )
        self.etiqueta_detalle_socios.pack(anchor="w", pady=(12, 4))
        
        columnas_tabla_socios_plan = ("Socio", "RUT", "Vence", "Estado")
        anchos_columnas_socios_plan = (300, 140, 120, 100)
        
        marco_tabla_socios_plan, self.tabla_socios_por_plan = tabla(
            pestaña_planes, 
            columnas_tabla_socios_plan, 
            anchos_columnas_socios_plan
        )
        marco_tabla_socios_plan.pack(fill="both", expand=True)

    # Captura el evento de clic o selección en la grilla de planes para refrescar el bloque inferior.
    def detectar_seleccion_plan(self, evento_seleccion):
        self.mostrar_detalle()

    # ---------- pestaña "Nuevo plan" ----------

    # Construye la estructura visual del formulario para dar de alta nuevos planes con sus restricciones horarias.
    def _armar_formulario(self, pestaña_nuevo_plan):
        marco_formulario_plan = ctk.CTkFrame(pestaña_nuevo_plan)
        marco_formulario_plan.pack(fill="x")
        
        self.campo_nombre_plan = self._crear_campo_entrada(marco_formulario_plan, "Nombre del plan", 0, 0, 240)
        self.campo_precio_plan = self._crear_campo_entrada(marco_formulario_plan, "Precio ($)", 0, 1, 130)
        self.campo_duracion_plan = self._crear_campo_entrada(marco_formulario_plan, "Duración (días)", 0, 2, 130)
        self.campo_hora_inicio = self._crear_campo_entrada(marco_formulario_plan, "Hora inicio", 2, 0, 110, "06:00")
        self.campo_hora_fin = self._crear_campo_entrada(marco_formulario_plan, "Hora término", 2, 1, 110, "23:00")

        ctk.CTkLabel(marco_formulario_plan, text="Días permitidos").grid(row=2, column=2, sticky="w", padx=15, pady=(10, 0))
        
        contenedor_dias_check = ctk.CTkFrame(marco_formulario_plan, fg_color="transparent")
        contenedor_dias_check.grid(row=3, column=2, columnspan=4, sticky="w", padx=10)
        
        self.lista_variables_dias = []
        for nombre_dia in DIAS:
            variable_booleana = ctk.BooleanVar(value=True)
            
            checkbox_dia = ctk.CTkCheckBox(
                contenedor_dias_check, 
                text=nombre_dia, 
                variable=variable_booleana, 
                onvalue=True, 
                offvalue=False, 
                width=62
            )
            checkbox_dia.pack(side="left", padx=3)
            self.lista_variables_dias.append(variable_booleana)

        fila_controles_inferior = ctk.CTkFrame(marco_formulario_plan, fg_color="transparent")
        fila_controles_inferior.grid(row=4, column=0, columnspan=6, sticky="w", padx=15, pady=12)
        
        ctk.CTkButton(
            fila_controles_inferior, 
            text="Crear plan", 
            width=140, 
            command=self.crear
        ).pack(side="left")
        
        self.etiqueta_mensajes_planes = ctk.CTkLabel(fila_controles_inferior, text="", wraplength=650, justify="left")
        self.etiqueta_mensajes_planes.pack(side="left", padx=15)

    # Método estático auxiliar que automatiza la creación simétrica de etiquetas y casillas de entrada en la cuadrícula.
    @staticmethod
    def _crear_campo_entrada(componente_padre, texto_etiqueta, numero_fila, numero_columna, ancho_casilla, valor_inicial=""):
        ctk.CTkLabel(componente_padre, text=texto_etiqueta).grid(row=numero_fila, column=numero_columna, sticky="w", padx=15, pady=(10, 0))
        
        campo_entrada = ctk.CTkEntry(componente_padre, width=ancho_casilla, height=34)
        campo_entrada.grid(row=numero_fila + 1, column=numero_columna, sticky="w", padx=15)
        
        if valor_inicial:
            campo_entrada.insert(0, valor_inicial)
            
        return campo_entrada

    # ---------- datos ----------

    # Remueve el resumen financiero de planes, lo vuelve a rellenar desde la base de datos y restaura la selección previa.
    def cargar(self):
        registro_seleccionado_previo = self.tabla_resumen_planes.selection()
        
        for registro_visual in self.tabla_resumen_planes.get_children():
            self.tabla_resumen_planes.delete(registro_visual)
            
        lista_resumen_planes = repo.resumen_planes(self.mes_actual_reporte)
        for plan in lista_resumen_planes:
            
            if plan["activo"]:
                tag_estado_estetico = "Activo"
                texto_estado_tabla = "Activo"
            else:
                tag_estado_estetico = "Baja"
                texto_estado_tabla = "Inactivo"
                
            socios_vigentes_total_texto = f"{plan['socios_vigentes']} / {plan['socios_total']}"
            monto_mes_formateado = moneda(plan["ingresos_mes"])
            monto_total_formateado = moneda(plan["ingresos_total"])
            
            valores_fila = (
                plan["nombre"], 
                moneda(plan["precio"]), 
                f"{plan['duracion_dias']} días", 
                resumen_horario(plan),
                texto_estado_tabla,
                socios_vigentes_total_texto,
                monto_mes_formateado, 
                monto_total_formateado
            )
            
            self.tabla_resumen_planes.insert(
                "", 
                "end", 
                iid=plan["id"], 
                tags=(tag_estado_estetico,), 
                values=valores_fila
            )
            
        if registro_seleccionado_previo and self.tabla_resumen_planes.exists(registro_seleccionado_previo[0]):
            self.tabla_resumen_planes.selection_set(registro_seleccionado_previo[0])
        else:
            self.mostrar_detalle()

    # Carga la lista detallada de socios vinculados al plan marcado y genera el informe financiero neto de la membresía.
    def mostrar_detalle(self):
        for socio_visual in self.tabla_socios_por_plan.get_children():
            self.tabla_socios_por_plan.delete(socio_visual)
            
        filas_seleccionadas = self.tabla_resumen_planes.selection()
        if not filas_seleccionadas:
            self.etiqueta_detalle_socios.configure(text="Selecciona un plan para ver quiénes están en él.")
            return
            
        id_plan_marcado = int(filas_seleccionadas[0])
        
        # Buscamos de forma humana y clara cuál es el plan que corresponde al ID cliqueado
        plan_seleccionado_auditoria = None
        lista_resumen_planes = repo.resumen_planes(self.mes_actual_reporte)
        for plan in lista_resumen_planes:
            if plan["id"] == id_plan_marcado:
                plan_seleccionado_auditoria = plan
                break
                
        lista_socios_del_plan = repo.socios_del_plan(plan_seleccionado_auditoria["id"])
        for socio in lista_socios_del_plan:
            situacion_membresia = repo.estado_socio(socio)
            nombre_completo = f"{socio['nombres']} {socio['apellidos']}"
            
            valores_fila = (
                nombre_completo, 
                socio["rut"], 
                socio["fecha_venc"], 
                situacion_membresia
            )
            self.tabla_socios_por_plan.insert("", "end", tags=(situacion_membresia,), values=valores_fila)
            
        ingresos_mes_texto = moneda(plan_seleccionado_auditoria["ingresos_mes"])
        ingresos_totales_texto = moneda(plan_seleccionado_auditoria["ingresos_total"])
        nombre_plan_actual = plan_seleccionado_auditoria['nombre']
        cantidad_socios_matriculados = len(lista_socios_del_plan)
        
        resumen_gerencial_texto = (
            f"Plan «{nombre_plan_actual}»: {cantidad_socios_matriculados} socio(s) registrados · "
            f"generó {ingresos_mes_texto} este mes · {ingresos_totales_texto} en total"
        )
        
        if not lista_socios_del_plan:
            resumen_gerencial_texto += "\nNingún socio tiene este plan por ahora."
            
        self.etiqueta_detalle_socios.configure(text=resumen_gerencial_texto)

    # ---------- acciones ----------

    # Procesa la creación definitiva de una nueva membresía, valida sus datos y limpia el formulario tras guardar.
    def crear(self):
        # Recolectamos de forma humana los índices de los días que el administrador dejó marcados
        lista_dias_numeros = []
        for posicion, variable_booleana in enumerate(self.lista_variables_dias):
            if variable_booleana.get():
                lista_dias_numeros.append(posicion)
                
        lista_errores, datos_normalizados = validar_plan(
            self.campo_nombre_plan.get(), 
            self.campo_precio_plan.get(), 
            self.campo_duracion_plan.get(),
            self.campo_hora_inicio.get(), 
            self.campo_hora_fin.get(), 
            lista_dias_numeros
        )
        
        if lista_errores:
            texto_alerta = "• " + "\n• ".join(lista_errores)
            self.etiqueta_mensajes_planes.configure(text=texto_alerta, text_color=ROJO)
            return
            
        try:
            repo.crear_plan(
                datos_normalizados["nombre"], 
                datos_normalizados["precio"], 
                datos_normalizados["duracion"], 
                datos_normalizados["hora_inicio"], 
                datos_normalizados["hora_fin"], 
                datos_normalizados["dias"]
            )
        except ValueError as error_nombre_duplicado:
            self.etiqueta_mensajes_planes.configure(text=str(error_nombre_duplicado), text_color=ROJO)
            return
            
        mensaje_exito = f"✔ Plan «{datos_normalizados['nombre']}» creado."
        self.etiqueta_mensajes_planes.configure(text=mensaje_exito, text_color=VERDE)
        
        # Limpiamos las casillas del formulario para dejarlas listas para el siguiente registro
        self.campo_nombre_plan.delete(0, "end")
        self.campo_precio_plan.delete(0, "end")
        self.campo_duracion_plan.delete(0, "end")
        
        self.cargar()

    # Activa o desactiva lógicamente el plan seleccionado de la grilla de reportes comerciales de forma segura.
    def alternar(self):
        filas_seleccionadas = self.tabla_resumen_planes.selection()
        if not filas_seleccionadas:
            messagebox.showinfo("Planes", "Selecciona un plan de la tabla.")
            return

        # La tabla entrega una LISTA con las filas elegidas (aunque sea una sola).
        # Tomamos la primera fila de esa lista y recién entonces la convertimos en número.
        primera_fila = filas_seleccionadas[0]
        id_plan_marcado = int(primera_fila)
        
        # Buscamos de forma humana y clara cuál es el plan que corresponde al ID cliqueado
        plan_seleccionado_estado = None
        lista_planes_totales = repo.listar_planes(solo_activos=False)
        for plan in lista_planes_totales:
            if plan["id"] == id_plan_marcado:
                plan_seleccionado_estado = plan
                break
                
        nuevo_estado_activo = not plan_seleccionado_estado["activo"]
        
        # Si el administrador va a apagar el plan, le advertimos la regla de negocio
        if not nuevo_estado_activo:
            nombre_plan_actual = plan_seleccionado_estado['nombre']
            pregunta_advertencia = (
                f"«{nombre_plan_actual}» dejará de ofrecerse a socios nuevos.\n"
                "Los socios que ya lo tienen lo conservan. ¿Continuar?"
            )
            if not messagebox.askyesno("Desactivar plan", pregunta_advertencia):
                return
                
        repo.cambiar_estado_plan(plan_seleccionado_estado["id"], nuevo_estado_activo)
        self.cargar()

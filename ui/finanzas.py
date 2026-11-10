import customtkinter as ctk
from datetime import date
from db import repositorio as repo
from ui.estilos import AZUL, ROJO, VERDE, moneda, tabla

CATEGORIAS_GASTOS = ["Arriendo", "Servicios básicos", "Sueldos", "Mantención", "Marketing", "Otros"]

# Genera una lista cronológica con los últimos meses en formato de texto (AAAA-MM), retrocediendo el año si corresponde.
def _meses(cantidad_meses_retroceder=12):
    año_actual = date.today().year
    mes_actual = date.today().month
    
    lista_meses_calculados = []
    
    for _ in range(cantidad_meses_retroceder):
        texto_mes_formateado = f"{año_actual}-{mes_actual:02d}"
        lista_meses_calculados.append(texto_mes_formateado)
        
        mes_actual = mes_actual - 1
        if mes_actual == 0:
            año_actual = año_actual - 1
            mes_actual = 12
            
    return lista_meses_calculados

# Toma los registros agrupados de la base de datos y los concatena en una sola línea descriptiva con sus montos y cantidades.
def _desglose(filas_agrupadas, mensaje_vacio="Sin movimientos este mes"):
    if not filas_agrupadas:
        return mensaje_vacio
        
    lista_bloques_texto = []
    for fila in filas_agrupadas:
        nombre_grupo = fila['grupo']
        monto_formateado = moneda(fila['total'])
        cantidad_movimientos = fila['n']
        
        texto_bloque = f"{nombre_grupo}: {monto_formateado} ({cantidad_movimientos})"
        lista_bloques_texto.append(texto_bloque)
        
    texto_final_unido = "   ·   ".join(lista_bloques_texto)
    return texto_final_unido

# Clase gráfica que construye el panel principal de control financiero y contable con balances en tiempo real.
class FinanzasFrame(ctk.CTkFrame):
    def __init__(self, componente_padre, aplicacion_principal):
        super().__init__(componente_padre, fg_color="transparent")
        self.mes_actual_filtro = date.today().strftime("%Y-%m")

        marco_cabecera_finanzas = ctk.CTkFrame(self, fg_color="transparent")
        marco_cabecera_finanzas.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            marco_cabecera_finanzas, 
            text="Finanzas", 
            font=("Segoe UI", 24, "bold")
        ).pack(side="left")
        
        self.selector_mes_filtro = ctk.CTkComboBox(
            marco_cabecera_finanzas, 
            values=_meses(), 
            state="readonly", 
            width=130, 
            command=self._cambiar_mes
        )
        self.selector_mes_filtro.set(self.mes_actual_filtro)
        self.selector_mes_filtro.pack(side="right")
        
        ctk.CTkLabel(marco_cabecera_finanzas, text="Mes:").pack(side="right", padx=8)

        contenedor_tarjetas_resumen = ctk.CTkFrame(self, fg_color="transparent")
        contenedor_tarjetas_resumen.pack(fill="x")
        
        # Inicializamos los tres visores informativos superiores con sus respectivos colores institucionales
        self.tarjeta_ingresos_brutos = self._tarjeta(contenedor_tarjetas_resumen, "Ingresos (ganancias)", VERDE)
        self.tarjeta_gastos_totales = self._tarjeta(contenedor_tarjetas_resumen, "Gastos", ROJO)
        self.tarjeta_ganancia_neta = self._tarjeta(contenedor_tarjetas_resumen, "Ganancia neta (ingresos − gastos)", AZUL)

        # Inicialización del navegador de pestañas para dividir la contabilidad de la empresa
        self.navegador_pestañas_finanzas = ctk.CTkTabview(self)
        self.navegador_pestañas_finanzas.pack(fill="both", expand=True, pady=(12, 0))
        
        pestaña_ingresos_caja = self.navegador_pestañas_finanzas.add("Ingresos")
        pestaña_gastos_caja = self.navegador_pestañas_finanzas.add("Gastos")

        # ---------- pestaña Ingresos ----------
        ctk.CTkLabel(
            pestaña_ingresos_caja, 
            text="De dónde vienen los ingresos (pagos de socios registrados)",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        
        self.etiqueta_resumen_ingresos_plan = ctk.CTkLabel(
            pestaña_ingresos_caja, 
            text="", 
            anchor="w", 
            justify="left", 
            wraplength=900
        )
        self.etiqueta_resumen_ingresos_plan.pack(anchor="w", pady=(4, 0))
        
        self.etiqueta_resumen_ingresos_metodo = ctk.CTkLabel(
            pestaña_ingresos_caja, 
            text="", 
            anchor="w", 
            justify="left", 
            wraplength=900
        )
        self.etiqueta_resumen_ingresos_metodo.pack(anchor="w", pady=(0, 8))
        
        columnas_tabla_ingresos_finanzas = ("Fecha", "Origen: socio", "RUT", "Plan pagado", "Método", "Monto")
        anchos_columnas_ingresos_finanzas = (95, 240, 120, 170, 120, 110)
        
        marco_tabla_ingresos_finanzas, self.tabla_detalle_ingresos_finanzas = tabla(
            pestaña_ingresos_caja, 
            columnas_tabla_ingresos_finanzas, 
            anchos_columnas_ingresos_finanzas
        )
        marco_tabla_ingresos_finanzas.pack(fill="both", expand=True)

        # ---------- pestaña Gastos ----------
        fila_formulario_gastos = ctk.CTkFrame(pestaña_gastos_caja, fg_color="transparent")
        fila_formulario_gastos.pack(fill="x", pady=(0, 6))
        
        self.campo_concepto_gasto = ctk.CTkEntry(
            fila_formulario_gastos, 
            placeholder_text="Concepto del gasto", 
            width=260, 
            height=34
        )
        self.campo_concepto_gasto.pack(side="left")
        
        self.campo_categoria_gasto = ctk.CTkComboBox(
            fila_formulario_gastos, 
            values=CATEGORIAS_GASTOS, 
            state="readonly", 
            width=180, 
            height=34
        )
        # El desplegable necesita UN solo texto marcado: dejamos elegida la primera categoría de la lista.
        primera_categoria = CATEGORIAS_GASTOS[0]
        self.campo_categoria_gasto.set(primera_categoria)
        self.campo_categoria_gasto.pack(side="left", padx=10)
        
        self.campo_monto_gasto = ctk.CTkEntry(
            fila_formulario_gastos, 
            placeholder_text="Monto", 
            width=120, 
            height=34
        )
        self.campo_monto_gasto.pack(side="left")
        
        ctk.CTkButton(
            fila_formulario_gastos, 
            text="Agregar gasto", 
            height=34, 
            command=self.agregar
        ).pack(side="left", padx=10)
        
        self.etiqueta_alertas_gastos = ctk.CTkLabel(fila_formulario_gastos, text="", text_color=ROJO)
        self.etiqueta_alertas_gastos.pack(side="left")
        
        ctk.CTkLabel(
            pestaña_gastos_caja, 
            text="Gastos por categoría", 
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        
        self.etiqueta_resumen_gastos_categoria = ctk.CTkLabel(
            pestaña_gastos_caja, 
            text="", 
            anchor="w", 
            justify="left", 
            wraplength=900
        )
        self.etiqueta_resumen_gastos_categoria.pack(anchor="w", pady=(4, 8))
        
        columnas_tabla_gastos_finanzas = ("Fecha", "Concepto", "Categoría", "Monto")
        anchos_columnas_gastos_finanzas = (110, 320, 180, 130)
        
        marco_tabla_gastos_finanzas, self.tabla_detalle_gastos_finanzas = tabla(
            pestaña_gastos_caja, 
            columnas_tabla_gastos_finanzas, 
            anchos_columnas_gastos_finanzas
        )
        marco_tabla_gastos_finanzas.pack(fill="both", expand=True)

        self.cargar()

    # Método estático auxiliar que automatiza la creación estética y simétrica de los paneles de balances superiores.
    @staticmethod
    def _tarjeta(componente_padre, texto_titulo, color_fondo_tarjeta):
        marco_tarjeta = ctk.CTkFrame(componente_padre, fg_color=color_fondo_tarjeta, corner_radius=12)
        marco_tarjeta.pack(side="left", padx=(0, 15), ipadx=20, ipady=8)
        
        ctk.CTkLabel(
            marco_tarjeta, 
            text=texto_titulo, 
            font=("Segoe UI", 13), 
            text_color="white"
        ).pack(padx=20, pady=(8, 0))
        
        etiqueta_valor_dinero = ctk.CTkLabel(
            marco_tarjeta, 
            text="$0", 
            font=("Segoe UI", 24, "bold"), 
            text_color="white"
        )
        etiqueta_valor_dinero.pack(padx=20, pady=(0, 8))
        
        return etiqueta_valor_dinero

    # Modifica el periodo temporal de consulta en la memoria y gatilla la actualización contable completa en pantalla.
    def _cambiar_mes(self, mes_seleccionado):
        self.mes_actual_filtro = mes_seleccionado
        self.cargar()

    # Extrae los balances y reportes agrupados desde el repositorio y repobla de forma íntegra las planillas de caja.
    def cargar(self):
        reporte_valores_mes = repo.resumen_mes(self.mes_actual_filtro)
        
        self.tarjeta_ingresos_brutos.configure(text=moneda(reporte_valores_mes["ingresos"]))
        self.tarjeta_gastos_totales.configure(text=moneda(reporte_valores_mes["gastos"]))
        self.tarjeta_ganancia_neta.configure(text=moneda(reporte_valores_mes["balance"]))
        
        # Si el balance neto da pérdidas (menor a cero), cambiamos el fondo de la tarjeta a color rojo de alerta
        if reporte_valores_mes["balance"] >= 0:
            color_tarjeta_balance = AZUL
        else:
            color_tarjeta_balance = ROJO
            
        self.tarjeta_ganancia_neta.master.configure(fg_color=color_tarjeta_balance)

        # 1. Procesamiento y actualización de datos de la pestaña de Ingresos
        ingresos_agrupados_plan = repo.ingresos_agrupados(self.mes_actual_filtro, "plan")
        self.etiqueta_resumen_ingresos_plan.configure(text=f"Por plan →  {_desglose(ingresos_agrupados_plan)}")
        
        ingresos_agrupados_metodo = repo.ingresos_agrupados(self.mes_actual_filtro, "metodo")
        self.etiqueta_resumen_ingresos_metodo.configure(text=f"Por método de pago →  {_desglose(ingresos_agrupados_metodo)}")
        
        for registro_ingreso in self.tabla_detalle_ingresos_finanzas.get_children():
            self.tabla_detalle_ingresos_finanzas.delete(registro_ingreso)
            
        lista_ingresos_leidos = repo.listar_ingresos(self.mes_actual_filtro)
        for ingreso in lista_ingresos_leidos:
            valores_fila_ingreso = (
                ingreso["fecha"], 
                ingreso["socio"], 
                ingreso["rut"], 
                ingreso["plan"],
                ingreso["metodo"], 
                moneda(ingreso["monto"])
            )
            self.tabla_detalle_ingresos_finanzas.insert("", "end", values=valores_fila_ingreso)

        # 2. Procesamiento y actualización de datos de la pestaña de Gastos
        gastos_agrupados_categoria = repo.gastos_por_categoria(self.mes_actual_filtro)
        self.etiqueta_resumen_gastos_categoria.configure(text=_desglose(gastos_agrupados_categoria, "Sin gastos este mes"))
        
        for registro_gasto in self.tabla_detalle_gastos_finanzas.get_children():
            self.tabla_detalle_gastos_finanzas.delete(registro_gasto)
            
        lista_gastos_leidos = repo.listar_gastos(self.mes_actual_filtro)
        for gasto in lista_gastos_leidos:
            valores_fila_gasto = (
                gasto["fecha"], 
                gasto["concepto"], 
                gasto["categoria"], 
                moneda(gasto["monto"])
            )
            self.tabla_detalle_gastos_finanzas.insert("", "end", values=valores_fila_gasto)

    # Valida el concepto y monto del egreso, registra el gasto en la base de datos y desplaza el filtro al mes actual.
    def agregar(self):
        texto_concepto = self.campo_concepto_gasto.get().strip()
        texto_monto = self.campo_monto_gasto.get().strip()
        
        if not texto_concepto or not texto_monto.isdigit() or int(texto_monto) <= 0:
            self.etiqueta_alertas_gastos.configure(text="Concepto y monto (entero > 0) son obligatorios.")
            return
            
        categoria_seleccionada = self.campo_categoria_gasto.get()
        monto_entero_gasto = int(texto_monto)
        repo.crear_gasto(texto_concepto, categoria_seleccionada, monto_entero_gasto)
        
        # Limpiamos las casillas de texto para dejarlas listas para el próximo registro
        self.campo_concepto_gasto.delete(0, "end")
        self.campo_monto_gasto.delete(0, "end")
        self.etiqueta_alertas_gastos.configure(text="")
        
        # Forzamos que el visor regrese al año y mes actual para visualizar el gasto recién ingresado
        self.mes_actual_filtro = date.today().strftime("%Y-%m")
        self.selector_mes_filtro.set(self.mes_actual_filtro)
        
        self.cargar()


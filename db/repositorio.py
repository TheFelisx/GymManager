"""
CAPA DE DATOS TEMPORAL (SQLite).

Nota de migración: Al cambiar a Oracle, mantén los nombres de las funciones y sus 
valores de retorno. Solo debes cambiar el código interno (oracledb y ':1').
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
from logica.auth import hash_clave
from logica.horarios import dentro_de_horario

# Define la ubicación física donde se creará el archivo de la base de datos local.
RUTA_BD = os.path.join(os.path.dirname(__file__), "gym_temp.db")

# Abre una conexión con la base de datos activando la lectura por nombres de columna y las llaves foráneas.
def _conn():
    
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion

# Devuelve la fecha actual del sistema formateada como texto estandarizado (AAAA-MM-DD).
def _hoy() -> str:
    
    fecha_actual_texto = date.today().isoformat()
    return fecha_actual_texto

# Crea la estructura completa de tablas de la base de datos si es la primera vez que se ejecuta el sistema.
def inicializar():
    
    with _conn() as conexion:
        conexion.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio INTEGER NOT NULL,
            duracion_dias INTEGER NOT NULL,
            hora_inicio TEXT NOT NULL DEFAULT '00:00',
            hora_fin TEXT NOT NULL DEFAULT '23:59',
            dias TEXT NOT NULL DEFAULT '0,1,2,3,4,5,6',
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT UNIQUE NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            fecha_nac TEXT NOT NULL,
            correo TEXT NOT NULL,
            telefono TEXT NOT NULL,
            plan_id INTEGER NOT NULL REFERENCES planes(id),
            fecha_venc TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            foto TEXT
        );

        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id INTEGER NOT NULL REFERENCES socios(id),
            monto INTEGER NOT NULL,
            metodo TEXT NOT NULL,
            fecha TEXT NOT NULL,
            plan_id INTEGER REFERENCES planes(id),
            registrado_por TEXT
        );

        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto INTEGER NOT NULL,
            fecha TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS asistencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id INTEGER REFERENCES socios(id),
            fecha_hora TEXT NOT NULL,
            resultado TEXT NOT NULL
        );
        """)
        
        # Migración: las bases creadas antes de existir "activo" lo reciben (todos los usuarios quedan activos).
        # Primero anotamos en una lista los nombres de las columnas que la tabla "usuarios" tiene hoy.
        columnas_usuarios = []
        for fila in conexion.execute("PRAGMA table_info(usuarios)"):
            columnas_usuarios.append(fila["name"])

        # Si todavía no existe la columna "activo", se la agregamos sin borrar ningún dato.
        if "activo" not in columnas_usuarios:
            conexion.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")

        # Inyecta los usuarios y planes iniciales por defecto si las tablas nacen completamente vacías.
        tabla_usuarios_vacia = conexion.execute("SELECT 1 FROM usuarios").fetchone() is None
        if tabla_usuarios_vacia:
            lista_usuarios_base = [
                ("admin", hash_clave("admin123"), "administrador"),
                ("recepcion", hash_clave("recep123"), "recepcionista"),
                ("guardia", hash_clave("guardia123"), "guardia")
            ]
            sql_insertar_usuario = "INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (?, ?, ?)"
            conexion.executemany(sql_insertar_usuario, lista_usuarios_base)
            
        tabla_planes_vacia = conexion.execute("SELECT 1 FROM planes").fetchone() is None
        if tabla_planes_vacia:
            lista_planes_base = [
                ("Mensual", 25000, 30, "00:00", "23:59", "0,1,2,3,4,5,6"),
                ("Trimestral", 65000, 90, "00:00", "23:59", "0,1,2,3,4,5,6"),
                ("Anual", 220000, 365, "00:00", "23:59", "0,1,2,3,4,5,6"),
                ("Mensual Mañana", 18000, 30, "06:00", "14:00", "0,1,2,3,4")
            ]
            sql_insertar_plan = "INSERT INTO planes (nombre, precio, duracion_dias, hora_inicio, hora_fin, dias) VALUES (?, ?, ?, ?, ?, ?)"
            conexion.executemany(sql_insertar_plan, lista_planes_base)

# ---------- usuarios / planes ----------

# Busca y devuelve los datos de un usuario en la base de datos según su nombre de acceso.
def obtener_usuario(nombre_usuario: str):
    with _conn() as conexion:
        sql = "SELECT * FROM usuarios WHERE usuario = ?"
        return conexion.execute(sql, (nombre_usuario,)).fetchone()


# Devuelve todos los usuarios (sin sus contraseñas) para mostrarlos en la tabla del administrador.
def listar_usuarios():
    with _conn() as conexion:
        sql = """
            SELECT id, usuario, rol, activo
            FROM usuarios
            ORDER BY activo DESC, rol, usuario
        """
        return conexion.execute(sql).fetchall()


# Crea un usuario nuevo. Recibe la contraseña YA cifrada. Lanza ValueError si el nombre ya existe.
def crear_usuario(nombre_usuario, clave_hash, rol):
    with _conn() as conexion:
        # Primero revisamos si ya hay alguien con ese nombre (sin distinguir mayúsculas de minúsculas).
        sql_buscar_repetido = "SELECT 1 FROM usuarios WHERE LOWER(usuario) = LOWER(?)"
        fila_repetida = conexion.execute(sql_buscar_repetido, (nombre_usuario,)).fetchone()
        if fila_repetida is not None:
            raise ValueError("Ya existe un usuario con ese nombre.")

        # Si no existe, lo guardamos. La columna "activo" toma sola su valor por defecto (1 = activo).
        sql_insertar = "INSERT INTO usuarios (usuario, clave_hash, rol) VALUES (?, ?, ?)"
        resultado = conexion.execute(sql_insertar, (nombre_usuario, clave_hash, rol))
        return resultado.lastrowid


# Activa o desactiva un usuario. Uno desactivado no puede iniciar sesión, pero su registro se conserva.
def cambiar_estado_usuario(id_usuario, activo: bool):
    # La base de datos guarda 1 para "activo" y 0 para "desactivado".
    if activo:
        valor_activo = 1
    else:
        valor_activo = 0

    with _conn() as conexion:
        conexion.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (valor_activo, id_usuario))


# Cuenta los administradores activos (para no dejar nunca el sistema sin ninguno).
def contar_administradores_activos():
    with _conn() as conexion:
        sql = "SELECT COUNT(*) FROM usuarios WHERE rol = 'administrador' AND activo = 1"
        fila = conexion.execute(sql).fetchone()
        cantidad = fila[0]
        return cantidad


# Retorna la lista de planes ordenados por duración y precio, con opción de filtrar solo los vigentes.
def listar_planes(solo_activos=True):
    if solo_activos:
        sql = "SELECT * FROM planes WHERE activo = 1 ORDER BY duracion_dias, precio"
    else:
        sql = "SELECT * FROM planes ORDER BY duracion_dias, precio"
        
    with _conn() as conexion:
        return conexion.execute(sql).fetchall()


# Registra un nuevo plan en el sistema, lanzando un error si el nombre ya está registrado.
def crear_plan(nombre, precio, duracion, hora_inicio, hora_fin, dias):
    with _conn() as conexion:
        sql_verificar = "SELECT 1 FROM planes WHERE LOWER(nombre) = LOWER(?)"
        if conexion.execute(sql_verificar, (nombre,)).fetchone():
            raise ValueError("Ya existe un plan con ese nombre.")
            
        sql_insertar = """
            INSERT INTO planes (nombre, precio, duracion_dias, hora_inicio, hora_fin, dias) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        parametros = (nombre, precio, duracion, hora_inicio, hora_fin, dias)
        cursor = conexion.execute(sql_insertar, parametros)
        return cursor.lastrowid


# Desactiva o activa un plan de membresía utilizando su ID para que no pueda ser asignado a nuevos socios.
def cambiar_estado_plan(plan_id, activo: bool):
    if activo:
        estado_numerico = 1
    else:
        estado_numerico = 0
        
    sql = "UPDATE planes SET activo = ? WHERE id = ?"
    with _conn() as conexion:
        conexion.execute(sql, (estado_numerico, plan_id))

# ---------- socios ----------
_SQL_SOCIO = """SELECT s.*, p.nombre AS plan, p.precio AS precio_plan,
                       p.hora_inicio, p.hora_fin, p.dias
                FROM socios s JOIN planes p ON p.id = s.plan_id"""


# Calcula y devuelve la situación del socio actual ('Activo', 'Vencido' o 'Baja') según sus fechas y vigencia.
def estado_socio(socio) -> str:
    if not socio["activo"]:
        return "Baja"
        
    if socio["fecha_venc"] >= _hoy():
        return "Activo"
    else:
        return "Vencido"

# Registra un nuevo socio calculando su vencimiento e inyectando de forma automática su primer pago en caja.
def crear_socio(rut, nombres, apellidos, fecha_nac, correo, telefono, plan_id, usuario=None):
    with _conn() as conexion:
        sql_verificar = "SELECT 1 FROM socios WHERE rut = ?"
        if conexion.execute(sql_verificar, (rut,)).fetchone():
            raise ValueError("Ya existe un socio con ese RUT.")
            
        sql_plan = "SELECT * FROM planes WHERE id = ?"
        plan = conexion.execute(sql_plan, (plan_id,)).fetchone()
        
        calculo_dias = timedelta(days=plan["duracion_dias"])
        fecha_vencimiento = (date.today() + calculo_dias).isoformat()
        
        sql_insertar_socio = """
            INSERT INTO socios (rut, nombres, apellidos, fecha_nac, correo, telefono, plan_id, fecha_venc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros_socio = (rut, nombres, apellidos, fecha_nac.isoformat(), correo, telefono, plan_id, fecha_vencimiento)
        cursor_socio = conexion.execute(sql_insertar_socio, parametros_socio)
        
        id_nuevo_socio = cursor_socio.lastrowid
        
        sql_insertar_pago = """
            INSERT INTO pagos (socio_id, plan_id, monto, metodo, fecha, registrado_por)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        parametros_pago = (id_nuevo_socio, plan_id, plan["precio"], "Efectivo", _hoy(), usuario)
        conexion.execute(sql_insertar_pago, parametros_pago)
        
        return id_nuevo_socio

# Busca socios en el sistema filtrando de forma parcial por su RUT, nombres o apellidos, de forma ordenada.
def buscar_socios(texto_busqueda: str = ""):
    texto_comodin = f"%{texto_busqueda.strip()}%"
    
    sql_completo = _SQL_SOCIO + """ 
        WHERE s.rut LIKE ? 
           OR s.nombres LIKE ?
           OR s.apellidos LIKE ? 
        ORDER BY s.apellidos
    """
    parametros = (texto_comodin, texto_comodin, texto_comodin)
    
    with _conn() as conexion:
        return conexion.execute(sql_completo, parametros).fetchall()


# Recupera la información detallada de un socio específico utilizando su número de RUT.
def obtener_socio_por_rut(rut_socio: str):
    sql_completo = _SQL_SOCIO + " WHERE s.rut = ?"
    
    with _conn() as conexion:
        return conexion.execute(sql_completo, (rut_socio,)).fetchone()


# Modifica los datos personales y el plan de un socio existente, conservando su foto si no se envía una nueva.
def actualizar_socio(socio_id, nombres, apellidos, correo, telefono, plan_id, foto=None):
    sql = """
        UPDATE socios 
        SET nombres = ?,
            apellidos = ?,
            correo = ?,
            telefono = ?,
            plan_id = ?,
            foto = COALESCE(?, foto) 
        WHERE id = ?
    """
    parametros = (nombres, apellidos, correo, telefono, plan_id, foto, socio_id)
    
    with _conn() as conexion:
        conexion.execute(sql, parametros)


# Actualiza exclusivamente la ruta de la fotografía de perfil de un socio en su registro.
def actualizar_foto(socio_id, nombre_foto):
    sql = "UPDATE socios SET foto = ? WHERE id = ?"
    
    with _conn() as conexion:
        conexion.execute(sql, (nombre_foto, socio_id))


# Desactiva el acceso de un socio al gimnasio sin eliminar su registro ni su historial de la base de datos.
def dar_de_baja(socio_id):
    sql = "UPDATE socios SET activo = 0 WHERE id = ?"
    
    with _conn() as conexion:
        conexion.execute(sql, (socio_id,))

# ---------- resumen por plan (vista del administrador) ----------

# Genera un reporte estadístico detallado de cada plan, calculando socios vigentes, totales e ingresos mensuales e históricos.
def resumen_planes(mes_busqueda: str):
    fecha_hoy = _hoy()
    formato_mes_comodin = f"{mes_busqueda}%"
    
    # Consulta base para calcular los ingresos mensuales filtrando por la fecha del pago
    sql_ingresos_mes = """
        (SELECT COALESCE(SUM(pg.monto), 0) 
         FROM pagos pg 
         JOIN socios s ON s.id = pg.socio_id
         WHERE COALESCE(pg.plan_id, s.plan_id) = p.id 
           AND pg.fecha LIKE ?)
    """
    
    # Consulta base para calcular los ingresos históricos totales acumulados del plan
    sql_ingresos_total = """
        (SELECT COALESCE(SUM(pg.monto), 0) 
         FROM pagos pg 
         JOIN socios s ON s.id = pg.socio_id
         WHERE COALESCE(pg.plan_id, s.plan_id) = p.id)
    """
    
    # Ensamblamos la gran consulta de control financiero para el administrador
    sql_principal = f"""
        SELECT p.*,
          (SELECT COUNT(*) FROM socios s 
           WHERE s.plan_id = p.id 
             AND s.activo = 1
             AND s.fecha_venc >= ?) AS socios_vigentes,
             
          (SELECT COUNT(*) FROM socios s 
           WHERE s.plan_id = p.id 
             AND s.activo = 1) AS socios_total,
             
          {sql_ingresos_mes} AS ingresos_mes,
          {sql_ingresos_total} AS ingresos_total
        FROM planes p 
        ORDER BY p.activo DESC, ingresos_total DESC, p.nombre
    """
    
    parametros = (fecha_hoy, formato_mes_comodin)
    
    with _conn() as conexion:
        return conexion.execute(sql_principal, parametros).fetchall()


# Retorna todos los socios asociados a un plan específico, ordenando primero los activos y por apellido alfabético.
def socios_del_plan(plan_id: int):
    sql = _SQL_SOCIO + " WHERE s.plan_id = ? ORDER BY s.activo DESC, s.apellidos"
    
    with _conn() as conexion:
        return conexion.execute(sql, (plan_id,)).fetchall()


# ---------- pagos (solo REGISTRO: el programa no procesa cobros) ----------

# Registra un pago en caja, extiende la fecha de vencimiento del socio de forma inteligente y actualiza su plan.
def registrar_pago(socio_id, plan_id, monto, metodo, usuario=None):
    with _conn() as conexion:
        sql_socio = "SELECT * FROM socios WHERE id = ?"
        socio = conexion.execute(sql_socio, (socio_id,)).fetchone()
        
        if not socio["activo"]:
            raise ValueError("El socio está dado de baja; no se pueden registrar pagos.")
            
        sql_plan = "SELECT * FROM planes WHERE id = ?"
        plan = conexion.execute(sql_plan, (plan_id,)).fetchone()
        
        fecha_vencimiento_actual = date.fromisoformat(socio["fecha_venc"])
        fecha_hoy = date.today()
        
        # Si la membresía actual vence en el futuro, sumamos los días desde ahí. Si ya venció, sumamos desde hoy.
        if fecha_vencimiento_actual > fecha_hoy:
            fecha_base_calculo = fecha_vencimiento_actual
        else:
            fecha_base_calculo = fecha_hoy
            
        calculo_dias = timedelta(days=plan["duracion_dias"])
        nueva_fecha_vencimiento = (fecha_base_calculo + calculo_dias).isoformat()
        
        sql_insertar_pago = """
            INSERT INTO pagos (socio_id, plan_id, monto, metodo, fecha, registrado_por) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        parametros_pago = (socio_id, plan_id, monto, metodo, _hoy(), usuario)
        conexion.execute(sql_insertar_pago, parametros_pago)
        
        sql_actualizar_socio = "UPDATE socios SET plan_id = ?, fecha_venc = ? WHERE id = ?"
        conexion.execute(sql_actualizar_socio, (plan_id, nueva_fecha_vencimiento, socio_id))
        
        return nueva_fecha_vencimiento


# Obtiene el historial de pagos de la caja ordenados del más reciente al más antiguo, con opción de filtro.
def listar_pagos(texto_busqueda="", limite_registros=300):
    texto_comodin = f"%{texto_busqueda.strip()}%"
    
    sql_completo = """
        SELECT pg.id, 
               pg.fecha, 
               pg.monto, 
               pg.metodo, 
               pg.registrado_por, 
               s.rut,
               s.nombres || ' ' || s.apellidos AS socio,
               COALESCE(pl.nombre, ps.nombre) AS plan
        FROM pagos pg
        JOIN socios s ON s.id = pg.socio_id
        JOIN planes ps ON ps.id = s.plan_id
        LEFT JOIN planes pl ON pl.id = pg.plan_id
        WHERE s.rut LIKE ? 
           OR s.nombres LIKE ? 
           OR s.apellidos LIKE ?
        ORDER BY pg.id DESC 
        LIMIT ?
    """
    parametros = (texto_comodin, texto_comodin, texto_comodin, limite_registros)
    
    with _conn() as conexion:
        return conexion.execute(sql_completo, parametros).fetchall()

# ---------- tótem ----------

# Procesa el intento de entrada de un socio por su RUT, registra el resultado en la base de datos y decide si abre el acceso.
def registrar_acceso(rut_socio: str):
    socio = obtener_socio_por_rut(rut_socio)
    
    if socio is None:
        resultado_acceso = "Denegado"
        mensaje_pantalla = "RUT no registrado"
    else:
        situacion_membresia = estado_socio(socio)
        
        if situacion_membresia != "Activo":
            resultado_acceso = "Denegado"
            mensaje_pantalla = f"Membresía {situacion_membresia.lower()}"
        else:
            en_horario, motivo_bloqueo = dentro_de_horario(socio)
            
            if en_horario:
                resultado_acceso = "Permitido"
                mensaje_pantalla = f"Bienvenido/a, {socio['nombres']}"
            else:
                resultado_acceso = "Denegado"
                mensaje_pantalla = motivo_bloqueo
                
    if socio:
        id_socio_registro = socio["id"]
    else:
        id_socio_registro = None
        
    fecha_hora_actual = datetime.now().isoformat(timespec="seconds")
    sql_asistencia = "INSERT INTO asistencias (socio_id, fecha_hora, resultado) VALUES (?, ?, ?)"
    
    with _conn() as conexion:
        conexion.execute(sql_asistencia, (id_socio_registro, fecha_hora_actual, resultado_acceso))
        
    permitir_ingreso = resultado_acceso == "Permitido"
    return permitir_ingreso, mensaje_pantalla, socio

# ---------- finanzas ----------
_FROM_INGRESOS = """
    FROM pagos pg
    JOIN socios s ON s.id = pg.socio_id
    JOIN planes ps ON ps.id = s.plan_id
    LEFT JOIN planes pl ON pl.id = pg.plan_id
"""
_GRUPOS = {
    "plan": "COALESCE(pl.nombre, ps.nombre)", 
    "metodo": "pg.metodo"
}

# Obtiene la lista detallada de todos los pagos recibidos durante un mes específico, con datos del socio y del plan.
def listar_ingresos(mes_busqueda: str):
    formato_mes_comodin = f"{mes_busqueda}%"
    
    sql_completo = f"""
        SELECT pg.fecha, 
               s.nombres || ' ' || s.apellidos AS socio, 
               s.rut,
               COALESCE(pl.nombre, ps.nombre) AS plan, 
               pg.metodo, 
               pg.monto 
        {_FROM_INGRESOS}
        WHERE pg.fecha LIKE ? 
        ORDER BY pg.fecha DESC, pg.id DESC
    """
    
    with _conn() as conexion:
        return conexion.execute(sql_completo, (formato_mes_comodin,)).fetchall()

# Calcula el total de dinero recaudado en el mes, agrupado dinámicamente por tipo de plan o por método de pago.
def ingresos_agrupados(mes_busqueda: str, criterio_agrupacion: str):
    columna_grupo_sql = _GRUPOS[criterio_agrupacion]
    formato_mes_comodin = f"{mes_busqueda}%"
    
    sql_completo = f"""
        SELECT {columna_grupo_sql} AS grupo, 
               SUM(pg.monto) AS total, 
               COUNT(*) AS n 
        {_FROM_INGRESOS}
        WHERE pg.fecha LIKE ? 
        GROUP BY grupo 
        ORDER BY total DESC
    """
    
    with _conn() as conexion:
        return conexion.execute(sql_completo, (formato_mes_comodin,)).fetchall()

# Suma el total de dinero perdido en gastos durante el mes, agrupado ordenadamente por cada categoría.
def gastos_por_categoria(mes_busqueda: str):
    formato_mes_comodin = f"{mes_busqueda}%"
    sql = """
        SELECT categoria AS grupo, 
               SUM(monto) AS total, 
               COUNT(*) AS n 
        FROM gastos 
        WHERE fecha LIKE ? 
        GROUP BY categoria 
        ORDER BY total DESC
    """
    
    with _conn() as conexion:
        return conexion.execute(sql, (formato_mes_comodin,)).fetchall()

# Registra una nueva salida de dinero en la tabla de egresos asociándole de forma automática la fecha de hoy.
def crear_gasto(concepto, categoria, monto):
    sql = "INSERT INTO gastos (concepto, categoria, monto, fecha) VALUES (?, ?, ?, ?)"
    parametros = (concepto, categoria, monto, _hoy())
    
    with _conn() as conexion:
        conexion.execute(sql, parametros)

# Obtiene la cartola detallada con todos los gastos realizados en el mes, ordenados cronológicamente.
def listar_gastos(mes_busqueda: str):
    formato_mes_comodin = f"{mes_busqueda}%"
    sql = "SELECT * FROM gastos WHERE fecha LIKE ? ORDER BY fecha DESC"
    
    with _conn() as conexion:
        return conexion.execute(sql, (formato_mes_comodin,)).fetchall()

# Calcula el balance financiero total del mes comparando de forma directa las entradas y salidas de dinero.
def resumen_mes(mes_busqueda: str):
    formato_mes_comodin = f"{mes_busqueda}%"
    
    sql_ingresos = "SELECT COALESCE(SUM(monto), 0) FROM pagos WHERE fecha LIKE ?"
    sql_gastos = "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha LIKE ?"
    
    with _conn() as conexion:
        fila_ingresos = conexion.execute(sql_ingresos, (formato_mes_comodin,)).fetchone()
        total_ingresos = fila_ingresos[0]
        
        fila_gastos = conexion.execute(sql_gastos, (formato_mes_comodin,)).fetchone()
        total_gastos = fila_gastos[0]
        
    balance_neto = total_ingresos - total_gastos
    
    reporte_financiero = {
        "ingresos": total_ingresos, 
        "gastos": total_gastos, 
        "balance": balance_neto
    }
    
    return reporte_financiero

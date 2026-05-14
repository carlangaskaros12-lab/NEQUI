# Documentacion del proyecto

## 1. Que es este proyecto

Este proyecto es una aplicacion web pequena hecha con **Python**, **Flask**, **HTML**, **CSS**, **JavaScript** y **SQLite**.

La idea principal es simular un sistema de prueba donde una persona ingresa tres datos:

- Identificador demo
- Dato privado demo
- Codigo dinamico demo

Luego esos datos llegan a un **dashboard**, donde otra persona puede revisar si la informacion es correcta o incorrecta.

Si la informacion es incorrecta, el dashboard permite indicar cual campo esta mal. Despues, la pantalla de ingreso muestra ese resultado.

Importante: este proyecto es solo de prueba. No se debe usar para capturar informacion real.

## 2. Tecnologias usadas

### Python

Python es el lenguaje principal del backend. El backend es la parte que procesa datos, guarda informacion y responde a las paginas web.

### Flask

Flask es un framework de Python para crear aplicaciones web. En este proyecto se usa para:

- Crear rutas como `/`, `/ingresar` y `/estado/<id>`.
- Recibir formularios.
- Mostrar plantillas HTML.
- Conectar la aplicacion con la base de datos.

### SQLite

SQLite es una base de datos sencilla que guarda la informacion en un archivo local.

En este proyecto, la base de datos se llama:

```text
proyecto_prueba.db
```

SQLite es buena opcion para proyectos pequenos porque no necesita instalar un servidor de base de datos.

### HTML

HTML se usa para crear la estructura visual de las paginas.

Por ejemplo:

- Titulos
- Formularios
- Botones
- Tablas

### CSS

CSS se usa para darle estilo a las paginas.

Por ejemplo:

- Colores
- Tamaños
- Bordes
- Posicion de los elementos

### JavaScript

JavaScript se usa en la pantalla de ingreso para consultar automaticamente si el registro ya fue revisado.

Esto permite que la pantalla quede cargando hasta que el dashboard marque el dato como correcto o incorrecto.

## 3. Estructura de archivos

El proyecto tiene esta estructura principal:

```text
proyecto1/
│
├── app.py
├── proyecto_prueba.db
├── DOCUMENTACION.md
│
└── templates/
    ├── index.html
    ├── ingresar.html
    └── generar.html
```

### app.py

Es el archivo principal de la aplicacion.

Aqui esta la logica del servidor:

- Configuracion de Flask.
- Conexion con SQLite.
- Creacion de la tabla.
- Registro de datos.
- Revision de registros.
- Consulta del estado de un registro.

### templates/index.html

Es la plantilla del dashboard.

Desde esta pantalla se puede:

- Ver los registros pendientes.
- Marcar un registro como correcto.
- Marcar un registro como incorrecto.
- Escoger que campo esta incorrecto.
- Ver el historial de registros revisados.

### templates/ingresar.html

Es la pantalla donde se ingresan los datos de prueba.

Desde esta pantalla se puede:

- Escribir los datos.
- Enviarlos al sistema.
- Esperar mientras el dashboard revisa el registro.
- Ver si un campo fue marcado como incorrecto.

### proyecto_prueba.db

Es el archivo de base de datos SQLite.

Aqui se guardan los registros ingresados y revisados.

## 4. Como ejecutar el proyecto

Primero se debe abrir PowerShell en la carpeta del proyecto:

```powershell
cd C:\Users\Calitrou\Desktop\proyecto1
```

Luego se ejecuta:

```powershell
python app.py
```

Si el puerto 5000 esta ocupado, se puede usar:

```powershell
python -m flask --app app run --port 5001
```

Despues se abre el navegador en:

```text
http://127.0.0.1:5001/ingresar
```

Para abrir el dashboard:

```text
http://127.0.0.1:5001/
```

## 5. Explicacion de app.py

### Importaciones

```python
from datetime import datetime
from pathlib import Path
import sqlite3

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
```

Estas lineas importan herramientas necesarias.

`datetime` sirve para guardar la fecha y hora.

`Path` ayuda a manejar rutas de archivos.

`sqlite3` permite usar la base de datos SQLite.

`Flask` y las demas funciones sirven para crear la aplicacion web.

### Configuracion inicial

```python
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "proyecto_prueba.db"

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-desarrollo"
```

`BASE_DIR` obtiene la carpeta donde esta el proyecto.

`DATABASE` indica donde se guardara la base de datos.

`app = Flask(__name__)` crea la aplicacion Flask.

`secret_key` permite usar sesiones y mensajes temporales.

### Diccionarios del sistema

```python
ESTADOS = {
    "pendiente": "Pendiente",
    "correcta": "Correcta",
    "incorrecta": "Incorrecta",
}
```

Este diccionario guarda los estados posibles de un registro.

```python
CAMPOS_INCORRECTOS = {
    "numero_clave": "Numero clave",
    "clave": "Clave",
    "clave_dinamica": "Clave dinamica",
    "varios": "Varios campos",
}
```

Este diccionario indica que campos se pueden marcar como incorrectos.

## 6. Base de datos

La funcion `init_db()` crea la tabla si no existe.

La tabla se llama `ingresos`.

Tiene estos campos:

```text
id
numero_clave
clave
clave_dinamica
estado
campo_incorrecto
nota_revision
creado_en
revisado_en
```

### Que significa cada campo

`id`: identificador unico de cada registro.

`numero_clave`: primer dato ingresado desde el formulario.

`clave`: segundo dato ingresado desde el formulario.

`clave_dinamica`: tercer dato ingresado desde el formulario.

`estado`: indica si el registro esta pendiente, correcto o incorrecto.

`campo_incorrecto`: guarda cual campo esta mal si el registro fue marcado como incorrecto.

`nota_revision`: guarda una nota opcional escrita desde el dashboard.

`creado_en`: fecha y hora en que se creo el registro.

`revisado_en`: fecha y hora en que se reviso el registro.

## 7. Rutas principales

### Ruta `/`

Esta ruta muestra el dashboard.

```python
@app.route("/")
def index():
```

Desde aqui se consultan:

- Registros pendientes.
- Historial.
- Totales.

Luego se muestra la plantilla:

```python
return render_template("index.html", ...)
```

### Ruta `/ingresar`

Esta ruta muestra el formulario de ingreso.

```python
@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
```

Si el metodo es `GET`, solo muestra la pagina.

Si el metodo es `POST`, significa que el usuario envio el formulario.

Cuando se envia el formulario:

1. Se leen los datos.
2. Se valida que no esten vacios.
3. Se guardan en SQLite.
4. Se guarda el id del registro en la sesion.
5. La pantalla vuelve a cargar, pero queda esperando revision.

### Ruta `/revisar/<int:registro_id>`

Esta ruta se usa desde el dashboard para revisar un registro.

```python
@app.route("/revisar/<int:registro_id>", methods=["POST"])
def revisar(registro_id):
```

Permite marcar el registro como:

- Correcto
- Incorrecto

Si es incorrecto, tambien guarda cual campo fallo.

### Ruta `/estado/<int:registro_id>`

Esta ruta devuelve el estado de un registro en formato JSON.

```python
@app.route("/estado/<int:registro_id>")
def estado(registro_id):
```

La usa JavaScript desde `ingresar.html`.

Sirve para saber si el registro sigue pendiente o si ya fue revisado.

## 8. Flujo completo del proyecto

1. El usuario entra a:

```text
/ingresar
```

2. Escribe los datos de prueba.

3. Presiona el boton `Entrar`.

4. Flask guarda los datos en SQLite con estado `pendiente`.

5. La pantalla de ingreso queda mostrando:

```text
Validando informacion...
```

6. El administrador entra al dashboard:

```text
/
```

7. El administrador revisa el registro.

8. Si esta correcto, lo marca como `Correcta`.

9. Si esta incorrecto, escoge el campo incorrecto.

10. La pantalla de ingreso consulta la ruta `/estado/<id>` cada 2 segundos.

11. Cuando detecta que el registro fue revisado, muestra el resultado.

Ejemplo:

```text
Campo incorrecto: Clave
```

## 9. Explicacion simple de JavaScript

En `ingresar.html` hay un script que se ejecuta cuando el registro esta pendiente.

Este codigo hace una consulta cada 2 segundos:

```javascript
const intervalo = window.setInterval(async () => {
    await consultarEstado();
}, 2000);
```

Eso significa:

Cada 2 segundos, pregunta al servidor si el registro ya fue revisado.

Si el servidor responde que sigue pendiente, no cambia nada.

Si responde que esta incorrecto, muestra el campo incorrecto.

Si responde que esta correcto, muestra un mensaje de validacion correcta.

## 10. Por que se uso SQLite

SQLite se uso porque el proyecto es pequeno y de prueba.

Ventajas:

- Es facil de usar.
- No necesita servidor.
- Guarda datos en un solo archivo.
- Viene incluido con Python.

Para un proyecto grande o en produccion se podria usar:

- PostgreSQL
- MySQL
- SQL Server

Pero para empezar, SQLite es suficiente.

## 11. Posibles mejoras futuras

Algunas mejoras que se podrian hacer despues:

- Crear login para el dashboard.
- Separar usuarios administradores y usuarios normales.
- Agregar busqueda en el dashboard.
- Agregar paginacion en el historial.
- Mejorar la seguridad de los datos.
- Usar variables de entorno para la clave secreta.
- Crear pruebas automaticas.
- Migrar a PostgreSQL si el proyecto crece.

## 12. Resumen final

Este proyecto sirve para aprender conceptos basicos de desarrollo web:

- Rutas en Flask.
- Formularios HTML.
- Guardar datos en SQLite.
- Mostrar datos en tablas.
- Actualizar registros.
- Usar JavaScript para consultar informacion sin recargar manualmente.

Es una buena base para entender como se conecta un frontend con un backend y una base de datos.

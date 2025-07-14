from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import bcrypt
from datetime import datetime
import jwt
from functools import wraps
from flask import request, jsonify
import jwt
from bson import ObjectId
from datetime import datetime, timedelta
import csv
from io import StringIO
from flask import Response

from flask import Flask, request, jsonify

from flask import Flask, request, jsonify, render_template


load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

from flask import redirect, url_for

@app.route("/")
def home():
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_estudiante():
    return render_template("dashboard_estudiante.html")




@app.route("/rutina", methods=["GET"])
def rutina_page():
    return render_template("rutina.html")

@app.route("/nutricion", methods=["GET"])
def nutricion_page():
    return render_template("registro_comida.html")

@app.route("/progreso", methods=["GET"])
def progreso_page():
    return render_template("progreso.html")

# Endpoint de registro de usuarios
@app.route("/registro", methods=["POST"])
def registro():
    data = request.get_json()

    # Validar campos requeridos
    campos_requeridos = ["nombre", "email", "password", "codigo_universitario", "sexo", "edad", "rol", "carrera"]
    if not all(campo in data for campo in campos_requeridos):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    # Verificar si el email ya existe
    if mongo.db.usuarios.find_one({"email": data["email"]}):
        return jsonify({"error": "El correo ya está registrado"}), 409

    # Hashear la contraseña
    password_hash = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

    # Crear documento de usuario
    usuario = {
        "nombre": data["nombre"],
        "email": data["email"],
        "password": password_hash.decode("utf-8"),
        "codigo_universitario": data["codigo_universitario"],
        "sexo": data["sexo"],
        "edad": int(data["edad"]),
        "rol": data["rol"],
        "carrera": data["carrera"],
        "fecha_creacion": datetime.utcnow()
    }

    mongo.db.usuarios.insert_one(usuario)
    return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    usuario = mongo.db.usuarios.find_one({"email": data["email"]})

    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not bcrypt.checkpw(data["password"].encode("utf-8"), usuario["password"].encode("utf-8")):
        return jsonify({"error": "Contraseña incorrecta"}), 401

    payload = {
        "id": str(usuario["_id"]),
        "nombre": usuario["nombre"],
        "rol": usuario["rol"]
    }

    token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")

    return jsonify({
        "mensaje": "Login exitoso",
        "token": token,
        "usuario": {
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": usuario["rol"]
        }
    }), 200


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token se envía en el header: Authorization: Bearer <token>
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            return jsonify({"error": "Token faltante"}), 401

        try:
            decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            usuario_id = decoded["id"]
            usuario = mongo.db.usuarios.find_one({"_id": ObjectId(usuario_id)})

            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Añadimos el usuario a kwargs para usarlo en la función protegida
            return f(usuario, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

    return decorated
@app.route("/perfil", methods=["GET"])
@token_required
def perfil(usuario):
    return jsonify({
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "carrera": usuario.get("carrera", "N/A")
    })
def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(usuario, *args, **kwargs):
            if usuario.get("rol") != required_role:
                return jsonify({"error": "Acceso denegado: rol no autorizado"}), 403
            return f(usuario, *args, **kwargs)
        return wrapper
    return decorator
@app.route("/solo_estudiantes", methods=["GET"])
@token_required
@require_role("estudiante")
def solo_estudiantes(usuario):
    return jsonify({"mensaje": f"Bienvenida estudiante {usuario['nombre']}!"})


@app.route("/solo_entrenadores", methods=["GET"])
@token_required
@require_role("entrenador")
def solo_entrenadores(usuario):
    return jsonify({"mensaje": f"Hola entrenador {usuario['nombre']}, aquí va tu panel."})


@app.route("/solo_admin", methods=["GET"])
@token_required
@require_role("admin")
def solo_admin(usuario):
    return jsonify({"mensaje": f"Área de administración para {usuario['nombre']}."})



@app.route("/entrenador/alimentos", methods=["POST"])
@token_required
@require_role("entrenador")
def insertar_alimento(usuario):
    data = request.get_json()

    campos_requeridos = ["nombre", "unidad", "porcion_estandar", "calorias", "macros"]
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({"error": f"Falta el campo requerido: {campo}"}), 400

    nombre = data["nombre"].strip().lower()

    # ❗ Validar si ya existe un alimento con ese nombre
    if mongo.db.alimentos.find_one({"nombre": {"$regex": f"^{nombre}$", "$options": "i"}}):
        return jsonify({"error": "Ya existe un alimento con ese nombre"}), 400

    macros = data["macros"]
    macros_normalizados = {
        "proteina": float(macros.get("proteina", 0)),
        "grasa": float(macros.get("grasa", macros.get("grasas", 0))),
        "carbohidratos": float(macros.get("carbohidratos", macros.get("carbs", 0)))
    }

    alimento = {
        "nombre": nombre,
        "unidad": data["unidad"],
        "porcion_estandar": float(data["porcion_estandar"]),
        "calorias": float(data["calorias"]),
        "macros": macros_normalizados
    }

    if "micros" in data:
        alimento["micros"] = data["micros"]

    mongo.db.alimentos.insert_one(alimento)
    return jsonify({"mensaje": "Alimento insertado correctamente"}), 201





@app.route("/comidas", methods=["POST"])
@token_required
@require_role("estudiante")
def registrar_comida(usuario):
    data = request.get_json()

    alimento_nombre = data.get("alimento")
    porcion = data.get("porcion", 1)
    unidad = data.get("unidad")
    calorias = data.get("calorias")
    macros = data.get("macros")
    micros = data.get("micros", {})

    if not alimento_nombre:
        return jsonify({"error": "El campo 'alimento' es obligatorio"}), 400

    alimento = mongo.db.alimentos.find_one({"nombre": alimento_nombre})

    if alimento:
        # Alimento existe → usamos datos del catálogo
        factor = porcion * (1 / alimento["porcion_estandar"])
        comida = {
            "usuario_email": usuario["email"],
            "fecha": datetime.utcnow() - timedelta(hours=5),
            "alimento": alimento_nombre,
            "porcion": porcion,
            "unidad": alimento["unidad"],
            "calorias": round(alimento["calorias"] * factor, 2),
            "macros": {k: round(v * factor, 2) for k, v in alimento["macros"].items()},
            "micros": {k: round(v * factor, 2) for k, v in alimento.get("micros", {}).items()}
        }
    else:
        # Alimento personalizado (por cada 100g)
        if not (unidad and calorias and macros):
            return jsonify({
                "error": "Alimento no encontrado. Para alimentos personalizados debes incluir: unidad, calorías y macros (por cada 100g)"
            }), 400

        factor = porcion / 100  # Porción en gramos sobre 100g

        comida = {
            "usuario_email": usuario["email"],
            "fecha": datetime.utcnow() - timedelta(hours=5),
            "alimento": alimento_nombre,
            "porcion": porcion,
            "unidad": unidad,
            "calorias": round(calorias * factor, 2),
            "macros": {k: round(v * factor, 2) for k, v in macros.items()},
            "micros": {k: round(v * factor, 2) for k, v in micros.items()}
        }

    mongo.db.comidas.insert_one(comida)

    return jsonify({"mensaje": "Comida registrada exitosamente", "comida": comida}), 201

from datetime import timedelta

@app.route("/comidas", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_comidas(usuario):
    comidas = list(mongo.db.comidas.find(
        {"usuario_email": usuario["email"]}
    ).sort("fecha", -1))

    for comida in comidas:
        comida["_id"] = str(comida["_id"])
        # Ajuste a hora local (UTC-5)
        comida["fecha"] = (comida["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")

    return jsonify(comidas), 200

@app.route("/comidas/<id>", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_comida_por_id(usuario, id):
    comida = mongo.db.comidas.find_one({
        "_id": ObjectId(id),
        "usuario_email": usuario["email"]
    })
    if not comida:
        return jsonify({"error": "Comida no encontrada"}), 404

    comida["_id"] = str(comida["_id"])
    # Ajuste a hora local (UTC-5)
    comida["fecha"] = (comida["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
    return jsonify(comida), 200


@app.route("/comidas/<id>", methods=["PUT"])
@token_required
@require_role("estudiante")
def modificar_comida(usuario, id):
    data = request.get_json()
    nueva_porcion = data.get("porcion")

    if not nueva_porcion:
        return jsonify({"error": "Falta el campo 'porcion'"}), 400

    comida = mongo.db.comidas.find_one({"_id": ObjectId(id), "usuario_email": usuario["email"]})
    if not comida:
        return jsonify({"error": "Comida no encontrada"}), 404

    # Recalcular calorías y macros
    alimento = mongo.db.alimentos.find_one({"nombre": comida["alimento"]})
    factor = nueva_porcion * (1 / alimento["porcion_estandar"])

    nuevos_datos = {
        "porcion": nueva_porcion,
        "calorias": round(alimento["calorias"] * factor, 2),
        "macros": {k: round(v * factor, 2) for k, v in alimento["macros"].items()},
        "micros": {k: round(v * factor, 2) for k, v in alimento.get("micros", {}).items()}
    }

    mongo.db.comidas.update_one(
        {"_id": ObjectId(id)},
        {"$set": nuevos_datos}
    )

    return jsonify({"mensaje": "Comida actualizada"}), 200

@app.route("/comidas/<id>", methods=["DELETE"])
@token_required
@require_role("estudiante")
def eliminar_comida(usuario, id):
    result = mongo.db.comidas.delete_one({"_id": ObjectId(id), "usuario_email": usuario["email"]})
    if result.deleted_count == 0:
        return jsonify({"error": "Comida no encontrada o no autorizada"}), 404

    return jsonify({"mensaje": "Comida eliminada"}), 200
@app.route("/alimentos", methods=["GET"])
@token_required
@require_role("estudiante")
def listar_alimentos(usuario):
    alimentos = list(mongo.db.alimentos.find({}, {"_id": 0}))  # ocultamos el _id
    return jsonify(alimentos), 200



from datetime import datetime, timedelta

@app.route("/calorias", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_calorias(usuario):
    fecha_str = request.args.get("fecha")
    if fecha_str:
        try:
            fecha_inicio = datetime.strptime(fecha_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}), 400
    else:
        # Si no se pasa fecha, usar hoy
        fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    fecha_fin = fecha_inicio + timedelta(days=1)

    comidas = list(mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": fecha_inicio, "$lt": fecha_fin}
    }))

    total_calorias = sum(comida.get("calorias", 0) for comida in comidas)

    return jsonify({
        "fecha": fecha_inicio.strftime("%Y-%m-%d"),
        "total_calorias": round(total_calorias, 2)
    }), 200



@app.route("/comidas/hoy", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_comidas_hoy(usuario):
    # Establecer el inicio y fin del día en hora local (-5 UTC)
    ahora = datetime.utcnow() - timedelta(hours=5)
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = inicio_dia + timedelta(days=1)

    comidas = list(mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": inicio_dia, "$lt": fin_dia}
    }).sort("fecha", -1))

    for comida in comidas:
        comida["_id"] = str(comida["_id"])
        comida["fecha"] = comida["fecha"].strftime("%Y-%m-%d %H:%M")

    return jsonify(comidas), 200



@app.route("/ejercicios", methods=["POST"])
@token_required
@require_role("entrenador")
def crear_ejercicio(usuario):
    data = request.get_json()

    nombre = data.get("nombre", "").strip()
    tipo = data.get("tipo")
    calorias = data.get("calorias_quemadas")

    if not nombre or not tipo or calorias is None:
        return jsonify({"error": "Faltan campos: 'nombre', 'tipo' y/o 'calorias_quemadas'"}), 400

    if tipo not in ["tiempo", "repeticiones"]:
        return jsonify({"error": "El tipo debe ser 'tiempo' o 'repeticiones'"}), 400

    try:
        calorias = float(calorias)
    except (ValueError, TypeError):
        return jsonify({"error": "El campo 'calorias_quemadas' debe ser numérico"}), 400

    if mongo.db.ejercicios.find_one({"nombre": nombre}):
        return jsonify({"error": "El ejercicio ya existe"}), 409

    ejercicio = {
        "nombre": nombre,
        "tipo": tipo,
        "calorias_quemadas": calorias
    }

    mongo.db.ejercicios.insert_one(ejercicio)
    return jsonify({"mensaje": "Ejercicio creado", "ejercicio": ejercicio}), 201

@app.route("/ejercicios", methods=["GET"])
@token_required
@require_role("entrenador")
def listar_ejercicios(usuario):
    ejercicios = list(mongo.db.ejercicios.find())
    for e in ejercicios:
        e["_id"] = str(e["_id"])
    return jsonify(ejercicios), 200

from bson import ObjectId

@app.route("/ejercicios/<id>", methods=["DELETE"])
@token_required
@require_role("entrenador")
def eliminar_ejercicio(usuario, id):
    try:
        result = mongo.db.ejercicios.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Ejercicio no encontrado"}), 404
        return jsonify({"mensaje": "Ejercicio eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": "ID inválido"}), 400



@app.route("/rutinas", methods=["POST"])
@token_required
@require_role("entrenador")
def crear_rutina(usuario):
    data = request.get_json()

    estudiante_email = data.get("estudiante_email")
    nombre_rutina = data.get("nombre")
    descripcion = data.get("descripcion")
    dia = data.get("dia")  # Ej: "lunes"
    ejercicios_input = data.get("ejercicios")

    if not all([estudiante_email, nombre_rutina, descripcion, dia, ejercicios_input]):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    # 🧠 Validar que todos los ejercicios existan
    nombres_ejercicios = [e["nombre"] for e in ejercicios_input]
    ejercicios_db = list(mongo.db.ejercicios.find({"nombre": {"$in": nombres_ejercicios}}))

    if len(ejercicios_db) != len(ejercicios_input):
        nombres_encontrados = [e["nombre"] for e in ejercicios_db]
        faltantes = list(set(nombres_ejercicios) - set(nombres_encontrados))
        return jsonify({"error": f"Ejercicios no encontrados: {', '.join(faltantes)}"}), 400

    ejercicios_final = []
    for ej_input in ejercicios_input:
        nombre = ej_input["nombre"]
        ej_db = next((e for e in ejercicios_db if e["nombre"] == nombre), None)

        if not ej_db:
            return jsonify({"error": f"Ejercicio '{nombre}' no encontrado"}), 400

        tipo = ej_db["tipo"]

        if tipo == "tiempo":
            duracion = ej_input.get("duracion_min")
            if duracion is None or duracion <= 0:
                return jsonify({"error": f"El ejercicio '{nombre}' requiere 'duracion_min' > 0"}), 400

            ejercicios_final.append({
                "nombre": nombre,
                "tipo": tipo,
                "duracion_min": duracion
            })

        elif tipo == "repeticiones":
            series = ej_input.get("series")
            repeticiones = ej_input.get("repeticiones")
            if not all([series, repeticiones]) or series <= 0 or repeticiones <= 0:
                return jsonify({"error": f"El ejercicio '{nombre}' requiere 'series' y 'repeticiones' > 0"}), 400

            ejercicios_final.append({
                "nombre": nombre,
                "tipo": tipo,
                "series": series,
                "repeticiones": repeticiones
            })

        else:
            return jsonify({"error": f"Tipo de ejercicio desconocido para '{nombre}'"}), 400

    # 🚫 Validar que no exista rutina ese día para ese estudiante
    if mongo.db.rutinas.find_one({"estudiante_email": estudiante_email, "dia": dia.lower()}):
        return jsonify({
            "error": f"Ya existe una rutina asignada para {estudiante_email} el día {dia.lower()}"
        }), 409

    rutina = {
        "entrenador_email": usuario["email"],
        "estudiante_email": estudiante_email,
        "nombre": nombre_rutina,
        "descripcion": descripcion,
        "dia": dia.lower(),
        "fecha_asignacion": datetime.utcnow() - timedelta(hours=5),
        "ejercicios": ejercicios_final
    }

    mongo.db.rutinas.insert_one(rutina)

    return jsonify({"mensaje": "Rutina asignada correctamente", "rutina": rutina}), 201





@app.route("/rutinas/<id>", methods=["PUT"])
@token_required
@require_role("entrenador")
def editar_rutina(usuario, id):
    data = request.get_json()

    nombre_rutina = data.get("nombre")
    descripcion = data.get("descripcion")
    dia = data.get("dia")  # Ej: "monday"
    ejercicios = data.get("ejercicios")

    if not all([nombre_rutina, descripcion, dia, ejercicios]):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    # Verificar si la rutina existe y pertenece al entrenador
    rutina = mongo.db.rutinas.find_one({"_id": ObjectId(id)})
    if not rutina:
        return jsonify({"error": "Rutina no encontrada"}), 404
    if rutina["entrenador_email"] != usuario["email"]:
        return jsonify({"error": "No autorizado para modificar esta rutina"}), 403

    # Validar ejercicios existentes y estructura según tipo
    nombres = [e["nombre"] for e in ejercicios]
    existentes = list(mongo.db.ejercicios.find({"nombre": {"$in": nombres}}))
    ejercicios_ref = {e["nombre"]: e for e in existentes}

    for e in ejercicios:
        ref = ejercicios_ref.get(e["nombre"])
        if not ref:
            return jsonify({"error": f"El ejercicio '{e['nombre']}' no está registrado."}), 400
        if ref["tipo"] == "tiempo":
            if "duracion_min" not in e:
                return jsonify({"error": f"Falta 'duracion_min' para el ejercicio '{e['nombre']}' (tipo tiempo)"}), 400
        elif ref["tipo"] == "repeticiones":
            if "series" not in e or "repeticiones" not in e:
                return jsonify({"error": f"Faltan 'series' y/o 'repeticiones' para el ejercicio '{e['nombre']}' (tipo repeticiones)"}), 400

    # Validar que no haya otra rutina del mismo estudiante en el mismo día
    dia = dia.lower()
    conflicto = mongo.db.rutinas.find_one({
        "_id": {"$ne": ObjectId(id)},
        "estudiante_email": rutina["estudiante_email"],
        "dia": dia
    })
    if conflicto:
        return jsonify({"error": f"El estudiante ya tiene otra rutina asignada para el día {dia}"}), 409

    # Actualizar
    mongo.db.rutinas.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "nombre": nombre_rutina,
                "descripcion": descripcion,
                "dia": dia,
                "ejercicios": ejercicios,
                "fecha_asignacion": datetime.utcnow() - timedelta(hours=5)
            }
        }
    )

    return jsonify({"mensaje": "Rutina actualizada correctamente"}), 200


@app.route("/rutinas/<id>", methods=["DELETE"])
@token_required
@require_role("entrenador")
def eliminar_rutina(usuario, id):
    rutina = mongo.db.rutinas.find_one({"_id": ObjectId(id)})

    if not rutina:
        return jsonify({"error": "Rutina no encontrada"}), 404

    if rutina["entrenador_email"] != usuario["email"]:
        return jsonify({"error": "No tienes permiso para eliminar esta rutina"}), 403

    mongo.db.rutinas.delete_one({"_id": ObjectId(id)})
    return jsonify({"mensaje": "Rutina eliminada exitosamente"}), 200


@app.route("/rutina-dia", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_rutina_dia(usuario):
    hoy = (datetime.utcnow() - timedelta(hours=5)).strftime("%A").lower()

    rutina = mongo.db.rutinas.find_one({
        "estudiante_email": usuario["email"],
        "dia": hoy
    })

    if not rutina:
        return jsonify({"mensaje": "No hay rutina asignada para hoy"}), 404

    rutina["_id"] = str(rutina["_id"])
    return jsonify({"rutina": rutina}), 200


@app.route("/rutinas-estudiante", methods=["GET"])
@token_required
@require_role("entrenador")
def obtener_rutinas_estudiante(usuario):
    email = request.args.get("estudiante_email")

    if not email:
        return jsonify({"error": "Debe especificar 'estudiante_email' en la consulta"}), 400

    rutinas = list(mongo.db.rutinas.find({"estudiante_email": email}))

    for r in rutinas:
        r["_id"] = str(r["_id"])
        r["fecha_asignacion"] = r["fecha_asignacion"].isoformat()

    return jsonify({"rutinas": rutinas}), 200


@app.route("/rutina-dia/progreso", methods=["POST"])
@token_required
@require_role("estudiante")
def registrar_progreso_rutina(usuario):
    data = request.get_json()

    hoy = (datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d")

    # Verificar si ya existe progreso para hoy
    progreso_existente = mongo.db.progreso_rutinas.find_one({
        "estudiante_email": usuario["email"],
        "fecha": {"$gte": datetime.strptime(hoy, "%Y-%m-%d")}
    })

    if progreso_existente:
        return jsonify({"error": "Ya se registró progreso para hoy"}), 409

    # Buscar la rutina del día
    dia_semana = (datetime.utcnow() - timedelta(hours=5)).strftime("%A").lower()
    rutina = mongo.db.rutinas.find_one({
        "estudiante_email": usuario["email"],
        "dia": dia_semana
    })

    if not rutina:
        return jsonify({"error": "No hay rutina asignada para hoy"}), 404

    ejercicios_realizados = data.get("ejercicios_realizados", [])
    if not ejercicios_realizados:
        return jsonify({"error": "Debes enviar los ejercicios realizados"}), 400

    total_calorias = 0
    ejercicios_validos = []

    for ej in ejercicios_realizados:
        nombre = ej.get("nombre")
        completado = ej.get("completado", False)

        if not completado:
            continue  # Ignorar ejercicios no completados

        ejercicio_ref = mongo.db.ejercicios.find_one({"nombre": nombre})
        if not ejercicio_ref:
            return jsonify({"error": f"Ejercicio '{nombre}' no está registrado"}), 400

        tipo = ejercicio_ref.get("tipo")
        calorias_por_unidad = ejercicio_ref.get("calorias_quemadas", 0)

        if tipo == "tiempo":
            duracion_min = ej.get("duracion_min")
            if not isinstance(duracion_min, (int, float)) or duracion_min <= 0:
                return jsonify({"error": f"Duración inválida para '{nombre}'"}), 400

            total_calorias += calorias_por_unidad * duracion_min
            ejercicios_validos.append({
                "nombre": nombre,
                "tipo": "tiempo",
                "duracion_min": duracion_min,
                "completado": True
            })

        elif tipo == "repeticiones":
            series = ej.get("series")
            repeticiones = ej.get("repeticiones")
            if not all(isinstance(x, int) and x > 0 for x in [series, repeticiones]):
                return jsonify({"error": f"Series o repeticiones inválidas para '{nombre}'"}), 400

            total_reps = series * repeticiones
            total_calorias += calorias_por_unidad * total_reps
            ejercicios_validos.append({
                "nombre": nombre,
                "tipo": "repeticiones",
                "series": series,
                "repeticiones": repeticiones,
                "completado": True
            })

        else:
            return jsonify({"error": f"Tipo de ejercicio desconocido para '{nombre}'"}), 400

    if not ejercicios_validos:
        return jsonify({"error": "No se registró ningún ejercicio válido"}), 400

    progreso = {
        "estudiante_email": usuario["email"],
        "fecha": datetime.utcnow() - timedelta(hours=5),
        "rutina_id": str(rutina["_id"]),
        "ejercicios_realizados": ejercicios_validos,
        "calorias_quemadas": total_calorias
    }

    mongo.db.progreso_rutinas.insert_one(progreso)

    return jsonify({
        "mensaje": "Progreso registrado exitosamente",
        "calorias_quemadas": total_calorias,
        "progreso": progreso
    }), 201



@app.route("/progreso", methods=["GET"])
@token_required
@require_role("estudiante")
def obtener_progreso_estudiante(usuario):
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")

    filtro_fecha = {}
    if desde_str:
        desde = datetime.strptime(desde_str, "%Y-%m-%d")
        filtro_fecha["$gte"] = desde
    if hasta_str:
        hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
        filtro_fecha["$lt"] = hasta

    query = {"estudiante_email": usuario["email"]}
    if filtro_fecha:
        query["fecha"] = filtro_fecha

    registros = list(mongo.db.progreso_rutinas.find(query).sort("fecha", -1))

    for r in registros:
        r["_id"] = str(r["_id"])
        r["fecha"] = r["fecha"].strftime("%Y-%m-%d")

        # Extra: obtener el nombre de la rutina
        rutina = mongo.db.rutinas.find_one({"_id": ObjectId(r["rutina_id"])})
        r["nombre_rutina"] = rutina["nombre"] if rutina else "Desconocida"

    return jsonify({"progreso": registros}), 200




@app.route("/progreso/calorias-quemadas", methods=["GET"])
@token_required
@require_role("estudiante")
def calorias_quemadas_por_dia(usuario):
    inicio = request.args.get("desde")  # Ej: 2025-07-01
    fin = request.args.get("hasta")      # Ej: 2025-07-13

    try:
        desde = datetime.strptime(inicio, "%Y-%m-%d")
        hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Formato de fecha inválido. Usa YYYY-MM-DD"}), 400

    registros = mongo.db.progreso_rutinas.find({
        "estudiante_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })

    resultado = {}
    total = 0
    for r in registros:
        dia = (r["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d")
        resultado[dia] = resultado.get(dia, 0) + r.get("calorias_quemadas", 0)
        total += r.get("calorias_quemadas", 0)

    return jsonify({"calorias_por_dia": resultado, "total": total}), 200


# Gráfico 2: Cumplimiento de rutina (porcentaje de días con rutina cumplida)
@app.route("/progreso/cumplimiento", methods=["GET"])
@token_required
@require_role("estudiante")
def porcentaje_cumplimiento(usuario):
    inicio = request.args.get("desde")
    fin = request.args.get("hasta")

    try:
        desde = datetime.strptime(inicio, "%Y-%m-%d")
        hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Fechas inválidas"}), 400

    # Buscar días con rutina asignada:
    dias_rutina = set()
    rutinas = mongo.db.rutinas.find({
        "estudiante_email": usuario["email"]
    })
    for r in rutinas:
        # Obtener todos los días entre inicio y fin que coincidan con el día de la rutina
        dia_semana = r.get("dia")
        actual = desde
        while actual < hasta:
            if actual.strftime("%A").lower() == dia_semana:
                dias_rutina.add(actual.strftime("%Y-%m-%d"))
            actual += timedelta(days=1)

    # Buscar progreso
    progreso = mongo.db.progreso_rutinas.find({
        "estudiante_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })
    dias_completados = { (p["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d") for p in progreso }

    total_dias = len(dias_rutina)
    cumplidos = len(dias_rutina & dias_completados)

    return jsonify({
        "dias_con_rutina": total_dias,
        "dias_completados": cumplidos,
        "porcentaje": round((cumplidos / total_dias) * 100, 2) if total_dias > 0 else 0
    }), 200

@app.route("/comidas/calorias", methods=["GET"])
@token_required
@require_role("estudiante")
def calorias_por_dia(usuario):
    inicio = request.args.get("desde")
    fin = request.args.get("hasta")

    try:
        desde = datetime.strptime(inicio, "%Y-%m-%d")
        hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Fechas inválidas"}), 400

    comidas = mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })

    resultado = {}
    total = 0
    for c in comidas:
        dia = (c["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d")
        resultado[dia] = resultado.get(dia, 0) + c.get("calorias", 0)
        total += c.get("calorias", 0)

    return jsonify({"calorias_por_dia": resultado, "total": round(total, 2)}), 200

# 📊 MACROS PROMEDIO POR DÍA
@app.route("/comidas/macros-promedio", methods=["GET"])
@token_required
@require_role("estudiante")
def macros_promedio(usuario):
    inicio = request.args.get("desde")
    fin = request.args.get("hasta")

    try:
        desde = datetime.strptime(inicio, "%Y-%m-%d")
        hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Fechas inválidas"}), 400

    comidas = mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })

    suma_macros = {"proteinas": 0, "grasas": 0, "carbohidratos": 0}
    dias = set()

    for c in comidas:
        macros = c.get("macros", {})
        for k in suma_macros:
            suma_macros[k] += macros.get(k, 0)
        dias.add((c["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d"))

    total_dias = len(dias)
    if total_dias == 0:
        return jsonify({"promedio_macros": suma_macros, "dias": 0}), 200

    promedio = {k: round(v / total_dias, 2) for k, v in suma_macros.items()}
    return jsonify({"promedio_macros": promedio, "dias": total_dias}), 200

# 📊 HISTORIAL DE COMIDAS ENTRE FECHAS
@app.route("/comidas/historial", methods=["GET"])
@token_required
@require_role("estudiante")
def historial_comidas(usuario):
    inicio = request.args.get("desde")
    fin = request.args.get("hasta")

    try:
        desde = datetime.strptime(inicio, "%Y-%m-%d")
        hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Fechas inválidas"}), 400

    comidas = list(mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    }).sort("fecha", -1))

    for c in comidas:
        c["_id"] = str(c["_id"])
        c["fecha"] = (c["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")

    return jsonify({"historial": comidas}), 200

@app.route("/balance-calorico", methods=["GET"])
@token_required
@require_role("estudiante")
def balance_calorico(usuario):
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")

    try:
        desde = datetime.strptime(desde_str, "%Y-%m-%d") if desde_str else datetime.utcnow() - timedelta(days=7)
        hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1) if hasta_str else datetime.utcnow()
    except:
        return jsonify({"error": "Formato de fechas inválido. Usa YYYY-MM-DD"}), 400

    # Inicializar resumen por día
    dia_actual = desde
    resumen = {}

    while dia_actual < hasta:
        fecha_str = dia_actual.strftime("%Y-%m-%d")
        resumen[fecha_str] = {"consumidas": 0, "quemadas": 0, "balance": 0}
        dia_actual += timedelta(days=1)

    # Calorías consumidas
    comidas = mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })
    for comida in comidas:
        fecha = (comida["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d")
        if fecha not in resumen:
            resumen[fecha] = {"consumidas": 0, "quemadas": 0, "balance": 0}
        resumen[fecha]["consumidas"] += comida.get("calorias", 0)

    # Calorías quemadas
    progresos = mongo.db.progreso_rutinas.find({
        "estudiante_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })
    for p in progresos:
        fecha = (p["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d")
        if fecha not in resumen:
            resumen[fecha] = {"consumidas": 0, "quemadas": 0, "balance": 0}
        resumen[fecha]["quemadas"] += p.get("calorias_quemadas", 0)

    # Calcular balances y totales
    total_consumidas = 0
    total_quemadas = 0
    for r in resumen.values():
        r["consumidas"] = round(r["consumidas"], 2)
        r["quemadas"] = round(r["quemadas"], 2)
        r["balance"] = round(r["consumidas"] - r["quemadas"], 2)
        total_consumidas += r["consumidas"]
        total_quemadas += r["quemadas"]

    balance_total = round(total_consumidas - total_quemadas, 2)

    return jsonify({
        "desde": desde.strftime("%Y-%m-%d"),
        "hasta": (hasta - timedelta(days=1)).strftime("%Y-%m-%d"),
        "resumen_diario": resumen,
        "totales": {
            "total_consumidas": round(total_consumidas, 2),
            "total_quemadas": round(total_quemadas, 2),
            "balance_total": balance_total
        }
    }), 200



@app.route("/progreso/cumplimiento-detallado", methods=["GET"])
@token_required
@require_role("estudiante")
def cumplimiento_detallado(usuario):
    hoy = datetime.utcnow() - timedelta(hours=5)
    desde = hoy - timedelta(days=6)  # últimos 7 días incluyendo hoy
    hasta = hoy + timedelta(days=1)

    # Inicializar conteos
    total_dias_con_rutina = 0
    completadas = 0
    incompletas = 0
    no_realizadas = 0

    # Obtener todas las rutinas asignadas al estudiante
    rutinas = list(mongo.db.rutinas.find({
        "estudiante_email": usuario["email"]
    }))

    if not rutinas:
        return jsonify({"mensaje": "No tienes rutinas asignadas"}), 200

    # Indexar rutinas por día de la semana
    rutinas_por_dia = {}
    for r in rutinas:
        dia = r["dia"]  # ejemplo: "monday"
        rutinas_por_dia[dia] = rutinas_por_dia.get(dia, []) + [r]

    actual = desde
    while actual < hasta:
        dia_nombre = actual.strftime("%A").lower()

        if dia_nombre in rutinas_por_dia:
            total_dias_con_rutina += 1

            # Buscar progreso para ese día
            progreso = mongo.db.progreso_rutinas.find_one({
                "estudiante_email": usuario["email"],
                "fecha": {
                    "$gte": datetime.combine(actual.date(), datetime.min.time()),
                    "$lt": datetime.combine(actual.date(), datetime.max.time())
                }
            })

            if progreso:
                rutina_id = progreso.get("rutina_id")
                rutina = mongo.db.rutinas.find_one({"_id": ObjectId(rutina_id)})

                if rutina:
                    total_ejercicios = len(rutina.get("ejercicios", []))
                    completados = [
                        e for e in progreso.get("ejercicios_realizados", [])
                        if e.get("completado") is True
                    ]

                    if len(completados) == total_ejercicios:
                        completadas += 1
                    else:
                        incompletas += 1
                else:
                    incompletas += 1  # rutina no encontrada, se asume incompleta
            else:
                no_realizadas += 1

        actual += timedelta(days=1)

    return jsonify({
        "periodo": {
            "desde": desde.strftime("%Y-%m-%d"),
            "hasta": (hasta - timedelta(days=1)).strftime("%Y-%m-%d")
        },
        "total_dias_con_rutina": total_dias_con_rutina,
        "completas": completadas,
        "incompletas": incompletas,
        "no_realizadas": no_realizadas,
        "porcentaje_completas": round((completadas / total_dias_con_rutina) * 100, 2) if total_dias_con_rutina else 0,
        "porcentaje_incompletas": round((incompletas / total_dias_con_rutina) * 100, 2) if total_dias_con_rutina else 0,
        "porcentaje_no_realizadas": round((no_realizadas / total_dias_con_rutina) * 100, 2) if total_dias_con_rutina else 0,
    }), 200


@app.route("/progreso/cumplimiento-por-dia", methods=["GET"])
@token_required
@require_role("estudiante")
def cumplimiento_ultimos_7_dias(usuario):
    hoy = datetime.utcnow() - timedelta(hours=5)  # Ajuste horario Perú
    resultados = {}

    # Obtener rutinas del estudiante
    rutinas = list(mongo.db.rutinas.find({"estudiante_email": usuario["email"]}))
    if not rutinas:
        return jsonify({"mensaje": "No tienes rutinas asignadas"}), 200

    # Agrupar rutinas por día (ej. "monday", "tuesday")
    rutinas_por_dia = {}
    for r in rutinas:
        dia = r["dia"].lower()
        rutinas_por_dia.setdefault(dia, []).append(r)

    for i in range(6, -1, -1):  # últimos 7 días desde hoy hacia atrás
        fecha_actual = hoy - timedelta(days=i)
        dia_nombre = fecha_actual.strftime("%A").lower()  # ejemplo: "sunday"
        fecha_str = fecha_actual.strftime("%Y-%m-%d")
        dia_esp = fecha_actual.strftime("%A")  # para mostrar en frontend (domingo, lunes...)

        porcentaje = None  # valor por defecto si no hay rutina ese día

        if dia_nombre in rutinas_por_dia:
            ejercicios_esperados = []
            for rutina in rutinas_por_dia[dia_nombre]:
                ejercicios_esperados.extend(rutina["ejercicios"])

            total = len(ejercicios_esperados)

            progreso = mongo.db.progreso_rutinas.find_one({
                "estudiante_email": usuario["email"],
                "fecha": {
                    "$gte": datetime.combine(fecha_actual.date(), datetime.min.time()),
                    "$lt": datetime.combine(fecha_actual.date(), datetime.max.time())
                }
            })

            if progreso:
                completados = progreso.get("ejercicios_realizados", [])
                completados_count = sum(1 for e in completados if e.get("completado") is True)
                porcentaje = round((completados_count / total) * 100, 2) if total > 0 else 0
            else:
                porcentaje = 0.0  # había rutina pero no se hizo

        resultados[fecha_str] = {
            "dia": dia_esp.lower(),  # nombre del día en español si lo localizas
            "porcentaje": porcentaje
        }

    return jsonify(resultados), 200
@app.route("/resumen/macros", methods=["GET"])
@token_required
@require_role("estudiante")
def resumen_macros(usuario):
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")

    try:
        desde = datetime.strptime(desde_str, "%Y-%m-%d")
        hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
    except:
        return jsonify({"error": "Fechas inválidas. Usa formato YYYY-MM-DD"}), 400

    comidas = mongo.db.comidas.find({
        "usuario_email": usuario["email"],
        "fecha": {"$gte": desde, "$lt": hasta}
    })

    resumen_diario = {}
    total_proteinas = total_carbs = total_grasas = 0

    for c in comidas:
        fecha = (c["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d")
        macros = c.get("macros", {})
        prot = macros.get("proteinas", 0)
        carb = macros.get("carbohidratos", 0)
        gras = macros.get("grasas", 0)

        if fecha not in resumen_diario:
            resumen_diario[fecha] = {"proteinas": 0, "carbohidratos": 0, "grasas": 0}

        resumen_diario[fecha]["proteinas"] += prot
        resumen_diario[fecha]["carbohidratos"] += carb
        resumen_diario[fecha]["grasas"] += gras

        total_proteinas += prot
        total_carbs += carb
        total_grasas += gras

    return jsonify({
        "desde": desde_str,
        "hasta": hasta_str,
        "macros_por_dia": resumen_diario,
        "totales": {
            "proteinas": round(total_proteinas, 2),
            "carbohidratos": round(total_carbs, 2),
            "grasas": round(total_grasas, 2)
        }
    }), 200



@app.route("/admin/usuarios", methods=["GET"])
@token_required
@require_role("admin")
def listar_usuarios(usuario):
    rol = request.args.get("rol")  # opcional: ?rol=estudiante o ?rol=entrenador
    filtro = {"rol": rol} if rol else {}

    usuarios = list(mongo.db.usuarios.find(filtro, {"password": 0}))  # no mostrar hash
    for u in usuarios:
        u["_id"] = str(u["_id"])
        u["fecha_creacion"] = u["fecha_creacion"].strftime("%Y-%m-%d")

    return jsonify({"usuarios": usuarios}), 200

@app.route("/admin/usuarios/<id>", methods=["GET"])
@token_required
@require_role("admin")
def obtener_usuario(usuario, id):
    u = mongo.db.usuarios.find_one({"_id": ObjectId(id)}, {"password": 0})
    if not u:
        return jsonify({"error": "Usuario no encontrado"}), 404

    u["_id"] = str(u["_id"])
    u["fecha_creacion"] = u["fecha_creacion"].strftime("%Y-%m-%d")
    return jsonify(u), 200

@app.route("/admin/usuarios/<id>", methods=["PUT"])
@token_required
@require_role("admin")
def actualizar_usuario(usuario, id):
    data = request.get_json()
    campos_actualizables = ["nombre", "email", "codigo_universitario", "sexo", "edad", "rol", "carrera"]
    cambios = {campo: data[campo] for campo in campos_actualizables if campo in data}

    if not cambios:
        return jsonify({"error": "No se enviaron campos para actualizar"}), 400

    result = mongo.db.usuarios.update_one({"_id": ObjectId(id)}, {"$set": cambios})
    if result.matched_count == 0:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200


@app.route("/admin/usuarios/<id>", methods=["DELETE"])
@token_required
@require_role("admin")
def eliminar_usuario(usuario, id):
    # No permitir que un admin se elimine a sí mismo
    if id == str(usuario["_id"]):
        return jsonify({"error": "No puedes eliminarte a ti mismo"}), 403

    result = mongo.db.usuarios.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200

@app.route("/admin/exportar/usuarios", methods=["GET"])
@token_required
@require_role("admin")
def exportar_usuarios(usuario):
    rol = request.args.get("rol")  # estudiante, entrenador, admin

    query = {}
    if rol:
        query["rol"] = rol

    usuarios = mongo.db.usuarios.find(query)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Email", "Rol", "Código", "Sexo", "Edad", "Carrera", "Fecha Creación"])

    for u in usuarios:
        writer.writerow([
            u.get("nombre"),
            u.get("email"),
            u.get("rol"),
            u.get("codigo_universitario"),
            u.get("sexo"),
            u.get("edad"),
            u.get("carrera"),
            u.get("fecha_creacion").strftime("%Y-%m-%d %H:%M") if u.get("fecha_creacion") else ""
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=usuarios.csv"})

@app.route("/admin/exportar/comidas", methods=["GET"])
@token_required
@require_role("admin")
def exportar_comidas(usuario):
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")

    query = {}
    if desde_str and hasta_str:
        try:
            desde = datetime.strptime(desde_str, "%Y-%m-%d")
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
            query["fecha"] = {"$gte": desde, "$lt": hasta}
        except:
            return jsonify({"error": "Fechas inválidas"}), 400

    comidas = mongo.db.comidas.find(query)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Fecha", "Alimento", "Porción", "Unidad", "Calorías", "Proteínas", "Grasas", "Carbohidratos"])

    for c in comidas:
        macros = c.get("macros", {})
        writer.writerow([
            c.get("usuario_email"),
            (c["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            c.get("alimento"),
            c.get("porcion"),
            c.get("unidad"),
            c.get("calorias"),
            macros.get("proteinas", 0),
            macros.get("grasas", 0),
            macros.get("carbohidratos", 0),
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=comidas.csv"})

@app.route("/admin/exportar/progreso", methods=["GET"])
@token_required
@require_role("admin")
def exportar_progreso(usuario):
    desde_str = request.args.get("desde")
    hasta_str = request.args.get("hasta")
    email = request.args.get("email")

    query = {}
    if desde_str and hasta_str:
        try:
            desde = datetime.strptime(desde_str, "%Y-%m-%d")
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
            query["fecha"] = {"$gte": desde, "$lt": hasta}
        except:
            return jsonify({"error": "Fechas inválidas"}), 400

    if email:
        query["estudiante_email"] = email

    progresos = mongo.db.progreso_rutinas.find(query)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Email", "Fecha", "Rutina ID", "Ejercicios Realizados", "Calorías Quemadas"])

    for p in progresos:
        ejercicios = "; ".join(
            [f"{e.get('nombre')} ({e.get('duracion_min')} min)" for e in p.get("ejercicios_realizados", [])]
        )
        writer.writerow([
            p.get("estudiante_email"),
            (p["fecha"] - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            p.get("rutina_id"),
            ejercicios,
            p.get("calorias_quemadas", 0)
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=progreso.csv"})
@app.route("/admin/exportar/rutinas", methods=["GET"])
@token_required
@require_role("admin")
def exportar_rutinas(usuario):
    email = request.args.get("email")

    query = {}
    if email:
        query["estudiante_email"] = email

    rutinas = mongo.db.rutinas.find(query)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre Rutina", "Estudiante Email", "Entrenador", "Día", "Descripción", "Ejercicios"])

    for r in rutinas:
        ejercicios = "; ".join([e.get("nombre", "") for e in r.get("ejercicios", [])])
        writer.writerow([
            r.get("nombre"),
            r.get("estudiante_email"),
            r.get("entrenador_email"),
            r.get("dia"),
            r.get("descripcion"),
            ejercicios
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=rutinas.csv"})

@app.route("/admin/exportar/alimentos", methods=["GET"])
@token_required
@require_role("admin")
def exportar_alimentos(usuario):
    alimentos = mongo.db.alimentos.find()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Unidad", "Porción Estándar", "Calorías", "Proteínas", "Grasas", "Carbohidratos"])

    for a in alimentos:
        macros = a.get("macros", {})
        writer.writerow([
            a.get("nombre"),
            a.get("unidad"),
            a.get("porcion_estandar"),
            a.get("calorias"),
            macros.get("proteinas", 0),
            macros.get("grasas", 0),
            macros.get("carbohidratos", 0),
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=alimentos.csv"})


@app.route("/entrenador_alimentos", methods=["GET"])
@token_required
@require_role("entrenador")
def listar_alimentos_entrenador(usuario):
    alimentos = list(mongo.db.alimentos.find())
    for a in alimentos:
        a["_id"] = str(a["_id"])  # Para que sea serializable en JSON
    return jsonify(alimentos), 200



@app.route("/entrenador_alimentos/<id>", methods=["DELETE"])
@token_required
@require_role("entrenador")
def eliminar_alimento(usuario, id):
    result = mongo.db.alimentos.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Alimento no encontrado"}), 404
    return jsonify({"mensaje": "Alimento eliminado correctamente"}), 200

@app.route("/entrenador_estudiantes", methods=["GET"])
@token_required
@require_role("entrenador")
def listar_estudiantes(usuario):
    filtro = {"rol": "estudiante"}

    nombre = request.args.get("nombre")
    carrera = request.args.get("carrera")

    if nombre:
        filtro["nombre"] = {"$regex": nombre, "$options": "i"}  # búsqueda parcial, sin distinguir mayúsculas
    if carrera:
        filtro["carrera"] = {"$regex": carrera, "$options": "i"}

    estudiantes = list(mongo.db.usuarios.find(filtro))

    for est in estudiantes:
        est["_id"] = str(est["_id"])
        est["fecha_creacion"] = est.get("fecha_creacion", "").isoformat() if "fecha_creacion" in est else None

    return jsonify(estudiantes), 200



@app.route("/entrenador")
def dashboard_entrenador():
    return render_template("entrenador_dashboard.html")


@app.route("/entrenador/alimentos")

def vista_alimentos():
    return render_template("entrenador_alimentos.html")

@app.route("/entrenador/estudiantes")
def vista_estudiantes():
    return render_template("entrenador_estudiantes.html")

@app.route("/entrenador/ejercicios")
def vista_ejercicios():
    return render_template("entrenador_ejercicios.html")

@app.route("/entrenador/rutinas")
def vista_rutinas():
    return render_template("entrenador_rutinas.html")


@app.route("/dashboard-admin")
def dashboard_admin():
    return render_template("admin_dashboard.html")

@app.route("/admin/registro")
def registro_admin():
    return render_template("admin_registro.html")




if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
import sqlite3
import qrcode
import time
import uuid
import paho.mqtt.client as mqtt
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Configuración de MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "vending/qrs"

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)

# Función para crear la base de datos SQLite
def crear_db():
    conn = sqlite3.connect("codigos.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS codigos (
            pedido_id TEXT PRIMARY KEY, 
            expiracion INTEGER, 
            qr_url TEXT
        )
    """)
    conn.commit()
    conn.close()

crear_db()

# Ruta para generar un QR
@app.route("/generar_qr", methods=["POST"])
def generar_qr():
    # Generar un ID único para el pedido
    pedido_id = f"PEDIDO-{uuid.uuid4().hex[:8]}"
    expiracion = int(time.time()) + 600  # Expira en 10 minutos

    # Crear el enlace que estará dentro del QR
    datos_qr = f"https://tuservidor.com/validar?pedido={pedido_id}&exp={expiracion}"

    # Generar la imagen QR
    qr = qrcode.make(datos_qr)
    nombre_archivo = f"static/{pedido_id}.png"
    qr.save(nombre_archivo)

    # Guardar en la base de datos (máximo 100 registros)
    conn = sqlite3.connect("codigos.db")
    c = conn.cursor()
    c.execute("INSERT INTO codigos VALUES (?, ?, ?)", (pedido_id, expiracion, nombre_archivo))
    conn.commit()
    conn.close()

    # Publicar en MQTT
    mqtt_client.publish(MQTT_TOPIC, f"{pedido_id},{expiracion},{nombre_archivo}")

    return jsonify({"pedido_id": pedido_id, "expiracion": expiracion, "qr_url": nombre_archivo})

# Ruta para enviar QR por correo
@app.route("/enviar_email", methods=["POST"])
def enviar_email():
    datos = request.json
    destinatario = datos["email"]
    qr_url = datos["qr_url"]

    remitente = "tuemail@gmail.com"
    mensaje = EmailMessage()
    mensaje["Subject"] = "Tu código QR"
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.set_content(f"Escanea este QR: {qr_url}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(remitente, "tucontraseña")
        servidor.send_message(mensaje)

    return jsonify({"status": "QR enviado por email"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

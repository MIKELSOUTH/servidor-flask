from flask import Flask, jsonify, request
import qrcode
import os
import time

app = Flask(__name__)

@app.route('/')
def index():
    return "Servidor Flask en funcionamiento"

@app.route('/generar_qr', methods=['POST'])
def generar_qr():
    try:
        # Obtener los datos del cuerpo de la solicitud
        data = request.get_json()

        # Verificar que los datos necesarios estén presentes
        if 'pedido_id' not in data or 'expiracion' not in data:
            return jsonify({'error': 'Faltan parámetros en la solicitud'}), 400

        pedido_id = data['pedido_id']
        expiracion = data['expiracion']

        # Crear el contenido del QR
        qr_content = f"{pedido_id},{expiracion}"

        # Generar el código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Crear la imagen del QR
        img = qr.make_image(fill='black', back_color='white')

        # Crear un nombre único para el archivo QR
        qr_filename = f"{pedido_id}.png"

        # Guardar el archivo en la carpeta 'static'
        img_path = os.path.join('static', qr_filename)
        img.save(img_path)

        # Calcular la fecha de expiración en formato UNIX (timestamp)
        expiration_time = time.time() + expiracion

        # Devolver la respuesta con el enlace al QR y la expiración
        return jsonify({
            'pedido_id': pedido_id,
            'expiracion': expiration_time,
            'qr_url': img_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)

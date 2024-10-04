import mysql.connector
import base64
import os
from flask import Flask, request, jsonify, Response
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'ssl_ca': os.getenv('DB_SSL_CA')
}

def check_auth(auth_header):
    if not auth_header:
        return False

    try:
        auth_type, encoded_credentials = auth_header.split(' ')
        if auth_type != 'Basic':
            return False
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':')
        return username == 'fluvial' and password == 'berick'
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    auth_header = request.headers.get('Authorization')
    if not check_auth(auth_header):
        return Response('Unauthorized', status=401, headers={'WWW-Authenticate': 'Basic realm="Login required"'})

    data = request.json
    turbpo = data.get('turbpo')
    temppo = data.get('temppo')
    PPM = data.get('PPM')

    current_time = datetime.now(timezone.utc) - timedelta(hours=3)

    if insert_data_to_db(turbpo, temppo, PPM, current_time):
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error'}), 500

def insert_data_to_db(turbpo, temppo, PPM, timestamp):
    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            ssl_ca=db_config['ssl_ca'],
            ssl_disabled=False
        )

        cursor = conn.cursor()

        query = "INSERT INTO Fluvial (turbpo, temppo, PPM, data) VALUES (%s, %s, %s, %s)"
        values = (turbpo, temppo, PPM, timestamp)

        cursor.execute(query, values)
        conn.commit()

        return True

    except mysql.connector.Error as err:
        print(f"Erro: {err}")
        return False

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(port=5000)

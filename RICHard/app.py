from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import mysql.connector
from mysql.connector import Error
from sentinel_downloader import get_sentinel_quicklook
from io import BytesIO
import requests
from datetime import datetime
import logging

app = Flask(__name__)
app.secret_key = 'tajny_klucz'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja połączenia z MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Pr@ktyk@nt1',
    'database': 'users'
}

def get_db_connection():
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except Error as e:
        logger.error(f"Błąd połączenia z bazą danych: {e}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        logger.error(f"Błąd inicjalizacji bazy danych: {e}")

@app.route('/')
def home():
    username = session.get('username')
    return render_template('home.html', username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 6:
            flash("Hasło musi mieć co najmniej 6 znaków.", "error")
            return redirect(url_for('register'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Rejestracja zakończona sukcesem! Możesz się zalogować.', 'success')
            return redirect(url_for('login', username=username))
        except mysql.connector.IntegrityError:
            flash("Nazwa użytkownika jest już zajęta.", "error")
            return redirect(url_for('register'))
        except Error as e:
            flash(f"Błąd bazy danych: {e}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row and row[0] == password:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                flash("Nieprawidłowa nazwa użytkownika lub hasło.", "error")
                return redirect(url_for('login'))
        except Error as e:
            flash(f"Błąd bazy danych: {e}", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Zostałeś wylogowany.", "success")
    return redirect(url_for('login'))

@app.route('/map')
def map():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('map.html', username=session.get('username'))

@app.route("/download_image", methods=["POST"])
def download_image():
    if 'username' not in session:
        return jsonify({"error": "Wymagane logowanie"}), 401

    try:
        data = request.get_json()
        if not data or 'corners' not in data:
            logger.error("Brak wymaganych danych w żądaniu")
            return jsonify({"error": "Brak wymaganych parametrów"}), 400

        satellite = data.get("satellite", "sentinel1")
        logger.info(f"Próba pobrania obrazu satelitarnego: {satellite}")

        result = get_sentinel_quicklook(data['corners'], satellite)
        if not result:
            logger.warning("Nie znaleziono obrazu dla podanych parametrów")
            return jsonify({"error": "Nie znaleziono obrazu satelitarnego"}), 404

        # Pobierz obraz z nagłówkiem Accept
        headers = {"Accept": "image/jpeg"}
        img_response = requests.get(
            result["quicklook_url"],
            headers=headers,
            stream=True,
            timeout=30
        )
        img_response.raise_for_status()

        # Zapisz do pamięci zamiast na dysk
        img_bytes = BytesIO(img_response.content)
        
        # Generuj nazwę pliku z datą
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result['title']}_{timestamp}.jpg"

        return send_file(
            img_bytes,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=filename
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd pobierania obrazu: {str(e)}")
        return jsonify({"error": f"Błąd pobierania obrazu: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd: {str(e)}")
        return jsonify({"error": f"Wewnętrzny błąd serwera: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
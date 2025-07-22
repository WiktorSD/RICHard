from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'tajny_klucz'

# Konfiguracja połączenia z MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',      # <- zmień na swojego użytkownika MySQL
    'password': 'Pr@ktyk@nt1',      # <- zmień na swoje hasło MySQL
    'database': 'users'        # <- zmień na swoją bazę danych MySQL
}

def get_db_connection():
    return mysql.connector.connect(**MYSQL_CONFIG)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Usuń poniższą linię, aby nie usuwać tabeli przy każdym starcie
        # cursor.execute('DROP TABLE IF EXISTS users')
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
        print(f"Błąd połączenia z bazą danych: {e}")

@app.route('/')
def home():
    username = None
    if 'username' in session:
        username = session['username']
    return render_template('home.html', username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 6:
            flash("Hasło musi mieć co najmniej 6 znaków.", "error")
            return redirect(url_for('register'))

        # hashed_password = generate_password_hash(password)
        # Zapisz hasło wprost (niezalecane w produkcji!)
        plain_password = password

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, plain_password))
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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        # Porównaj hasło wprost
        if row and row[0] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash("Nieprawidłowa nazwa użytkownika lub hasło.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Zostałeś wylogowany.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

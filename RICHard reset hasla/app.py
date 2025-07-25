from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'tajnyklucz'

DATABASE = 'database.db'
EMAIL_ADDRESS = 'richardsentinel12@gmail.com'
EMAIL_PASSWORD = 'TWOJE_HASLO_APP_GMAIL'  # <- Wstaw tutaj swoje hasło aplikacji Gmail

s = URLSafeTimedSerializer(app.secret_key)

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ====================
# STRONA GŁÓWNA
# ====================
@app.route('/')
def home():
    username = session.get('username')
    return render_template('home.html', username=username)

# ====================
# LOGOWANIE
# ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            flash('Zalogowano pomyślnie.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')

    return render_template('login.html')

# ====================
# WYLOGOWANIE
# ====================
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Wylogowano.', 'success')
    return redirect(url_for('login'))

# ====================
# RESET HASŁA - KROK 1
# ====================
@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user:
            token = s.dumps(email, salt='reset-password')
            reset_url = url_for('reset_token', token=token, _external=True)
            body = f'Kliknij, aby zresetować hasło: {reset_url}'

            msg = MIMEText(body)
            msg['Subject'] = 'Resetowanie hasła'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.send_message(msg)
                return render_template('message_sent.html')
            except Exception as e:
                return f'Błąd wysyłania e-maila: {e}'
        else:
            flash('Nie znaleziono użytkownika.', 'danger')
    return render_template('reset_request.html')

# ====================
# RESET HASŁA - KROK 2
# ====================
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)
    except:
        return 'Link wygasł lub jest nieprawidłowy.'

    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash('Hasła się nie zgadzają!', 'danger')
            return redirect(request.url)
        hashed = generate_password_hash(password)
        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed, email))
        conn.commit()
        conn.close()
        return 'Hasło zostało zmienione!'
    return render_template('reset_token.html')

@app.route('/map')
def map():
    return render_template('map.html')

# ====================
# START SERWERA
# ====================
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template_string
import jwt
import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'userdb')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
APP_TITLE = os.environ.get('APP_TITLE', 'Система управления пользователями')
WELCOME_MESSAGE = os.environ.get('WELCOME_MESSAGE', 'Добро пожаловать в систему')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ==================== СТРАНИЦА ВХОДА ====================
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Вход - {{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 400px;
            margin: 50px auto;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            width: 100%;
        }
        button:disabled {
            background-color: #ccc;
        }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    <form id="loginForm">
        <input type="text" id="username" placeholder="Логин" required>
        <input type="password" id="password" placeholder="Пароль" required>
        <button type="submit" id="loginBtn">Войти</button>
    </form>
    <div id="result"></div>
    <script>
        localStorage.removeItem('token');
        
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('loginBtn');
            btn.disabled = true;
            btn.textContent = 'Вход...';
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                const data = await response.json();
                
                if (response.ok) {
                    localStorage.setItem('token', data.token);
                    window.location.href = '/home';
                } else {
                    document.getElementById('result').innerHTML = 
                        '<p class="error">' + data.error + '</p>';
                }
            } catch (err) {
                document.getElementById('result').innerHTML = 
                    '<p class="error">Ошибка соединения</p>';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Войти';
            }
        });
    </script>
</body>
</html>
'''

# ==================== ГЛАВНАЯ СТРАНИЦА ====================
HOME_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Главная - {{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .menu {
            background: #f0f0f0;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .menu a {
            margin-right: 20px;
            color: #4CAF50;
            text-decoration: none;
            font-weight: bold;
        }
        .menu a:hover { text-decoration: underline; }
        .logout { color: red; cursor: pointer; }
        .content {
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }
        .info-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="menu">
        <a href="/home">Главная</a>
        <a href="/profile">Профиль</a>
        <span class="logout" onclick="logout()">Выйти</span>
    </div>
    
    <div class="content">
        <h1>{{ title }}</h1>
        <p>{{ message }}</p>
        
        <div class="info-card">
            <h3>Информация о системе</h3>
            <p><strong>Система:</strong> Система управления пользователями v1.0</p>
            <p><strong>Статус:</strong> <span style="color: green">Онлайн</span></p>
            <p><strong>Сервисы:</strong> Авторизация, Профили, Уведомления</p>
            <p><strong>База данных:</strong> PostgreSQL (StatefulSet)</p>
        </div>
        
        <div class="info-card">
            <h3>Доступные функции</h3>
            <ul>
                <li><strong>Вход/Выход</strong> — аутентификация через JWT</li>
                <li><strong>Профиль пользователя</strong> — просмотр данных учётной записи</li>
                <li><strong>Уведомления</strong> — получение системных уведомлений</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h3>Вы вошли как: <span id="username">...</span></h3>
        </div>
    </div>
    
    <script>
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/';
        }
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            document.getElementById('username').textContent = payload.username;
        } catch(e) {
            document.getElementById('username').textContent = 'Неизвестно';
        }
        
        function logout() {
            localStorage.removeItem('token');
            window.location.href = '/';
        }
    </script>
</body>
</html>
'''

# ==================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ====================
PROFILE_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Профиль - {{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .menu {
            background: #f0f0f0;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .menu a {
            margin-right: 20px;
            color: #4CAF50;
            text-decoration: none;
            font-weight: bold;
        }
        .menu a:hover { text-decoration: underline; }
        .logout { color: red; cursor: pointer; }
        .profile-data {
            background: #fafafa;
            padding: 20px;
            border-radius: 5px;
        }
        .profile-data p {
            font-size: 16px;
            margin: 10px 0;
        }
        .label {
            font-weight: bold;
            color: #555;
        }
    </style>
</head>
<body>
    <div class="menu">
        <a href="/home">Главная</a>
        <a href="/profile">Профиль</a>
        <span class="logout" onclick="logout()">Выйти</span>
    </div>
    
    <h1>Профиль пользователя</h1>
    <div class="profile-data" id="profile">Загрузка...</div>
    
    <script>
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/';
        }
        
        fetch('/api/profile', {
            headers: {'Authorization': 'Bearer ' + token}
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                document.getElementById('profile').innerHTML = 
                    '<p style="color: red">' + data.error + '</p>';
            } else {
                document.getElementById('profile').innerHTML = 
                    '<p><span class="label">ID:</span> ' + data.id + '</p>' +
                    '<p><span class="label">Логин:</span> ' + data.username + '</p>' +
                    '<p><span class="label">Email:</span> ' + data.email + '</p>' +
                    '<p><span class="label">Создан:</span> ' + data.created_at + '</p>';
            }
        })
        .catch(err => {
            document.getElementById('profile').innerHTML = 
                '<p style="color: red">Ошибка загрузки профиля</p>';
        });
        
        function logout() {
            localStorage.removeItem('token');
            window.location.href = '/';
        }
    </script>
</body>
</html>
'''

# ==================== МАРШРУТЫ ====================

@app.route('/')
def login_page():
    return render_template_string(LOGIN_PAGE, title=APP_TITLE, message=WELCOME_MESSAGE)

@app.route('/home')
def home_page():
    return render_template_string(HOME_PAGE, title=APP_TITLE, message=WELCOME_MESSAGE)

@app.route('/profile')
def profile_page():
    return render_template_string(PROFILE_PAGE, title=APP_TITLE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

@app.route('/ready')
def ready():
    try:
        get_db_connection()
        return jsonify({'status': 'ready'}), 200
    except:
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # В БД пароль в plain text (для простоты)
    cur.execute("SELECT id, username, email, created_at FROM users WHERE username = %s AND password = %s", 
                (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Неверный логин или пароль'}), 401

@app.route('/api/profile', methods=['GET'])
def profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Token missing'}), 401
    
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return jsonify(user)
        return jsonify({'error': 'User not found'}), 404
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

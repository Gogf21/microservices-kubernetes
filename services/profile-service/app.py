from flask import Flask, request, jsonify, render_template_string
import jwt
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
DB_HOST = os.environ.get('DB_HOST', 'postgres-db')
DB_NAME = os.environ.get('DB_NAME', 'userdb')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
APP_TITLE = os.environ.get('PROFILE_TITLE', 'Профиль пользователя')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

PROFILE_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Профиль - {{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
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
        .logout { color: red; cursor: pointer; }
        .profile-data {
            background: #fafafa;
            padding: 20px;
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
    
    <h1>{{ title }}</h1>
    <div class="profile-data" id="profile">Загрузка...</div>
    
    <script>
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/';
        }
        
        fetch('/api/profile', {
            headers: {'Authorization': 'Bearer ' + token}
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('profile').innerHTML = 
                    '<p style="color: red">' + data.error + '</p>';
            } else {
                document.getElementById('profile').innerHTML = 
                    '<p><strong>ID:</strong> ' + data.id + '</p>' +
                    '<p><strong>Логин:</strong> ' + data.username + '</p>' +
                    '<p><strong>Email:</strong> ' + data.email + '</p>' +
                    '<p><strong>Создан:</strong> ' + data.created_at + '</p>';
            }
        })
        .catch(() => {
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

@app.route('/')
@app.route('/profile')
def profile_page():
    return render_template_string(PROFILE_PAGE, title=APP_TITLE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'profile-service'}), 200

@app.route('/ready')
def ready():
    try:
        get_db_connection()
        return jsonify({'status': 'ready'}), 200
    except:
        return jsonify({'status': 'not ready'}), 503

@app.route('/api/profile', methods=['GET'])
def get_profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Token missing'}), 401
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['user_id']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, username, email, created_at FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return jsonify(dict(user))
        else:
            return jsonify({'error': 'Пользователь не найден'}), 404
            
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Срок действия токена истёк'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Недействительный токен'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

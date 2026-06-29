from flask import Flask, request, jsonify
import os
import datetime

app = Flask(__name__)

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'notification-service'}), 200

@app.route('/ready')
def ready():
    return jsonify({'status': 'ready'}), 200

@app.route('/api/notify', methods=['POST'])
def send_notification():
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if LOG_LEVEL == 'DEBUG':
        msg = f"DEBUG: Отправка уведомления пользователю {user_id}: {message}"
    else:
        msg = f"INFO: Уведомление отправлено пользователю {user_id}: {message}"
    
    print(msg, flush=True)
    
    # Запись в emptyDir (кэш)
    try:
        with open('/cache/notifications.log', 'a') as f:
            f.write(f"{datetime.datetime.now().isoformat()} | {msg}\n")
    except:
        pass
    
    return jsonify({
        'status': 'sent',
        'timestamp': datetime.datetime.now().isoformat(),
        'user_id': user_id,
        'message': message
    })

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        with open('/cache/notifications.log', 'r') as f:
            lines = f.readlines()
        return jsonify({'notifications': lines[-10:]})
    except:
        return jsonify({'notifications': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

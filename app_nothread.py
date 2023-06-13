from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected'})
    emit('thread_list', {'threads': []}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    emit('message', {'username': data['username'], 'message': data['message']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
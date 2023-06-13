from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import threading

app = Flask(__name__)
CORS(app)
# app.config['SECRET_KEY'] = 'secret_key'
# socketio = SocketIO(app, transports=['websocket'])
socketio = SocketIO(app, transports=['websocket'])

threads = {}
thread_count = 0
thread_count_lock = threading.Lock()

class ChatThread(threading.Thread):
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.exit_flag = threading.Event()

    def run(self):
        with thread_count_lock:
            global thread_count
            thread_count += 1
            print(f"Thread {self.client_id} started. Total threads: {thread_count}")

        while not self.exit_flag.is_set():
            socketio.sleep(1)

        with thread_count_lock:
            thread_count -= 1
            print(f"Thread {self.client_id} terminated. Total threads: {thread_count}")

    def get_user_threads(self):
        with thread_count_lock:
            user_threads = [thread for thread in threading.enumerate() if isinstance(thread, ChatThread) and thread.client_id == self.client_id]
            return user_threads

def get_active_threads():
    with thread_count_lock:
        active_thread_ids = [str(thread.ident) for thread in threads.values() if thread.is_alive()]
        return active_thread_ids

@socketio.on('connect')
@cross_origin(origin='http://localhost:8080')
def handle_connect():
    emit('connected', {'data': 'Connected'})

    current_thread = ChatThread(request.sid)
    threads[request.sid] = current_thread
    current_thread.start()

    active_threads = get_active_threads()
    emit('thread_list', {'threads': active_threads}, broadcast=True)

    handle_list_threads()

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

    thread = threads.pop(request.sid, None)
    if thread:
        thread.exit_flag.set()
        thread.join()

    active_threads = get_active_threads()
    emit('thread_list', {'threads': active_threads}, broadcast=True)

    handle_list_threads()

@socketio.on('message')
def handle_message(data):
    emit('message', {'username': data['username'], 'message': data['message']}, broadcast=True)

@socketio.on('list_threads')
def handle_list_threads():
    client_id = request.sid
    thread = threads.get(client_id)
    if thread:
        user_threads = thread.get_user_threads()
        thread_ids = [str(t.ident) for t in user_threads]
        emit('thread_list', {'threads': thread_ids})

    active_threads = get_active_threads()
    print(f"Active Threads: {active_threads}")

if __name__ == '__main__':
    socketio.run(app)

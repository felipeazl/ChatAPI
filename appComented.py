from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", transports=['websocket'])

# Armazena as threads de chat ativas e conta o número total de threads.
threads = {}
thread_count = 0
thread_count_lock = threading.Lock()

# Classe para representar uma thread de chat
class ChatThread(threading.Thread):
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.exit_flag = threading.Event()

    def run(self):
        # Ao iniciar a thread, incrementa o contador de threads e exibe o número total de threads.
        with thread_count_lock:
            global thread_count
            thread_count += 1
            print(f"Thread {self.client_id} iniciada. Total de threads: {thread_count}")

        # Loop principal da thread.
        while not self.exit_flag.is_set():
            socketio.sleep(1)

        # Ao encerrar a thread, decrementa o contador de threads e exibe o número total de threads.
        with thread_count_lock:
            thread_count -= 1
            print(f"Thread {self.client_id} encerrada. Total de threads: {thread_count}")

    def get_user_threads(self):
        # Retorna uma lista de threads associadas a um cliente específico.
        with thread_count_lock:
            user_threads = [thread for thread in threading.enumerate() if isinstance(thread, ChatThread) and thread.client_id == self.client_id]
            return user_threads

def get_active_threads():
    # Retorna uma lista de identificadores de threads ativas.
    with thread_count_lock:
        active_thread_ids = [str(thread.ident) for thread in threads.values() if thread.is_alive()]
        return active_thread_ids

@socketio.on('connect')
def handle_connect():
    # Manipula o evento de conexão de um cliente.
    # Envia uma resposta de conexão para o cliente e cria uma nova thread de chat para o cliente.

    emit('connected', {'data': 'Conectado'})

    # Cria uma nova thread de chat para o cliente atual.
    current_thread = ChatThread(request.sid)
    threads[request.sid] = current_thread
    current_thread.start()

    # Obtém a lista de threads ativas e envia para todos os clientes.
    active_threads = get_active_threads()
    emit('thread_list', {'threads': active_threads}, broadcast=True)

    handle_list_threads()

@socketio.on('disconnect')
def handle_disconnect():
    # Manipula o evento de desconexão de um cliente.
    # Interrompe e remove a thread de chat associada ao cliente.

    print('Cliente desconectado')

    # Interrompe e remove a thread de chat associada ao cliente atual.
    thread = threads.pop(request.sid, None)
    if thread:
        thread.exit_flag.set()
        thread.join()

    # Obtém a lista de threads ativas e envia para todos os clientes.
    active_threads = get_active_threads()
    emit('thread_list', {'threads': active_threads}, broadcast=True)

    handle_list_threads()

@socketio.on('message')
def handle_message(data):
    # Manipula o evento de recebimento de uma mensagem de chat.
    # Reenvia a mensagem para todos os clientes conectados.

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
    print(f"Threads Ativas: {active_threads}")

if __name__ == '__main__':
    socketio.run(app)

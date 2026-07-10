import argparse
import socket
import logging
import threading
from queue import Queue

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse parameters 
parser = argparse.ArgumentParser()
parser.add_argument('--ip', required=True)
parser.add_argument('--port', required=True)
args = parser.parse_args()

# Vars
HOST, PORT = args.ip, int(args.port)
MAX_CONNECTIONS = 10

def accept_connection_thread(soc: socket.socket, timeout: int = 10*60) -> None:
    """Accept connections in a thread"""
    while not shutdown.is_set():
        connection_semaphore.acquire() # Stop accepting if MAX_CONNECTIONS is hit
        try:
            conn, addr = soc.accept() # blocking function call until someone connects
            logger.info(f"{addr} connected...")
            conn.settimeout(timeout)
            logger.debug(f"set timeout on {addr}: {timeout}")
            with connections_lock:
                active_connections.append(conn)
        except OSError as e:
            if shutdown.is_set():
                connection_semaphore.release()
                break
            logger.error(f"Connection failed: {e}")
            connection_semaphore.release()
            continue

        # Each connection will get its own send queue so that the server receives messages async
        send_queue: Queue[bytes] = Queue()
        with client_queues_lock:
            client_queues[conn] = send_queue

        threading.Thread(target=receive_data_thread, args=(conn,), daemon=True).start()
        threading.Thread(target=send_data_thread, args=(conn, send_queue), daemon=True).start()

def cleanup_connection(conn: socket.socket):
    """Cleanup old connections from connection pool"""
    peer = conn.getpeername()
    with connections_lock:
        if conn in active_connections:
            active_connections.remove(conn)
            conn.close()
            logger.info(f"Closed connection: {peer}")
            connection_semaphore.release() # Free up a slot for a new incoming connection
            with client_queues_lock:
                client_queues.pop(conn, None)

def receive_data_thread(conn: socket.socket) -> None:
    peer = conn.getpeername()
    try:
        while True:
            # receive data from client with buffer size 1024
            data = conn.recv(1024) # blocking function call until data is received
            logger.debug(f"received {len(data)} bytes")
            if not data:
                # This only happens when client sends b'' which is triggered by a FIN message
                break
            data = f"{peer}: ".encode('utf-8') + data
            # When you receive a message, write it to all clients' queues so it can be broadcast
            with client_queues_lock:
                for c, q in client_queues.items():
                    if c is not conn:
                        q.put(data)
    except (TimeoutError, OSError) as e:
        logger.info(f"Connection to {peer} ended: {e}")
    finally:
        cleanup_connection(conn)

def send_data_thread(conn: socket.socket, send_queue: Queue[bytes]) -> None:
    while True:
        data = send_queue.get().strip()
        try:
            conn.sendall(data)
            logger.debug(f"sent {len(data)} bytes")
        except OSError as e:
            logger.info(f"Error sending data: {e}")
            break

if __name__ == "__main__":
    # Locks: Ensures thread-safe edits to the list
    connections_lock = threading.Lock()
    active_connections = []
    client_queues_lock = threading.Lock()
    client_queues = {}
    shutdown = threading.Event()
    connection_semaphore = threading.BoundedSemaphore(MAX_CONNECTIONS)
    
    # Create server socket obj
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
        # Bind the socket to a host and port
        server.bind((HOST, PORT))
        # Start listening for connections
        server.listen()
        logger.info(f"Server is listening on {HOST}:{PORT}...")

        # Start a thread to accept connections
        accept_connections = threading.Thread(target=accept_connection_thread, args=(server,), daemon=True)
        accept_connections.start()
        
        try:
            accept_connections.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            shutdown.set()


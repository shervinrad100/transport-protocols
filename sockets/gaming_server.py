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
HOST, PORT = args.ip, int(args.port)

active_connections = []
connections_lock = threading.Lock() # Ensures thread-safe edits to the list
MAX_CONNECTIONS = 10
shutdown = threading.Event()
connection_semaphore = threading.BoundedSemaphore(MAX_CONNECTIONS)


def receive_data_thread(conn: socket.socket, receive_queue: Queue[bytes]) -> None:
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
            receive_queue.put((data))
    except (TimeoutError, OSError) as e:
        logger.info(f"Connection to {peer} ended: {e}") # TODO getpeername or getsockname
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

def cleanup_connection(conn: socket.socket):
    """Cleanup old connections from connection pool"""
    peer = conn.getpeername()
    with connections_lock:
        if conn in active_connections:
            active_connections.remove(conn)
            conn.close()
            logger.info(f"Closed connection: {peer}")
            connection_semaphore.release() # Free up a slot for a new incoming connection

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


        data_queue: Queue[bytes] = Queue()

        threading.Thread(target=receive_data_thread, args=(conn, data_queue), daemon=True).start()
        threading.Thread(target=send_data_thread, args=(conn, data_queue), daemon=True).start() # TODO the sender will receive it's own message

if __name__ == "__main__":
    # Create server socket obj
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as server:
        # Bind the socket to a host and port
        server.bind((HOST, PORT))
        # Start listening for connections
        server.listen() # TODO since for each client we will have 2 threads, we should limit number of connections we accept
        logger.info(f"Server is listening on {HOST}:{PORT}...")

        # Start a thread to accept connections
        accept_connections = threading.Thread(target=accept_connection_thread, args=(server,), daemon=True)
        accept_connections.start()
        
        try:
            accept_connections.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            shutdown.set()


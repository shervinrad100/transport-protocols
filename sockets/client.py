import logging
import argparse
import socket
import threading

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Parse parameters 
parser = argparse.ArgumentParser()
parser.add_argument('--ip', required=True)
parser.add_argument('--port', required=True)
args = parser.parse_args()
HOST, PORT = args.ip, int(args.port)

# Reveive data from server in a thread
def receive_message(soc: socket.socket):
    peer = soc.getpeername()
    while True:
        try:
            # receive data from server with buffer size 1024
            data = soc.recv(1024) # blocking function call until data is received
            logger.debug(f"received {len(data)} bytes")
            if not data:
                # This only happens when server sends b'' which is triggered by a FIN message
                break
            print(f"{data.decode('utf-8')}") # TODO who is the data being received from?
        except (ConnectionResetError, ConnectionAbortedError):
            logger.error(f"Connection to {peer} was lost unexpectedly.")
            break
        except TimeoutError:
            logger.info(f"Connection to {peer} timed out.")
            break
    

# Send data to server in a thread
def send_message(soc: socket.socket):
    while True:
        data = input().strip()
        if not data:
            continue
        try:
            soc.sendall(data.encode('utf-8'))
            logger.debug(f"sent {len(data)} bytes")
        except OSError:
            logger.error("Cannot send. Connection is closed.")
            break

if __name__ == "__main__":
    # Create client socket obj
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as client:
        # Bind the socket to a host and port
        client.connect((HOST, PORT))
        logger.info(f"Client connected to {client.getpeername()} from {client.getsockname()}")

        receive_thread = threading.Thread(target=receive_message, args=(client,), daemon=True)
        send_thread = threading.Thread(target=send_message, args=(client,), daemon=True)
        
        receive_thread.start()
        send_thread.start()

        try:
            while receive_thread.is_alive():
                receive_thread.join(timeout=1)
        except KeyboardInterrupt:
            logger.info("Shutting down client")
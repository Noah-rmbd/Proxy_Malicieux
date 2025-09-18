import socket
import threading

def handle_client(client_socket):
    # Receive data from the client
    request = client_socket.recv(4096)

    # Extract the target server's address from the request
    target_host = "example.com"  # This would be parsed from the request
    target_port = 80

    # Create a socket to connect to the target server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((target_host, target_port))

    # Forward the client's request to the target server
    print("Request : ",request)
    server_socket.send(request)

    # Receive the response from the target server
    response = server_socket.recv(4096)

    # Send the response back to the client
    print("Response : ", response)
    client_socket.send(response)

    # Close the sockets
    client_socket.close()
    server_socket.close()

def start_proxy():
    # Create a socket for the proxy server
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind(("127.0.0.1", 8888))
    proxy_socket.listen(5)

    print("Proxy server is running on port 8888...")

    while True:
        # Accept incoming client connections
        client_socket, addr = proxy_socket.accept()
        print(f"Accepted connection from {addr}")

        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_proxy()

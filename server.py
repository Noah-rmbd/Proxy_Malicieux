import signal
import socket
import threading

class ProxyServer:
    def __init__(self, config):
        self.config = config
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        self.serverSocket.listen(10)
        print("Proxy started on port", config['BIND_PORT'])

    def start(self):
        try:
            while True:
                clientSocket, client_address = self.serverSocket.accept()
                threading.Thread(
                    target=self.proxy_thread,
                    args=(clientSocket,),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self, *args):
        print("\nShutting down proxy...")
        self.serverSocket.close()
        exit(0)

    def proxy_thread(self, clientSocket):
        try:
            request = clientSocket.recv(self.config['MAX_REQUEST_LEN'])
            print(request.decode('utf-8'))

            # Parse URL
            first_line = request.decode().split('\n')[0]
            url = first_line.split(' ')[1]

            http_pos = url.find("://")
            temp = url[(http_pos+3):] if http_pos != -1 else url

            port_pos = temp.find(":")
            webserver_pos = temp.find("/")
            if webserver_pos == -1:
                webserver_pos = len(temp)

            webserver = ""
            port = 80
            if port_pos == -1 or webserver_pos < port_pos:
                webserver = temp[:webserver_pos]
            else:
                port = int(temp[port_pos+1:webserver_pos])
                webserver = temp[:port_pos]

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.config['CONNECTION_TIMEOUT'])
            s.connect((webserver, port))
            s.sendall(request)

            while True:
                data = s.recv(self.config['MAX_REQUEST_LEN'])
                if len(data) > 0:
                    clientSocket.send(data)
                else:
                    break

            s.close()
            clientSocket.close()

        except Exception as e:
            print("Error in proxy_thread:", e)
            clientSocket.close()

# Exemple d'utilisation :
if __name__ == '__main__':
    config = {
        'HOST_NAME': '127.0.0.1',
        'BIND_PORT': 8888,
        'MAX_REQUEST_LEN': 4096,
        'CONNECTION_TIMEOUT': 5
    }

    proxy = ProxyServer(config)
    signal.signal(signal.SIGINT, proxy.shutdown)
    proxy.start()

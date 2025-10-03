import signal
import socket
import threading

class ProxyServer:
    def __init__(self, config):
        """Initialize proxy server with configuration settings"""
        self.config = config
        # Create TCP socket for server
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow socket address reuse to avoid "Address already in use" errors
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to configured host and port
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        # Listen for incoming connections (queue up to 10)
        self.serverSocket.listen(10)
        print("Proxy started on port", config['BIND_PORT'])

    def start(self):
        """Main server loop that accepts client connections"""
        try:
            while True:
                # Accept incoming client connection
                clientSocket, client_address = self.serverSocket.accept()
                print("Start thread :")
                # Spawn new thread to handle client request (enables concurrent connections)
                threading.Thread(
                    target=self.proxy_thread,
                    args=(clientSocket,),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self, *args):
        """Shut down the proxy server"""
        print("\nShutting down proxy...")
        self.serverSocket.close()
        exit(0)
    
    # --------------------- fake-news functions --------------------------------
    def change_content_length(self, data, difference):
        """Update Content-Length header of the given data"""
        start = "Content-Length: "
        # Locate Content-Length header in HTTP response
        idx1 = data.find(start)
        idx2 = data.find("\r", idx1 + len(start))
        # Extract current content length value
        number = int(data[idx1 + len(start):idx2])
        # Replace with updated value (only first occurrence)
        return data.replace(str(number), str(number + difference), 1)
    
    def replace_word(self, data, old, new):
        """Replace all occurrences of a word and update Content-Length accordingly"""
        # Count the occurences of old word
        nb_words = data.count(old)
        # Calculate byte difference between old and new strings (UTF-8)
        char_diff = len(bytes(new, 'utf-8')) - len(bytes(old, 'utf-8'))
        
        if (nb_words > 0):
            # Perform string replacement
            data = data.replace(old, new)
            # Adjust Content-Length header to reflect total byte change
            data = self.change_content_length(data, char_diff*nb_words)
        return data
    
    def apply_fake_news(self, data):
        """Apply content modifications to HTML responses"""
        # Replace "Stockholm" with "Linköping"
        data = self.replace_word(data, " Stockholm", " Linköping")
        # Replace local smiley image with trolley URL
        data = self.replace_word(data, "./smiley.jpg", "https://i.redd.it/cgefug8s28881.jpg")
        # Replace "Smiley" with "Trolley"
        data = self.replace_word(data, "Smiley", "Trolley")
        return data

    # --------------------- main thread -------------------------------------
    def proxy_thread(self, clientSocket):
        """Handle individual client request by forwarding to destination server"""
        # Receive HTTP request from client
        request = clientSocket.recv(self.config['MAX_REQUEST_LEN'])
        print("\nRequest : \n", request.decode('utf-8'))

        # Parse destination server from HTTP request line
        first_line = request.decode().split('\n')[0]
        url = first_line.split(' ')[1]
        # Strip protocol prefix (http://)
        http_pos = url.find("://")
        temp = url[(http_pos+3):] if http_pos != -1 else url

        # Extract hostname and port from URL
        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = 80 # Default HTTP port
        if port_pos == -1 or webserver_pos < port_pos:
            # No explicit port specified
            webserver = temp[:webserver_pos]
        else:
            # Port explicitly specified in URL
            port = int(temp[port_pos+1:webserver_pos])
            webserver = temp[:port_pos]

        # Connect to destination web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        # Forward client's request to destination server
        s.sendall(request)

        # Receive and forward response data
        while True:
            data = s.recv(self.config['MAX_REQUEST_LEN'])
            print("la réponse : ", data)
            # Apply content modification if response is HTML
            if len(data) > 0 and "html" in url:
                # Decode response to string
                data = data.decode('utf-8', 'ignore')
                # Apply fake news transformations
                data = self.apply_fake_news(data)
                # Re-encode to bytes
                data = bytes(data,  "utf-8")
                # Send modified data to client
                clientSocket.send(data)
                
            # Forward non-HTML data unchanged
            elif len(data) > 0:
                clientSocket.send(data)
            else:
                # No more data, close connections
                break

        s.close()
        clientSocket.close()

# Instantiates and run the ProxyServer
if __name__ == '__main__':
    # Configuration dictionary
    config = {
        'HOST_NAME': '127.0.0.1',  # Localhost
        'BIND_PORT': 8888,         # Proxy listening port
        'MAX_REQUEST_LEN': 4096    # Maximum request/response buffer size
    }

    proxy = ProxyServer(config)
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, proxy.shutdown)
    proxy.start()
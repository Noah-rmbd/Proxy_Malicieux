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
                print("Start thread :")
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

    def change_content_length(self, data, difference):
        start = "Content-Length: "
        # Find the index of the start and end substring
        idx1 = data.find(start)
        idx2 = data.find("\r", idx1 + len(start))
        # Find the original value
        number = int(data[idx1 + len(start):idx2])
        
        return data.replace(str(number), str(number + difference), 1)

    def replace_link(self, data, old="./smiley.jpg", new="https://i.redd.it/cgefug8s28881.jpg"):
        # count the occurences of old link
        nb_links = data.count(old)
        # calculate the difference of length between old and new in utf-8
        char_diff = len(bytes(new, 'utf-8')) - len(bytes(old, 'utf-8'))

        if (nb_links > 0):
            # replace old by new
            data = data.replace(old, new)
            # update the content_length field
            data = self.change_content_length(data, char_diff*nb_links)
        return data
    
    def replace_word(self, data, old=" Stockholm", new=" Linköping"):
        # count the occurences of old word
        nb_words = data.count(old)
        # calculate the difference of length between old and new in utf-8
        char_diff = len(bytes(new, 'utf-8')) - len(bytes(old, 'utf-8'))
        
        if (nb_words > 0):
            # replace old by new
            data = data.replace(old, new)
            # update the content_length field
            data = self.change_content_length(data, char_diff*nb_words)
        return data
    
    def apply_fake_news(self, data):
        # takes an http packet as input and outputs this packet with fake news
        data = self.replace_word(data, " Stockholm", " Linköping")
        data = self.replace_word(data, "./smiley.jpg", "https://i.redd.it/cgefug8s28881.jpg")
        data = self.replace_word(data, "Smiley", "Siphano")
        return data


    def proxy_thread(self, clientSocket):
        request = clientSocket.recv(self.config['MAX_REQUEST_LEN'])
        print("\nRequest : \n", request.decode('utf-8'))

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
        s.connect((webserver, port))
        s.sendall(request)

        while True:
            data = s.recv(self.config['MAX_REQUEST_LEN'])
    
            if len(data) > 0 and "html" in url:
                # Converts the utf-8 data into string
                data = data.decode('utf-8', 'ignore')
                data = self.apply_fake_news(data)
                #data = self.replace_word(data)
                #data = self.replace_link(data)
                data = bytes(data,  "utf-8")
              
                clientSocket.send(data)
            elif len(data) > 0:
                clientSocket.send(data)
            else:
                break

        s.close()
        clientSocket.close()

# Exemple d'utilisation :
if __name__ == '__main__':
    config = {
        'HOST_NAME': '127.0.0.1',
        'BIND_PORT': 8888,
        'MAX_REQUEST_LEN': 4096
    }

    proxy = ProxyServer(config)
    signal.signal(signal.SIGINT, proxy.shutdown)
    proxy.start()
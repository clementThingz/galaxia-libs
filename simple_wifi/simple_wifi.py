import wifi
import socketpool
import sys
import time
import ipaddress

_simple_tcp_socket_pool = socketpool.SocketPool(wifi.radio)


class SimpleTcp:
    def __init__(self):
        self.server_socket = None
        self.client_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
        self.current_client = None
    
    def start_server(self, port=80):
        if self.server_socket:
            self.server_socket.close()
        self.server_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
        #Création du serveur
        self.server_socket.bind((str(wifi.radio.ipv4_address),port))
        self.server_socket.listen(1)

    def monitor_server(self):
        if self.server_socket:
            self.server_socket.setblocking(False)
            try:
                if self.current_client:
                    self.current_client[0].close()

                self.current_client = self.server_socket.accept()
                
            except OSError:
                pass
            self.server_socket.setblocking(True)

    def wait_client(self, timeout=None):
        if not self.server_socket:
            raise AttributeError("Server not started")
        if self.current_client:
            return self.current_client[1]

        self.server_socket.settimeout(timeout)
       # timestamp = time.monotonic() 
        # while (timeout == None or (time.monotonic() - timestamp) < timeout):
        try:
            client = self.server_socket.accept()
        except OSError as e:
            print(e)
            t, value, trace = sys.exc_info()
            code = value.args[0]
            if code == 116 or code == 11: #TIMEOUT == 116
                self.server_socket.setblocking(True)
                return None
            else:
                self.server_socket.setblocking(True)
                raise e

        self.server_socket.setblocking(True)

        # if timeout and (time.monotonic() - timestamp) >= timeout:
        #     return None

        client[0].setblocking(True)
        self.current_client = client
        return client[1]

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()

    def receive_from_client(self, timeout=None):
        if not self.current_client:
            raise AttributeError("No client")
        buff = bytearray(256)
        if timeout:
            self.current_client[0].settimeout(timeout)
        try:
            numbytes = self.current_client[0].recvfrom_into(buff)
        except OSError as e:
            print(e)
            if timeout:
                self.current_client[0].setblocking(True)
            return bytearray()

        if timeout:
            self.current_client[0].setblocking(True)
        
        buff = buff[: numbytes[0]]
        return buff

    def send_to_client(self, data):
        if not self.current_client:
            raise AttributeError("No client")
        if (not type(data) is bytes) and (not type(data) is bytearray):
            raise TypeError('data must be of type bytes or bytearray, found '+str(type(data)))
        sent = 0
        while sent < len(data):
            s = self.current_client[0].send(data[sent:])
            sent += s
    
    def close_client(self):
        if self.current_client:
            self.current_client[0].close()
        self.current_client = None
    
    def connect(self, ip, port=80):
        # if not self.client_socket:
        #     self.client_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
        
        s_connected = False
        deleteSocket = True
        while not s_connected:
            try:
                self.monitor_server()
                if deleteSocket == True:
                    self.client_socket.close()
                    self.client_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
                self.client_socket.connect((ip, port))
                s_connected = True
                deleteSocket = True
            except OSError as e:
                # print(e)
                t, value, trace = sys.exc_info()
                code = value.args[0]
                if code == 11:
                    deleteSocket = False
                elif code != 0 and code != 127:
                    raise e
        
    def send(self, data):
        if not self.client_socket:
            raise AttributeError("No client")
        if (not type(data) is bytes) and (not type(data) is bytearray):
            raise TypeError('data must be of type bytes or bytearray, found '+str(type(data)))
        sent = 0
        while sent < len(data):
            s = self.client_socket.send(data[sent:])
            sent += s

    def receive(self, timeout=None):
        if not self.client_socket:
            raise AttributeError("Not connected")
        buff = bytearray(256)
        if timeout:
            self.client_socket.settimeout(timeout)
        numbytes = self.client_socket.recvfrom_into(buff)
        if timeout:
            self.client_socket.setblocking(True)
        buff = buff[: numbytes[0]]
        return buff

    def close(self):
        if self.client_socket:
            self.client_socket.close()


class SimpleWifi:
    
    def __init__(self):
        self.simple_tcp = SimpleTcp()
        self.ip = None
        self.last_ip = None

    def get_my_ip(self):
        return self.ip
    
    def get_last_connected_ip(self):
        return self.last_ip

    def connect(self, ssid, pwd, static_ip=None, server_port=80):
        ip = None
        while not ip:
            try:
                wifi.radio.connect(ssid, pwd)
                ip = wifi.radio.ipv4_address
            except ConnectionError as e:
                print(e)
                pass

        
        if static_ip:
            addr = ipaddress.IPv4Address(static_ip)
            wifi.radio.set_ipv4_address(addr)

        self.simple_tcp.start_server(server_port)
        self.ip = wifi.radio.ipv4_address
        print(self.ip)
        return self.ip
    
    def send(self, data, ip, port=80):
        try:
            self.simple_tcp.connect(ip, port)
            # length = len(data)
            b = bytes(str(data), "utf-8")
            # b.append(length & 0xff)
            # b.append((length >> 8) & 0xff)
            # b.append((length >> 16) & 0xff)
            # b.append((length >> 24) & 0xff)

            # for d in data:
            #     b.append(d)
            
            self.simple_tcp.send(b)
            self.simple_tcp.close()
        except OSError as e:
            print(e)
            self.simple_tcp.close()
            return False
        return True

    def receive(self, protocol=None, ip=None, timeout=None):
        timestamp = time.monotonic() 
        self.simple_tcp.close_client()
        while True:
            client_ip = self.simple_tcp.wait_client(timeout)
            #print(client_ip)
            if not client_ip:
                return ""
            
            self.last_ip = client_ip[0]
            if ip == None or str(client_ip[0]) == str(ip):
                data = bytearray()
                while (timeout == None or (time.monotonic() - timestamp) < timeout):
                    d = self.simple_tcp.receive_from_client(0)
                    if len(d) > 0:
                        for b in d:
                            data.append(b)
                    else:  
                        self.simple_tcp.close_client()
                        return data.decode("utf-8")
                    request = data.decode("utf8-8")
                    if protocol == "http" and request.endswith("\r\n\r\n"):
                        return request


                # if timeout != None and (time.monotonic() - timestamp) >= timeout:
                #     self.simple_tcp.close_client()
                #     return bytearray()

                # length = data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24
                # while len(data) < length + 4 and (timeout == None or (time.monotonic() - timestamp) < timeout):
                #     d = self.simple_tcp.receive_from_client(0)
                #     if len(d) > 0:
                #         for b in d:
                #             data.append(b)
                #     else:
                #         self.simple_tcp.close_client()
                #         return bytearray()

                # self.simple_tcp.close_client()
                # return data[4:]
            else:
                self.simple_tcp.close_client()

    def send_to_client(self, data):
        b = bytes(str(data), "utf-8")
        return self.simple_tcp.send_to_client(b)

class SimpleHttpRequest:

    def __init__(self, method="", url="", params=dict()):
        self.method = method
        self.url = url
        self.params = params

    def get_method(self):
        return self.method
    
    def set_method(self, method):
        self.method = method
    
    def get_url(self):
        return self.url

    def set_url(self, url):
        self.url = url
    
    def set_params(self, params):
        self.params = params
    
    def get_params(self):
        return self.params
    
    def add_params(self, key, value):
        self.params[key] = value

class SimpleHttpResponse:

    def __init__(self, code=200, text="", headers=dict()):
        self.code = code
        self.headers = headers
        self.text = str(text)
    
    def __str__(self):
        response = "HTTP/1.1 "+str(self.code)+"\r\n"
        response += "content-type: text/html\r\n"
        response += "\r\n"
        response += self.text
        return response

    def get_code(self):
        return self.code
    
    def set_code(self, code):
        self.code = code

    def get_text(self):
        return self.text
    
    def set_text(self, text):
        self.text = str(text)
    
    def set_headers(self, headers):
        self.headers = headers
    
    def get_headers(self):
        return self.headers
    
    def add_headers(self, key, value):
        self.headers[key] = value

    def replace(self, key, value):
        self.text = self.text.replace("{"+key+"}", value)

class SimpleHttp:

    def __init__(self, simple_wifi):
        self.simple_wifi = simple_wifi
        self.request = None

    def __get_params(self, url):
        d = dict()
        params = url.split("?")[1]
        params = params.split('&')
        for p in params:
            pair = p.split("=")
            if len(pair) == 2:
                d[pair[0]] = pair[1]
        print(params)
        
        return d

    def __parse_request(self, request):
        if request.startswith("GET"):
            r = SimpleHttpRequest("GET")
            key_http = request.find("HTTP")
            if key_http == -1:
                raise AttributeError("Malformed request, http not found:"+str(request))
            url_complete = request[4:key_http].split(' ')[0]
            index = url_complete.find("?")
            if index != -1:
                r.set_url(url_complete[:index])
                params = self.__get_params(url_complete)
                r.set_params(params)
            else:
                r.set_url(url_complete)
            return r
        else:
            raise AttributeError("Unknown request:"+str(request))

    def wait_request(self):
        while True:
            request = self.simple_wifi.receive(protocol="http")
            #print(len(request))
            if len(request) > 0:
                self.request = self.__parse_request(request)
                return self.request

    def respond(self, response, code=200):
        r = SimpleHttpResponse(code, response)
        path = __file__
        path = path[:path.find("simple_wifi.py")]+"template.html"
        f = open(path)
        r.set_text(f.read())
        f.close()
        r.replace("request", self.request.get_url())
        r.replace("response", str(response))
        return self.simple_wifi.send_to_client(str(r))
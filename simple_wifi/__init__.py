import wifi
import socketpool
import sys
import time
import ipaddress

try:
    import ethernet
except:
    pass

_simple_tcp_socket_pool = socketpool.SocketPool(wifi.radio)

"""wifi"""

class SimpleTcp:
    
    """SimpleTcp"""
    def __init__(self, initClient=True):
        self.server_socket = None
        if initClient:
            self.client_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
        self.current_client = None
    
    def start_server(self, ip=None, port=2000):
        if ip == None:
            ip = wifi.radio.ipv4_address

        if self.server_socket:
            self.server_socket.close()
        self.server_socket = _simple_tcp_socket_pool.socket(_simple_tcp_socket_pool.AF_INET, _simple_tcp_socket_pool.SOCK_STREAM)
        #Création du serveur
        self.server_socket.bind((str(ip),port))
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

    def wait_client(self, timeout=None, debug=True):
        if not self.server_socket:
            raise AttributeError("Server not started")
        if self.current_client:
            return self.current_client[1]

        self.server_socket.settimeout(timeout)
       # timestamp = time.monotonic() 
        # while (timeout == None or (time.monotonic() - timestamp) < timeout):
        try:
            client = self.server_socket.accept()
            self.server_socket.setblocking(True)

            # if timeout and (time.monotonic() - timestamp) >= timeout:
            #     return None

            client[0].setblocking(True)
            self.current_client = client
            return client[1]
        except OSError as e:
            if debug:
                print(e)
            #t, value, trace = sys.exc_info()
            #print(value)
            #code = value.args[0]
            if e.errno == 116 or e.errno == 11: #TIMEOUT == 116
                self.server_socket.setblocking(True)
                return None
            else:
                self.server_socket.setblocking(True)
                raise e

    def has_client(self):
        if self.current_client:
            return True
        return False

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
            
            if timeout:
                self.current_client[0].setblocking(True)
                raise Exception("Timeout")
            else:
                print(e)
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
            try:
                s = self.current_client[0].send(data[sent:])
                sent += s
            except:
                return
    
    def close_client(self):
        if self.current_client:
            self.current_client[0].close()
        self.current_client = None
    
    def connect(self, ip, port=2000):
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
                try:
                    t, value, trace = sys.exc_info()
                    code = value.args[0]
                    if code == 11:
                        deleteSocket = False
                    elif code != 0 and code != 127:
                        raise e
                except:
                    pass
        
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
    """SimpleWfi"""
    def __init__(self):
        self.simple_tcp = SimpleTcp()
        self.simple_tcp_http = SimpleTcp(False)
        self.ip = None
        self.ip_ap = None
        self.last_ip = None

    def get_my_ip(self):
        return self.ip
    
    def get_my_ip_ap(self):
        return self.ip_ap
    
    def get_last_connected_ip(self):
        return self.last_ip

    def is_client_connected(self):
        return self.simple_tcp.has_client()

    def scan(self):
        """
        Scan wifi nearby wifi networks

        :return: An array of Network objects. Each has a ssid attribute and a rssi attribute
        """
        networks = []
        for network in wifi.radio.start_scanning_networks():
            networks.append(network)
        wifi.radio.stop_scanning_networks()
        return networks


    def connect(self, ssid, pwd, static_ip=None, server_port=2000, timeout=None, netmask=None, gateway=None):
        """
        Connect to an access point

        :param ssid: Access point ssid
        :param pwd: Access point password
        :param static_ip: The static IP to assign to the Galaxia
        :param server_port: The port used by the TCP server
        :param timeout: Maximum time in seconds to wait for connection (None = no timeout)
        """
        ip = None
        timestamp = time.monotonic()

        while not ip:
            if timeout and (time.monotonic() - timestamp) >= timeout:
                #print(f"Timeout lors de la connexion WiFi après {timeout}s")
                #return None
                raise RuntimeError(f"Timeout lors de la connexion WiFi après {timeout}s")

            try:
                wifi.radio.connect(ssid, pwd)
                ip = wifi.radio.ipv4_address
            except ConnectionError as e:
                if str(e) == "Aucun réseau avec ce ssid":
                    print("Pas de réseau avec SSID = "+ssid)
                else:
                    print(e)

                if timeout and (time.monotonic() - timestamp) >= timeout:
                    #print(f"Timeout lors de la connexion WiFi après {timeout}s")
                    #return None
                    raise RuntimeError(f"Timeout lors de la connexion WiFi après {timeout}s")
                pass

        
        if static_ip:
            addr = ipaddress.IPv4Address(static_ip)
            n = ipaddress.IPv4Address(netmask) if netmask else None
            g = ipaddress.IPv4Address(gateway) if gateway else None
            wifi.radio.set_ipv4_address(addr, netmask=n, gateway=g)

        self.ip = wifi.radio.ipv4_address
        self.simple_tcp.start_server(self.ip, server_port)
        self.simple_tcp_http.start_server(self.ip, 80)

        print("Connecté au point d'accès")
        print("IP Galaxia :"+str(self.ip))
        return self.ip

    def connect_eth(self, static_ip=None, server_port=2000, timeout=None, netmask=None, gateway=None):
        """
        Connect via Ethernet

        :param static_ip: The static IP to assign to the Galaxia
        :param server_port: The port used by the TCP server
        :param timeout: Maximum time in seconds to wait for connection (None = no timeout)
        """
         # Essayer d'activer Ethernet une seule fois
        eth_status = ethernet.active(True)

        # Si None, l'adaptateur n'existe pas - sortir immédiatement
        if eth_status is None:
            #print("Eth adapter not found")
            gc.collect()
            #return None
            raise RuntimeError("Eth adapter not found")

        timestamp_start = time.time()

        ethernet.ifconfig("dhcp")
        timestamp = time.monotonic()
        dhcp_timeout = 2.5 if static_ip else (timeout - (time.monotonic() - timestamp_start) if timeout else None)

        while not ethernet.isconnected():
            if dhcp_timeout and (time.monotonic() - timestamp) >= dhcp_timeout:
                break
            pass

        if not ethernet.isconnected() and not static_ip:
            #print(f"Timeout lors de la connexion Ethernet après {timeout}s")
            ethernet.active(False)  # Désactiver Ethernet avant de sortir
            gc.collect()
            #return None
            raise RuntimeError(f"Timeout lors de la connexion Ethernet après {timeout}s")

        c = list(ethernet.ifconfig())
        if static_ip:
            c[0] = static_ip
            if netmask:
                c[1] = netmask
            if gateway:
                c[2] = gateway
            ethernet.ifconfig(c)
        c = ethernet.ifconfig()
        self.ip = c[0]
        self.simple_tcp.start_server(self.ip, server_port)
        self.simple_tcp_http.start_server(self.ip, 80)
        print("Connecté")
        print("IP Galaxia :"+str(self.ip))
        return self.ip

    def start_access_point(self, ssid="Thingz-Galaxia", password="", server_port=2000):
        """
        Start an access point on the Galaxia

        :param ssid: Access point name
        :param password: Access point password
        :param server_port: The port used by the TCP server
        """
        if(len(password) > 0):
            wifi.radio.start_ap(ssid, password)
        else:
            wifi.radio.start_ap(ssid)

        self.ip_ap = wifi.radio.ipv4_address_ap
        self.simple_tcp.start_server(self.ip_ap, server_port)
        self.simple_tcp_http.start_server(self.ip_ap, 80)

        print("IP Galaxia :"+str(self.ip_ap))
        return self.ip_ap

    
    def send(self, data, ip, port=2000, stopSequence="\r", waitResponse=False):
        """
        Connect to IP and send data

        :param data: the data to be send
        :type data: bytearray
        :param ip: The IP address to connect to
        :param port: The port to connect to
        """
        try:
            self.simple_tcp.connect(ip, port)
            # length = len(data)
            b = bytes(str(data)+stopSequence, "utf-8")
            # b.append(length & 0xff)
            # b.append((length >> 8) & 0xff)
            # b.append((length >> 16) & 0xff)
            # b.append((length >> 24) & 0xff)

            # for d in data:
            #     b.append(d)
            
            self.simple_tcp.send(b)
            data = bytearray()
            response = None
            if waitResponse:
                while True:
                    if len(data):
                        timeout = 1
                    try:    
                        d = self.simple_tcp.receive()
                        #print(d)
                        if len(d) > 0:
                            for b in d:
                                data.append(b) 
                    except:
                        break

                    response = data.decode("utf-8")
                    
                    if response.endswith(stopSequence):
                        break
            
            self.simple_tcp.close()
            if waitResponse:
                if not response:
                    return ""
                return response[:response.find(stopSequence)]
        except OSError as e:
            print(e)
            self.simple_tcp.close()
            return False
        return True

    def receive(self, ip=None, timeout=None, stopSequence="\r", block=True, reuseClient=False, verbose=False):
        """
        Receive data from TCP server

        :param ip: Filter request by IP. Requests from other IPs than IP will be ignored
        :param timeout: set how long to wait before returning if no data is received
        :param stopSequence: set the end of message characters
        :param block: wait until something is received
        :param reuseClient: If a client is already connected, keep the connection and try to receive from this client again
        :return: A string containing the message
        """
        #keep current client
        if not reuseClient:
            self.simple_tcp.close_client()

        while True:
            #wait for client only if we don't reuse the same
            if not reuseClient or (not self.simple_tcp.has_client()):
                client_ip = self.simple_tcp.wait_client(timeout if block else 0, debug=True if block else False)
                #print(client_ip)
                if not client_ip:
                    if block:
                        continue
                    return ""
            
                self.last_ip = client_ip[0]

            if ip == None or str(self.last_ip) == str(ip):
                data = bytearray()
                timestamp = time.monotonic()
                while (timeout == None or (time.monotonic() - timestamp) < timeout):
                    force_timeout = 0
                    if len(data) > 0 :
                        force_timeout = 1 #if reception started force timeout
                    
                    d = ""
                    timeout_triggered = False
                    try:
                        d = self.simple_tcp.receive_from_client(force_timeout)
                    except Exception as e:
                        #print(e)
                        if str(e) == "Timeout":
                            timeout_triggered = True
                        d = ""

                    if len(d) > 0:
                        for b in d:
                            data.append(b)
                    else:
                        if not timeout_triggered: #socket was closed on the other side
                            self.simple_tcp.close_client()
                            break
                        else:
                            if verbose:
                                print("Message de "+str(self.last_ip))
                            return data.decode("utf-8")

                    request = data.decode("utf-8")
                    
                    if request.endswith(stopSequence):
                        if verbose:
                            print("Message de "+str(self.last_ip))
                        return request[:request.find(stopSequence)]
            else:
                self.simple_tcp.close_client()

    def receive_http(self, ip=None, timeout=None, block=True, verbose=False):
        """
        Receive an HTTP request from the HTTP server

        :param ip: Filter request by IP. Requests from other IPs than IP will be ignored
        :param timeout: set how long to wait before returning if no data is received
        :param block: wait until something is received
        :return: The HTTP request
        :rtype: :class:`simple_wifi.SimpleHttpRequest`
        """
        self.simple_tcp_http.close_client()

        while True: 
            client_ip = self.simple_tcp_http.wait_client(timeout if block else 0, debug=True if block else False)
            #print(client_ip)
            if not client_ip:
                if block:
                    continue
                return ""
            self.last_ip = client_ip[0]
            if ip == None or str(client_ip[0]) == str(ip):
                data = bytearray()
                timestamp = time.monotonic()
                request = ""
                while (timeout == None or (time.monotonic() - timestamp) < timeout):
                    force_timeout = 0
                    
                    d = ""
                    try:
                        d = self.simple_tcp_http.receive_from_client(force_timeout)
                    except Exception:
                        d = ""

                    if len(d) > 0:
                        request += d.decode("utf-8")
                        for b in d:
                            data.append(b)
                    else:  
                        self.simple_tcp_http.close_client()
                        if verbose:
                            print("Message de "+str(self.last_ip))
                        return request

                    
                    if request.endswith("\r\n\r\n"):
                        if verbose:
                            print("Message de "+str(self.last_ip))
                        return request

            else:
                self.simple_tcp_http.close_client()

    def send_to_client(self, data, stopSequence='\r'):
        """
        Respond to a client of the TCP server

        :param data: the response
        """
        b = bytes(str(data)+stopSequence, "utf-8")
        try:
            return self.simple_tcp.send_to_client(b)
        except OSError:
            self.simple_tcp.close_client()
            return False
        except AttributeError:
            return False
    
    def send_to_http_client(self, data):
        """
        Respond to client of the HTTP server

        :param data: the response
        """
        b = bytes(str(data), "utf-8")
        return self.simple_tcp_http.send_to_client(b)

    def close(self, http=False):
        """
        Close the connection with the current client of the TCP server
        """
        if http:
            self.simple_tcp_http.close_client()
        else:
            self.simple_tcp.close_client()
             
    def close_connection_with_server(self):
        """
        Close existing socket

        """
        self.simple_tcp.close()

class SimpleHttpRequest:

    def __init__(self, method="", url="", params=dict()):
        self.method = method
        self.url = url
        self.params = params
        self.returned = False
        self.timestamp = time.monotonic()

    #The request has been returned to the user
    def set_returned(self):
        self.returned = True

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
    
    def get_timestamp(self):
        return self.timestamp

class SimpleHttpResponse:

    def __init__(self, code=200, text="", headers=dict()):
        self.code = code
        self.headers = headers
        self.text = str(text)
        self.content_type = "text/html"
    
    def __str__(self):
        response = self.get_http_header()
        response += self.text
        return response

    def get_http_header(self):
        response = "HTTP/1.1 "+str(self.code)+"\r\n"
        response += "content-type: "+self.content_type+"\r\n"
        response += "\r\n"
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
        #url map to webpage who need to be resolve in background (through a call of handle_web_page/get_pending_request())
        self.web_page_urls = []
        self.page_elements = {}
        #Lock for wait request
        self.wait = False
        self.wait_request_has_been_called = False
        self.request_timeout = 5

    def __get_params(self, url):
        d = dict()
        params = url.split("?")[1]
        params = params.split('&')
        for p in params:
            pair = p.split("=")
            if len(pair) == 2:
                d[pair[0]] = pair[1]
        #print(params)
        
        return d

    def __parse_request(self, request):
        if request.startswith("GET"):
            r = SimpleHttpRequest("GET")
            key_http = request.find("HTTP")
            if key_http == -1:
                raise AttributeError("Malformed request, http not found:"+str(request))
            url_complete = request[5:key_http].split(' ')[0]

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

    def add_web_page_url(self, url, cb):
        for page in self.web_page_urls:
            if page["url"] == url:
                page["cb"] = cb
                return
        self.web_page_urls.append({"url":url, "cb": cb})

    def add_web_button(self, url, cb):
        self.page_elements[url] = {"type": "button", "value":False, "cb":cb}
        self.web_page_urls.append({"url": url, "cb": self.handle_button})

    def handle_button(self):
        url = self.request.get_url()
        if url in self.page_elements.keys() and self.page_elements[url]["type"] == "button":
            self.page_elements[url]["value"] = True
        
        if self.page_elements[url]["cb"]:
            self.page_elements[url]["cb"]()
            self.page_elements[url]["value"] = False

        self.respond(str(self.page_elements[url]["value"]))


    def get_page_element(self, url):
        if url in self.page_elements.keys():
            value = self.page_elements[url]["value"] 
            if value and self.page_elements[url]["type"] == "button":
                self.page_elements[url]["value"] = False
            return value
        return None

    def handle_web_pages(self):
        if self.wait == True:
            return None

        request = self.get_pending_request()
        if request and request['user_cb']:
            request['user_cb']()
    
    def get_pending_request(self):
        #Not connected

        if wifi.radio.ipv4_address == None and wifi.radio.ipv4_address_ap == None:
            try:
                if not ethernet.isconnected():
                    return None
            except:
                return None

        if self.request:
            for page in self.web_page_urls:
                if page['url'] == self.request.get_url():
                    if self.request.returned:
                        return None
                    self.request.set_returned()
                    return { "request": self.request, "user_cb": page['cb']}

            if self.wait_request_has_been_called == True and time.monotonic() - self.request.get_timestamp() < self.request_timeout:
                    return None
               
        try:
            request = self.simple_wifi.receive_http(block=False)
        except AttributeError:
            self.simple_wifi.close(True)
            return None

        #print(len(request))
        if len(request) > 0:
            self.request = self.__parse_request(request)
            for page in self.web_page_urls:
                # print(page)
                if page['url'] == self.request.get_url():
                    # print("Ok")
                    return { "request": self.request, "user_cb": page['cb']}

        self.simple_wifi.close(True)
        return None

    def wait_request(self):
        self.wait_request_has_been_called = True
        while True:
            if self.request and (not self.request.returned):
                self.request.set_returned()
                return self.request

            self.request = None
            self.wait = True
            
            request = self.simple_wifi.receive_http(timeout=5000)
            
            #print(len(request))
            if len(request) > 0:
                self.request = self.__parse_request(request)
                found_web_page = False
                for page in self.web_page_urls:
                    if page['url'] == self.request.get_url():
                        page['cb']()
                        found_web_page = True
                        break
                self.wait = False
                if found_web_page:
                    continue
                #print(self.request.get_url())
                self.request.set_returned()
                return self.request

    def respond_with_html(self, response, code=200, template="template.html", tags=None):
        if tags == None:
            url = ""
            if self.request:
                self.request.get_url()
            tags = [('request', self.request.get_url())]
        tags.append(('response', str(response)))

        r = SimpleHttpResponse(code, response)
       
        path = __file__
        path = path[:path.find("__init__.mpy")]+str(template)
        f = open(path)

        end = False
        page = ""

        self.simple_wifi.send_to_http_client(r.get_http_header())
        tagsFound = {}
        while not end:
            tagPartialFound = False
            content = f.read(512)
            if content:
                page += content
            else:
                #print("end file")
                break

            for tag, value in tags:
                if tag in tagsFound.keys():
                    continue
                if page.find("{"+tag+"}") != -1:
                    page = page.replace("{"+tag+"}", str(value))
                    tagsFound[tag] = "found"
                else:
                    # break
                    for i in range(len(tag), 0, -1):
                        if page.endswith(tag[-i:]):
                            tagPartialFound = True
                            break
            if not tagPartialFound:
                # print("no partial")
                # print(page)
                self.simple_wifi.send_to_http_client(page)
                page = ""
             
        #r.set_text(f.read())
        
        f.close()

        # r.replace('response', str(response))
        # for tag, value in tags:
        #     r.replace(tag, str(value))
        if len(page):
            r = self.simple_wifi.send_to_http_client(page)
        self.request = None
        return r

    def respond(self, response, code=200):
        r = SimpleHttpResponse(code, response)
        r.content_type = "text/plain"
        r.set_text(response)

        r = self.simple_wifi.send_to_http_client(str(r))
        self.request = None
        return r


def version():
    return "1.0.26"
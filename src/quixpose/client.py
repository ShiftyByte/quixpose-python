from enum import Enum
import requests
import websocket
import rel
import json
import base64

CLIENT_DEFAULT_API_HOST = "api.quixpose.io"

class ClientErrorCategory(Enum):
    NETWORK = 1 # Technical network connectivity issue
    SERVICE = 2 # Quixpose service issue
    USAGE = 3 # Incorrect usage of the client class

class ClientError(Exception):
    def __init__(self, category, message):
        super().__init__(message)
        self._category = category

class Client:
    def __init__(self, **kwargs):
        self._endpoint_id = None
        self._ws = None
        self._ws_rcv_callback = None
        self._recv_callback = None
        self._connect_callback = None
        self._disconnect_callback = None
        self._api_host = CLIENT_DEFAULT_API_HOST
        if "api_host" in kwargs:
            self._api_host = kwargs['api_host']
    
    def get_endpoint(self):
        # check if we already have an endpoint and port
        if self._endpoint_id is not None and self._remote_port is not None:
            return self._endpoint_id, self._remote_port
        # Request a new endpoint id
        url = f"https://{self._api_host}/expose"
        resp = requests.post(url, json={})
        # check http response errors
        if resp.status_code != 200:
            raise ClientError(ClientErrorCategory.NETWORK, f"HTTP Error {resp.status_code}: {resp.reason}")
        # check content is json
        try:
            jresp = resp.json()
        except requests.exceptions.JSONDecodeError:
            raise ClientError(ClientErrorCategory.SERVICE, f"Response from api was was not a valid JSON: {resp.text}")
        # check response status
        if "status" not in jresp or jresp['status'] != "success":
            if "message" in jresp:
                raise ClientError(ClientErrorCategory.SERVICE, f"Service Request Unsuccessful {jresp['status']}: {jresp['message']}")
            raise ClientError(ClientErrorCategory.SERVICE, f"Service Request Unsuccessful {jresp['status']}.")
        # get the endpoint
        if "endpoint" not in jresp or "port" not in jresp:
            raise ClientError(ClientErrorCategory.SERVICE, f"Service Response is Malformed: f{jresp}")
        # save and return it
        self._endpoint_id = jresp['endpoint']
        self._remote_port = jresp['port']
        return self._endpoint_id, self._remote_port

    def _ws_on_open(self, ws):
        pass

    def _ws_on_message(self, ws, message):
        # print(message)
        try:
            jmsg = json.loads(message)
        except json.JSONDecodeError:
            return
        # dispatch events
        if "event" in jmsg:
            if jmsg['event'] == "connect" and "src" in jmsg:
                if self._connect_callback is not None:
                    self._connect_callback(jmsg['src'])
            if jmsg['event'] == "data" and "src" in jmsg and "data" in jmsg:
                if self._recv_callback is not None:
                    try:
                        data = base64.standard_b64decode(jmsg['data'])
                    except:
                        return
                    self._recv_callback(jmsg['src'], data)
            if jmsg['event'] == "disconnect" and "src" in jmsg:
                if self._disconnect_callback is not None:
                    self._disconnect_callback(jmsg['src'])

    def _ws_on_error(self, ws, error):
        pass

    def _ws_on_close(self, ws):
        pass

    def connect(self, on_connect, on_recv, on_disconnect):
        # make sure we have an endpoint
        if self._endpoint_id is None:
            raise ClientError(ClientErrorCategory.USAGE, "Can't connect without an endpoint_id, provide one at construction, or call get_endpoint().")
        # make sure we have an on_recv callback
        if on_recv is None:
            raise ClientError(ClientErrorCategory.USAGE, "on_recv callback must be provided, with the structure on_recv(source, data).")
        self._recv_callback = on_recv
        # make sure we have an on_connect callback
        if on_connect is None:
            raise ClientError(ClientErrorCategory.USAGE, "on_connect callback must be provided, with the structure on_connect(source).")
        self._connect_callback = on_connect
        # make sure we have an on_disconnect callback
        if on_disconnect is None:
            raise ClientError(ClientErrorCategory.USAGE, "on_disconnect callback must be provided, with the structure on_disconnect(source).")
        self._disconnect_callback = on_disconnect
        # connect to the websocket
        self._ws = websocket.WebSocketApp(f"wss://{self._api_host}/ws/{self._endpoint_id}",
            on_open=self._ws_on_open,
            on_message=self._ws_on_message,
            on_error=self._ws_on_error,
            on_close=self._ws_on_close)
    
    def process_blocking(self):
        # make sure we have connected ws
        if self._ws is None:
            raise ClientError(ClientErrorCategory.USAGE, "Cannot process messages without an active connection, use connect() first.")
        # start and block
        self._ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
        rel.signal(2, rel.abort)  # Keyboard Interrupt
        rel.dispatch()
        
    def send(self, dest, data):
        # make sure we have connected ws
        if self._ws is None:
            raise ClientError(ClientErrorCategory.USAGE, "Cannot send data without an active connection, use connect() first.")
        # encode data, make a json and send it
        self._ws.send(json.dumps({
            "action": "send",
            "dst":  dest,
            "data": base64.standard_b64encode(data).decode()
        }))

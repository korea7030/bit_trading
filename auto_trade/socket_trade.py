import pytz
from websocket import WebSocketApp
from threading import Thread
import json
import time
from datetime import datetime


class UpbitReal:
    def __init__(self, request, callback=print):
        self.request = request
        self.callback = callback
        self.ws = WebSocketApp(
            url="wss://api.upbit.com/websocket/v1",
            on_message=lambda ws, msg: self.on_message(ws, msg),
            on_error=lambda ws, msg: self.on_error(ws, msg),
            on_close=lambda ws:     self.on_close(ws),
            on_open=lambda ws:     self.on_open(ws))
        self.running = False
    def on_message(self, ws, msg):
        msg = json.loads(msg.decode('utf-8'))
        msg['timestamp'] = datetime.fromtimestamp(msg['timestamp']/ 1000, tz=pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')
        self.callback(msg)
    def on_error(self, ws, msg):
        self.callback(msg)
    def on_close(self, ws):
        self.callback("closed")
        self.running = False
    def on_open(self, ws):
        th = Thread(target=self.activate, daemon=True)
        th.start()
    def activate(self):
        self.ws.send(self.request)
        while self.running:
            time.sleep(1)
        self.ws.close()
    def start(self):
        self.running = True
        self.ws.run_forever()

if __name__ == "__main__":
    request='[{"ticket":"test"},{"type":"ticker","codes":["KRW-BTC"]}]'
    real = UpbitReal(request=request)     
    real.start()
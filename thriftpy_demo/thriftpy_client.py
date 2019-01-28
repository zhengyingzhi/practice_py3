# -*-coding:utf-8-*-

import json
import thriftpy
from thriftpy.rpc import client_context, make_client


API_KEY = "123ABC321CBA"

################################################################################
# !official demo!
# 读入thrift文件,module_name最好与server端保持一致（也可不一致）
pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")

def main_ping():
    with client_context(pp_thrift.PingService, '127.0.0.1', 24680) as cli:
        pong = cli.ping()
        print("rsp:", pong)
################################################################################


class TradeClient(object):
    def __init__(self, api_key, host, port):
        self.api_key = api_key
        trade_thrift = thriftpy.load("traderpc.thrift", module_name="trade_thrift")
        self.client = make_client(trade_thrift.TradeRpcService, host, port, timeout=5000)

    def __enter__(self):
        print("TradeClient enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("TradeClient exit")
        self.close()
        return self

    def close(self):
        self.client.close()

    def login(self, username, password, **kwargs):
        return self._invoke('login', username=username, password=password, **kwargs)

    def send_order(self, **kwargs):
        return self._invoke('send_order', **kwargs)

    def position(self, **kwargs):
        return self._invoke('position', **kwargs)

    def _invoke(self, method, **kwargs):
        params = json.dumps(kwargs)
        output = self.client.invoke(self.api_key, method, params)
        return json.loads(output)

def main_trade():
    cli = TradeClient(API_KEY, "127.0.0.1", 24680)
    rv = cli.login("038313", "123123")
    print("login rv:", rv)

    rv = cli.send_order(symbol="000006.SZ", price=16.6, volume=600)
    print("send_order rv:", rv)

    rv = cli.position()
    print("position rv:", rv)

if __name__ == "__main__":
    # main_ping()
    main_trade()

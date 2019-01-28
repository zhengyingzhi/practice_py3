# -*-coding:utf-8-*-

import json
import thriftpy
from thriftpy.rpc import make_server

API_KEY = "123ABC321CBA"

################################################################################
# !official demo!
pp_thrift = thriftpy.load("pingpong.thrift", module_name="pp_thrift")

# 实现.thrift文件定义的接口
class Dispatcher(object):
    def ping(self):
        print("ping pong!")
        return 'pong'

def main_pong():
    # 定义监听的端口和服务
    server = make_server(pp_thrift.PingService, Dispatcher(), '127.0.0.1', 24680)
    print("serving...")
    server.serve()
################################################################################

def gen_success_result(data):
    return {'success': True, 'data': data}

def gen_fail_result(data):
    return {'success': False, 'data': data}

class TradeServer(object):
    def __init__(self):
        self.methods = {
            "login": self.login,
            "send_order": self.send_order,
            "position": self.position
        }

    def login(self, username, password):
        """登录请求"""
        print("server login()", username, password)
        return gen_success_result("ok")

    def send_order(self, symbol, price, volume):
        """委托请求"""
        print("server send_order()", symbol, price, volume)
        return gen_success_result("oid")

    def position(self):
        """持仓查询"""
        print("server position()")
        return gen_success_result("pos")

    def invoke(self, api_key, method, input):
        """rpc func"""
        if api_key != API_KEY:
            raise Exception("invalid api key:{}".format(api_key))
        kwargs = json.loads(input)
        print('invoke %s, %s ..' % (method, kwargs))

        method = self.methods.get(method, None)
        if method is None:
            raise Exception('unkonwn method: %s' % method)

        output_data = method(**kwargs)
        output = json.dumps(output_data)
        return output

def start_trade_server(thrift_file="traderpc.thrift"):
    trade_thrift = thriftpy.load(thrift_file, module_name="trade_thrift")
    print('trade server running...')
    server = make_server(trade_thrift.TradeRpcService, TradeServer(), '0.0.0.0', 24680, client_timeout=30000)
    server.serve()
    print('trade server stopped')

if __name__ == "__main__":
    # main_pong()
    start_trade_server()

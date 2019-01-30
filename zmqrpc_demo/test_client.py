# encoding: UTF-8

from __future__ import print_function
from time import sleep

from zmq_rpc import RpcClient


class MockOrder(object):
    def __init__(self, accountID, symbol, volume, price, userID):
        self.accountID = accountID
        self.symbol = symbol
        self.volume = volume
        self.price = price
        self.userID = userID

    def __repr__(self):
        return "MockOrder({})".format(str(self.__dict__))

    def to_dict(self):
        return self.__dict__

########################################################################
class TestClient(RpcClient):
    """RPC测试客户端"""

    def __init__(self, req_ip, req_port, sub_addr, sub_port):
        """Constructor"""
        super(TestClient, self).__init__(req_ip, req_port, sub_addr, sub_port)

    def callback(self, topic, data):
        """回调函数实现"""
        print('client received topic:', topic, ', data:', data)


def main(req_ip, req_port, sub_addr='localhost', sub_port=0):
    tc = TestClient(req_ip, req_port, sub_addr, sub_port)
    tc.subscribe_topic('')
    tc.start()

    while 1:
        cmd = input("input cmd:")
        if cmd == "get_order":
            ret = tc.get_order()
            print('get_order() ret:{}'.format(ret))
        elif cmd == "get_orders":
            ret = tc.get_orders()
            print('get_orders() ret:{}'.format(ret))
        elif cmd == 'q' or cmd == 'e':
            break
        else:
            print(tc.add(1, 3))

if __name__ == '__main__':
    req_port = 24680
    sub_port = 24682

    main('localhost', req_port, 'localhost', sub_port)
    try:
        main('localhost', req_port, 'localhost', sub_port)
    except Exception:
        print('exception')

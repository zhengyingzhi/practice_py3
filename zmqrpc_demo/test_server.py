# encoding: UTF-8

from __future__ import print_function
from time import sleep, time

from zmq_rpc import RpcServer

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
class TestServer(RpcServer):
    """RPC测试服务器"""

    def __init__(self, rep_ip, rep_port, pub_ip, pub_port):
        """Constructor"""
        super(TestServer, self).__init__(rep_ip, rep_port, pub_ip, pub_port)

        # 注册rpc函数
        self.register(self.add)
        self.register(self.get_order)
        self.register(self.get_orders)

    def add(self, a, b):
        """测试函数"""
        print('receiving: add(%s, %s)' % (a,b))
        return a + b

    def get_order(self):
        print('SERVER: get_order()')
        order1 = MockOrder("038313", "rb1901", 1, 4001, "HFTrading")
        return order1

    def get_orders(self):
        print('SERVER: get_orders()')
        order1 = MockOrder("038313", "rb1901", 1, 4001, "HFTrading")
        order2 = MockOrder("038313", "IF1812", 2, 3002, "DoubleMA")
        return [order1, order2]

if __name__ == '__main__':
    rep_port = 24680
    pub_port = 24682

    ts = TestServer('*', rep_port, '*', pub_port)
    ts.start()

    while 1:
        s = input("input...")
        content = 'current server time is %s' % time()
        print(content)
        ts.publish(str('test'), str(content))
        sleep(2)

#-*- coding:utf-8 -*-

from threading import Lock

try:
    # Py2.7
    from xmlrpclib import ServerProxy
    from httplib import CannotSendRequest, ResponseNotReady
except ImportError:
    # Py 3.5
    from xmlrpc.client import ServerProxy
    from http.client import CannotSendRequest, ResponseNotReady


class RpcClient:
    def __init__(self):
        self.lock = Lock()
        self.api_proxy = None

    def InitRemote(self, server_ip, server_port):
        # if self.api_proxy:
        #     return

        self.api_proxy = ServerProxy("http://%s:%d/" % (server_ip, server_port), allow_none=True, encoding='utf-8')
        if not self.api_proxy.GW_Ping():
            raise Exception("Ping doesn't return True")

    def InitSession(self):
        """初始化会话信息"""
        return self.SendHard(self.api_proxy.GW_InitSession, tuple())

    def UserLogin(self, session, account_id, account_pwd):
        """请求登录"""
        return self.SendHard(self.api_proxy.GW_UserLogin, (session, account_id, account_pwd))

    def Disconnect(self, session):
        """断开会话信息"""
        return self.SendHard(self.api_proxy.GW_Disconnect, (session,))

    def SendOrder(self, session, trade_acct, trade_accttype, params):
        """发送订单"""
        return self.SendHard(self.api_proxy.GW_SendOrder, (session, trade_acct, trade_accttype, params))

    def SendHeartbeat(self, session):
        """发送心跳"""
        return self.SendHard(self.api_proxy.GW_HeartBeat, (session, ))

    def SendHard(self, remoteCall, argList):
        """远程请求"""
        try:
            return remoteCall(*argList)
        except CannotSendRequest:
            print("SendHard: CannotSendRequest %s %s" % (remoteCall.__name__, str(argList)))
        except ResponseNotReady:
            print("SendHard: CannotSendRequest %s %s" % (remoteCall.__name__, str(argList)))


if __name__ == "__main__":
    rpccli = RpcClient()
    rpccli.InitRemote("127.0.0.1", 13579)

    session = rpccli.InitSession()
    print("session:{}".format(session))

    rv = rpccli.UserLogin(session, "yizhe", "123321")
    print("UserLogin rv:{}".format(rv))

    order = {"symbol": "000001.SZ", "volume": 1000, "price": 10.98, "side": "1", "order_type":"MKT"}
    rv = rpccli.SendOrder(session, "yizhe", "0", order)
    print("SendOrder rv:{}".format(rv))

    rv = rpccli.Disconnect(session)
    print("Disconnect rv:{}".format(rv))

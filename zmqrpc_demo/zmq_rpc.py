# encoding: UTF-8
# 此文件实现了基于ZMQ通信模型的RPC服务端和客户端的封装逻辑
# 

import threading
import traceback
import signal

import zmq

from json import dumps, loads

try:
    from msgpack import packb, unpackb
except ImportError:
    pass

try:
    import cPickle
    pDumps = cPickle.dumps
    pLoads = cPickle.loads
except ImportError:
    import pickle
    pDumps = pickle.dumps
    pLoads = pickle.loads


# 实现Ctrl-c中断recv
signal.signal(signal.SIGINT, signal.SIG_DFL)


########################################################################
class RpcObject(object):
    """
    RPC对象

    提供对数据的序列化打包和解包接口，目前提供了json、msgpack、cPickle三种工具。

    msgpack：性能更高，但通常需要安装msgpack相关工具；
    json：性能略低但通用性更好，大部分编程语言都内置了相关的库。
    cPickle：性能一般且仅能用于Python，但是可以直接传送Python对象，非常方便。

    因此建议尽量使用msgpack，如果要和某些语言通讯没有提供msgpack时再使用json，
    当传送的数据包含很多自定义的Python对象时建议使用cPickle。

    如果希望使用其他的序列化工具也可以在这里添加。
    """

    #----------------------------------------------------------------------
    def __init__(self, pack_type="pickle"):
        """Constructor"""
        # self.use_json()
        # self.use_msgpack()
        self.use_pickle()

    def pack(self, data):
        """打包"""
        pass

    def unpack(self, data):
        """解包"""
        pass

    def __json_pack(self, data):
        """使用json打包"""
        s = dumps(data)
        return s.encode('utf-8')

    def __json_unpack(self, data):
        """使用json解包"""
        data = data.decode('utf-8')
        return loads(data)

    def __msgpack_pack(self, data):
        """使用msgpack打包"""
        return packb(data)

    def __msgpack_unpack(self, data):
        """使用msgpack解包"""
        return unpackb(data)

    def __pickle_pack(self, data):
        """使用cPickle打包"""
        return pDumps(data)

    def __pickle_unpack(self, data):
        """使用cPickle解包"""
        return pLoads(data)

    def use_json(self):
        """使用json作为序列化工具"""
        self.pack = self.__json_pack
        self.unpack = self.__json_unpack

    def use_msgpack(self):
        """使用msgpack作为序列化工具"""
        self.pack = self.__msgpack_pack
        self.unpack = self.__msgpack_unpack

    def use_pickle(self):
        """使用cPickle作为序列化工具"""
        self.pack = self.__pickle_pack
        self.unpack = self.__pickle_unpack


########################################################################
class RpcServer(RpcObject):
    """RPC服务器"""

    def __init__(self, rep_ip, rep_port, pub_ip='localhost', pub_port=0):
        """Constructor
        rep_address = 'tcp://localhost:24680'
        pub_address = 'tcp://localhost:24682'
        """
        super(RpcServer, self).__init__()

        # 保存功能函数的字典，key是函数名，value是函数对象
        self.__functions = {}

        # zmq相关
        self.__context = zmq.Context()

        rep_address = 'tcp://{}:{}'.format(rep_ip, rep_port)
        # print("+++", rep_address)
        self.__sock_rep = self.__context.socket(zmq.REP)    # 请求回应socket
        self.__sock_rep.bind(rep_address)

        if pub_ip and pub_port:
            pub_address = 'tcp://{}:{}'.format(pub_ip, pub_port)
            # print("+++", pub_address)
            self.__sock_pub = self.__context.socket(zmq.PUB)# 数据广播socket
            self.__sock_pub.bind(pub_address)
            self.__pub_lock = threading.Lock()              # 防止多线程publish
        else:
            self.__sock_pub = None

        # 工作线程相关
        self.__active = False                               # 服务器的工作状态
        self.__thread = threading.Thread(target=self.run)   # 服务器的工作线程

    def start(self):
        """启动服务器"""
        self.__active = True

        if not self.__thread.isAlive():
            self.__thread.start()

    def stop(self, join=False):
        """停止服务器"""
        self.__active = False

        if join and self.__thread.isAlive():
            self.__thread.join()

    def run(self):
        """服务器线程运行函数"""
        while self.__active:
            if not self.__sock_rep.poll(1000):
                continue

            # 从请求响应socket收取请求数据
            reqb = self.__sock_rep.recv()

            # 序列化解包
            req = self.unpack(reqb)

            # 获取函数名和参数
            name, args, kwargs = req
            #print('> btrpc server run() name:{}, args:{}, kwars:{}'.format(name, args, kwargs))

            # 获取引擎中对应的函数对象，并执行调用，如果有异常则捕捉后返回
            try:
                func = self.__functions[name]
                r = func(*args, **kwargs)
                rep = [True, r]
            except Exception as e:
                rep = [False, traceback.format_exc()]

            # 序列化打包
            repb = self.pack(rep)

            # 通过请求响应socket返回调用结果
            self.__sock_rep.send(repb)

    def publish(self, topic, data):
        """
        广播推送数据
        topic：主题内容（注意必须是ascii编码）
        data：具体的数据
        """
        # 序列化数据
        datab = self.pack(data)

        # py3's send_multipart()
        if isinstance(topic, str):
            topic = topic.encode('utf-8')

        # 通过广播socket发送数据
        # self.__pub_lock.acquire()
        self.__sock_pub.send_multipart([topic, datab])
        # self.__pub_lock.release()

    def register(self, func):
        """注册函数"""
        self.__functions[func.__name__] = func


########################################################################
class RpcClient(RpcObject):
    """RPC客户端"""

    def __init__(self, req_ip, req_port, sub_addr='localhost', sub_port=0):
        """Constructor
        req_address = 'tcp://localhost:24680'
        sub_address = 'tcp://localhost:24682'
        """
        super(RpcClient, self).__init__()

        # zmq相关
        self.__req_address = 'tcp://{}:{}'.format(req_ip, req_port)
        self.__sub_address = 'tcp://{}:{}'.format(sub_addr, sub_port)

        self.__context = zmq.Context()
        self.__sock_req = self.__context.socket(zmq.REQ)        # 请求发出socket
        if sub_addr and sub_port:
            self.__sock_sub = self.__context.socket(zmq.SUB)    # 广播订阅socket

            # 工作线程相关，用于处理服务器推送的数据
            self.__active = False                                   # 客户端的工作状态
            self.__thread = threading.Thread(target=self.run)       # 客户端的工作线程
        else:
            self.__sock_sub = None
            self.__active = False
            self.__thread = None

    def __getattr__(self, name):
        """实现远程调用功能"""
        # 执行远程调用任务
        def dorpc(*args, **kwargs):
            #print('>RpcClient dorpc() name:{}, args:{}, kwargs:{}'.format(name, args, kwargs))
            # 生成请求
            req = (name, args, kwargs)

            # 序列化打包请求
            reqb = self.pack(req)

            # 发送请求并等待回应
            self.__sock_req.send(reqb)
            repb = self.__sock_req.recv()

            # 序列化解包回应
            rep = self.unpack(repb)

            # 若正常则返回结果，调用失败则触发异常
            if rep[0]:
                return rep[1]
            else:
                raise RemoteException(rep[1])

        return dorpc

    def start(self):
        """启动客户端"""
        # 连接服务器
        self.__sock_req.connect(self.__req_address)

        if self.__sock_sub:
            self.__sock_sub.connect(self.__sub_address)

            self.__active = True

            if not self.__thread.isAlive():
                self.__thread.start()

    def stop(self):
        """停止客户端"""
        if self.__active:
            self.__active = False

            if self.__thread.isAlive():
                self.__thread.join()

    def run(self):
        """客户端线程运行函数"""
        while self.__active:
            if not self.__sock_sub.poll(1000):
                continue

            # 从订阅socket收取广播数据
            topic, datab = self.__sock_sub.recv_multipart()

            # 序列化解包
            data = self.unpack(datab)

            # 调用回调函数处理
            self.callback(topic, data)

    def callback(self, topic, data):
        """回调函数，必须由用户实现"""
        raise NotImplementedError

    def subscribe_topic(self, topic):
        """
        订阅特定主题的广播数据
        可以使用topic=''来订阅所有的主题
        注意topic必须是ascii编码
        """
        self.__sock_sub.setsockopt(zmq.SUBSCRIBE, topic.encode('utf-8'))


########################################################################
class RemoteException(Exception):
    """RPC远程异常"""

    def __init__(self, value):
        """Constructor"""
        self.__value = value

    def __str__(self):
        """输出错误信息"""
        return self.__value

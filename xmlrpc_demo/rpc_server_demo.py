#-*- coding:utf-8 -*-

import time
import logbook
from logbook.more import ColorizedStderrHandler
from uuid import uuid4
from datetime import datetime
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

# set as local time format (default is utc)
logbook.set_datetime_format('local')

# std_handler = StreamHandler(sys.stdout, level='INFO')
std_handler = ColorizedStderrHandler(bubble=True, level='INFO')
std_handler.push_application()

file_name = "rpc_server_{}.log".format(datetime.now().strftime("%Y-%m-%d"))
fp_handler = logbook.FileHandler(file_name, bubble=True, level='INFO')
fp_handler.push_application()

log = logbook.Logger("rpc_svr")

g_worker_proxies= dict()
g_order_no = 0


class WorkerProxy:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.last_heartbeat_timestamp = time.time()
        self.logined = False

    def process_single_order(self, trade_acct, trade_accttype, order_data):
        """处理单笔委托请求"""
        g_order_no += 1
        return g_order_no

def GW_InitSession():
    new_worker_id = uuid4().hex
    log.info("GW_InitSession net_work_id:{}".format(new_worker_id))

    worker_proxy = WorkerProxy(new_worker_id)
    g_worker_proxies[new_worker_id] = worker_proxy
    return new_worker_id

def GW_UserLogin(worker_id, *args):
    worker_proxy = g_worker_proxies.get(worker_id)
    if not worker_proxy:
        log.error("GW_UserLogin unknown worker_id:{}".format(worker_id))
        return -1

    log.info("GW_UserLogin args:\n{}".format(args))
    username = args[0]
    password = args[1]
    return 0

def GW_Disconnect(worker_id, *args):
    worker_proxy = g_worker_proxies[worker_id]
    log.info("GW_Disconnect Worker %s." % worker_proxy.worker_id)
    if worker_id in g_worker_proxies:
        del g_worker_proxies[worker_id]

    return 0

def GW_SendOrder(worker_id, *args):
    worker_proxy = g_worker_proxies.get(worker_id)
    if not worker_proxy:
        log.error("GW_SendOrder unknown worker_id:{}".format(worker_id))
        return -1

    log.info("GW_SendOrder args:\n{}".format(args))
    trade_acct = args[0]
    trade_accttype = args[1]
    order_data = args[2]
    return worker_proxy.process_single_order(trade_acct, trade_accttype, order_data)

def GW_HeartBeat(worker_id, *args):
    worker_proxy = g_worker_proxies.get(worker_id)
    if not worker_proxy:
        log.error("GW_HeartBeat unknown worker_id:{}".format(worker_id))
        return -1

    worker_proxy.last_heartbeat_timestamp = time.time()

def GW_Ping():
    # log.info("pingpingping")
    return True


'''-----------------------------
'''
def check_heartbeat():
    while True:
        time.sleep(10)
        try:
            for worker_proxy in g_worker_proxies.values():
                print("worker_proxy=", worker_proxy)
                if time.time() - worker_proxy.last_heartbeat_timestamp > 60:
                    log.info("Worker heartbeat timeout! id=%s" % (worker_proxy.worker_id,))
                    GW_Disconnect(worker_proxy.worker_id)
        except Exception as e:
            print("check_heartbeat: Exception Ignored.", e)

if __name__ == "__main__":
    gw_port = 13579
    server=SimpleXMLRPCServer(("0", gw_port), allow_none=True)
    log.info("[RPC Server] bind to port {}...".format(gw_port))

    '''rpc functions'''
    server.register_function(GW_InitSession)
    server.register_function(GW_UserLogin)
    server.register_function(GW_Disconnect)
    server.register_function(GW_SendOrder)
    server.register_function(GW_HeartBeat)
    server.register_function(GW_Ping)

    # heartbeat thread
    # Thread(target=check_heartbeat, daemon=True).start()

    server.serve_forever(poll_interval=1)

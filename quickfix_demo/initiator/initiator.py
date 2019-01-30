# -*- coding: utf-8 -*-
import sys
import quickfix as fix
import quickfix44 as fix44

import time
import logging
import argparse
from logger import setup_logger

setup_logger('FIXC', 'Logs/initiator_message.log')
log = logging.getLogger('FIXC')

# configured
__SOH__ = chr(1)


class Application(fix.Application):
    """FIX Client Application"""

    def onCreate(self, sessionID):
        log.info("onCreate:{}".format(sessionID))
        self.sessionID = sessionID
        return

    def onLogon(self, sessionID):
        log.info("onLogon:{}".format(sessionID))
        self.sessionID = sessionID
        return

    def onLogout(self, sessionID): 
        log.info("onLogout:{}".format(sessionID))
        return

    def toAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info("toAdm >> (%s)" % msg)
        return

    def fromAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info("fromAdm >> (%s)" % msg)
        return

    def toApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info("toApp >> (%s)" % msg)
        return

    def fromApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info("fromApp >> (%s)" % msg)
        self.onMessage(message, sessionID)
        return

    def onMessage(self, message, sessionID):
        """on Message"""
        pass

    def make_single_order(self, order_id, symbol, qty):
        account = "YIZHE0"
        order = fix44.NewOrderSingle()
        order.setField(fix.Account(account))
        order.setField(fix.ClOrdID(order_id))
        order.setField(fix.Symbol(symbol))
        order.setField(fix.Side("1"))
        order.setField(fix.OrdType("U"))
        order.setField(fix.OrderQty(qty))
        order.setField(fix.Price(49))
        return order

    def run(self):
        """Run"""
        time.sleep(1)
        symbols = ["000110.SZ", "600660.SH"]
        i = 0
        while 1:
            time.sleep(1.5)
            i += 1
            cmd = input("input cmd: order|cancel|e(q):")
            if cmd == 'e' or cmd == 'q':
                break
            elif cmd == 'order':
                order_id = str(i)
                symbol = symbols[i % 2]
                qty = ((i % 10) + 1) * 100
                order = self.make_single_order(order_id, symbol, qty)
                fix.Session.sendToTarget(order, self.sessionID)
            elif cmd == 'cancel':
                pass

def main(file_name):
    """Main"""
    log.info("-->> initiator main file_name:{}".format(file_name))
    try:
        settings = fix.SessionSettings(file_name)
        application = Application()
        storefactory = fix.FileStoreFactory(settings)
        logfactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storefactory, settings, logfactory)
        application.initiator = initiator

        initiator.start()
        application.run()
        initiator.stop()
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
        initiator.stop()
        sys.exit()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='FIX Client')
    parser.add_argument('file_name', type=str, help='Name of configuration file')
    args = parser.parse_args()
    main(args.file_name)

# -*- coding: utf-8 -*-
import time

import quickfix as fix
import quickfix44 as fix44

import argparse
import logging
from logger import setup_logger

setup_logger('FIXS', 'Logs/executor_message.log')
log = logging.getLogger('FIXS')

# const variable
__SOH__ = chr(1)


class Application(fix.Application):
    """FIX Acceptor Application"""
    orderID = 1
    execID = 1

    def __init__(self):
        super(Application, self).__init__()

    def genOrderID(self):
        Application.orderID += 1
        return repr(Application.orderID)

    def genExecID(self):
        Application.execID += 1
        return str(Application.execID)

    def onCreate(self, sessionID):
        log.info('onCreate:{}'.format(sessionID))
        return

    def onLogon(self, sessionID):
        log.info('onLogon:{}'.format(sessionID))
        return

    def onLogout(self, sessionID):
        log.info('onLogout:{}'.format(sessionID))
        return

    def toAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info('toAdm sessionID:{}, message:{}'.format(sessionID, ))
        sndTime = fix.SendingTime()
        message.getHeader().getField(sndTime)
        print((sndTime.getString()))
        return

    def fromAdmin(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info('fromAdm sessionID:{}, message:{}'.format(sessionID, msg))
        return

    def toApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info('toApp sessionID:{}, message:{}'.format(sessionID, msg))
        return

    def fromApp(self, message, sessionID):
        msg = message.toString().replace(__SOH__, "|")
        log.info('fromApp sessionID:{}, message:{}'.format(sessionID, msg))
        beginString = fix.BeginString()
        msgType = fix.MsgType()
        message.getHeader().getField(beginString)
        message.getHeader().getField(msgType)

        if msgType.getValue() == fix.MsgType_NewOrderSingle:
            log.info("********** fromApp [NewOrderSingle] MsgType **********")
            self.new_order(message, beginString, sessionID)
        if msgType.getValue() == fix.MsgType_OrderCancelRequest:
            log.info("********** fromApp [OrderCancelRequest] MsgType **********")
            self.cancel(message, sessionID)

    def cancel(self, message, sessionID):
        symbol = fix.Symbol()
        side = fix.Side()
        orderQty = fix.OrderQty()
        clOrdID = fix.ClOrdID()
        org = fix.OrigClOrdID()
        message.getField(symbol)
        message.getField(side)
        message.getField(orderQty)
        message.getField(clOrdID)
        message.getField(org)
        log.info("cancel:\nsymbol:{},side:{},orderQty:{},clOrdID:{},org:{} -----"\
            .format(symbol, side, orderQty, clOrdID, org))

        cancel = fix44.OrderCancelReject()
        cancel.setField(clOrdID)
        cancel.setField(fix.OrderID(self.genOrderID()))
        cancel.setField(fix.OrdStatus(fix.OrdStatus_NEW))
        cancel.setField(fix.OrigClOrdID(org.getValue()))
        cancel.setField(fix.Text('order completed'))
        cancel.setField(fix.TransactTime())
        cancel.setField(fix.CxlRejReason(fix.CxlRejReason_BROKER))
        cancel.setField(fix.CxlRejResponseTo(fix.CxlRejResponseTo_ORDER_CANCEL_REQUEST))

        fix.Session.sendToTarget(cancel, sessionID)

    def new_order(self, message, beginString, sessionID):
        symbol = fix.Symbol()
        side = fix.Side()
        ordType = fix.OrdType()
        orderQty = fix.OrderQty()
        price = fix.Price(50)
        clOrdID = fix.ClOrdID()

        message.getField(ordType)
        message.getField(symbol)
        message.getField(side)
        message.getField(orderQty)
        message.getField(price)
        message.getField(clOrdID)
        log.info("new_order:\nordType:{},symbol:{},side:{},orderQty:{},price:{},clOrdID:{} -----"\
            .format(ordType, symbol, side, orderQty, price, clOrdID))

        executionReport = fix.Message()
        executionReport.getHeader().setField(beginString)
        executionReport.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))

        executionReport.setField(fix.TransactTime())
        executionReport.setField(fix.OrderID(self.genOrderID()))
        executionReport.setField(fix.ExecID(self.genExecID()))
        executionReport.setField(fix.OrdStatus(fix.OrdStatus_NEW))
        executionReport.setField(symbol)
        executionReport.setField(side)
        executionReport.setField(fix.CumQty(orderQty.getValue()))
        executionReport.setField(fix.AvgPx(price.getValue()))
        executionReport.setField(fix.LastShares(orderQty.getValue()))
        executionReport.setField(fix.LastPx(price.getValue()))
        executionReport.setField(clOrdID)
        executionReport.setField(orderQty)
        executionReport.setField(fix.ExecType(fix.ExecType_NEW))
        executionReport.setField(fix.LeavesQty(orderQty.getValue()))

        try:
            fix.Session.sendToTarget(executionReport, sessionID)
            time.sleep(1)
            if ordType.getValue() == fix.OrdType_MARKET:
                executionReport.setField(fix.OrdStatus(fix.OrdStatus_FILLED))
                executionReport.setField(fix.ExecType(fix.ExecType_TRADE))
                fix.Session.sendToTarget(executionReport, sessionID)

        except fix.SessionNotFound as e:
            return


def main(file_name):
    """run an acceptor application service"""
    log.info("-->> executor main file_name:{}".format(file_name))
    try:
        settings = fix.SessionSettings(file_name)
        application = Application()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)

        acceptor = fix.SocketAcceptor(application, storeFactory, settings, logFactory)
        log.info('-->> starting acceptor')
        acceptor.start()

        while 1:
            time.sleep(1)
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FIX Acceptor')
    parser.add_argument('file_name', type=str, help='Name of configuration file')
    args = parser.parse_args()
    main(args.file_name)    # 'executor.ini'

# -*- coding:utf-8 -*-
# 一个简单的python3线程模型

from __future__ import print_function

import time
from queue import Queue, Empty
from threading import Thread


class PCData:
    def __init__(self, type_, data):
        self.type_ = type_
        self.data = data

# 多线程生产者-消费者模型
class ProducerConsumer(object):
    def __init__(self):
        self.__queue = Queue()
        self.__active = False
        self.__thread = Thread(target=self.__run)

        self.__proc_num = 0
        self.__data_num = 0

    def start(self):
        """启动线程"""
        if not self.__active:
            self.__active = True
            self.__thread.start()

    def stop(self):
        """停止线程"""
        if self.__active:
            self.__active = False
            self.__queue.put(None)
            self.__thread.join()

    def get_qsize(self):
        """获取队列大小"""
        return self.__queue.qsize()

    def put_data(self, type_, data):
        """放入数据"""
        self.__data_num += 1
        pcd = PCData(type_, data)
        self.__queue.put(pcd)

    def process_data(self, type_, data):
        """处理数据"""
        raise NotImplementedError("not process_data!")

    def __run(self):
        """线程函数"""
        while self.__active:
            try:
                pcd = self.__queue.get(block = True, timeout = 1)  # 获取事件的阻塞时间设为1秒
                if pcd is None:
                    break

                self.process_data(pcd.type_, pcd.data)
                self.__proc_num += 1
            except Empty:
                pass

################################################################
# test
class DataSaver(ProducerConsumer):
    def __init__(self):
        super(DataSaver, self).__init__()

    def process_data(self, type_, data):
        print("process_data type:{}, data:{}".format(type_, data))

def main():
    ds = DataSaver()
    ds.start()

    for i in range(5):
        ds.put_data(i, i + 5)

    time.sleep(1.0)
    ds.stop()
    print("tested!")

if __name__ == '__main__':
    main()

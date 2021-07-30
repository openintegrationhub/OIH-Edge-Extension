import threading
import time

lockobj = threading.Condition()
test = "test"


class A(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(1)
            lockobj.acquire()
            print("Thread A hat die Konrolle")
            time.sleep(1)
            lockobj.notify_all()
            lockobj.release()


class B(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(1)
            lockobj.acquire()
            print("Thread B hat die Konrolle")
            time.sleep(1)
            lockobj.notify_all()
            lockobj.release()


a = A()
b = B()
#a.start()
#b.start()
#a.join()
#b.join()


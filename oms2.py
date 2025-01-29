import threading
import time
from datetime import datetime, timedelta
from collections import deque

class Logon:
    def __init__(self, username, password):
        self.username = username

class Logout:
    def __init__(self, username):
        self.username = username

class OrderRequest:
    def __init__(self, symbol_id, price, qty, side, order_id):
        self.m_symbolId = symbol_id
        self.m_price = price
        self.m_qty = qty
        self.m_side = side
        self.m_orderId = order_id

class RequestType:
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType:
    Unknown = 0
    Accept = 1
    Reject = 2

class OrderResponse:
    def __init__(self, order_id, response_type):
        self.m_orderId = order_id
        self.m_responseType = response_type

class OrderManagement:
    def __init__(self, start_time, end_time, mos):
        self.start_time = start_time
        self.end_time = end_time
        self.max_orders_per_second = mos
        self.order_queue = deque()
        self.order_lock = threading.Lock()
        self.response_log = []
        self.sent_orders = {}  # Track sent orders by orderId
        self.stop_event = threading.Event()

        # Start the order processing thread
        self.processing_thread = threading.Thread(target=self.process_orders)
        self.processing_thread.start()

    def is_within_time_window(self):
        now = datetime.now()
        return self.start_time <= now.time() <= self.end_time

    def sendLogon(self):
        print("Logon message sent.")

    def sendLogout(self):
        print("Logout message sent.")

    def send(self, request):
        print(f"Order sent to exchange: {request.m_orderId}")
        self.sent_orders[request.m_orderId] = time.time()

    def process_orders(self):
        while not self.stop_event.is_set():
            with self.order_lock:
                for _ in range(min(len(self.order_queue), self.max_orders_per_second)):
                    order = self.order_queue.popleft()
                    self.send(order)
            time.sleep(1)  

    def onData(self, request):
        if not self.is_within_time_window():
            print(f"Order rejected (outside time window): {request.m_orderId}")
            return

        with self.order_lock:
            for queued_order in self.order_queue:
                if queued_order.m_orderId == request.m_orderId:
                    if request.m_price == 0 and request.m_qty == 0:
                        self.order_queue.remove(queued_order)
                        print(f"Order cancelled: {queued_order.m_orderId}")
                        return
                    else:
                        queued_order.m_price = request.m_price
                        queued_order.m_qty = request.m_qty
                        print(f"Order modified: {queued_order.m_orderId}")
                        return
            
            if isinstance(request, OrderRequest):
                self.order_queue.append(request)
                print(f"Order queued: {request.m_orderId}")

    def onDataResponse(self, response):
        order_id = response.m_orderId
        if order_id in self.sent_orders:
            latency = time.time() - self.sent_orders[order_id]
            self.response_log.append((response.m_responseType, order_id, latency))
            print(f"Response received: {response.m_responseType}, Order ID: {order_id}, Latency: {latency:.2f} seconds")
        else:
            print(f"Response received for unknown order: {response.m_orderId}")

    def stop(self):
        self.stop_event.set()
        self.processing_thread.join()



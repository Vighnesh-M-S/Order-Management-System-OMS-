import unittest
from datetime import datetime
from oms2 import OrderManagement, OrderRequest, OrderResponse, ResponseType

class TestOrderManagement(unittest.TestCase):
    def setUp(self):
        start_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0).time()
        end_time = datetime.now().replace(hour=13, minute=0, second=0, microsecond=0).time()
        self.oms = OrderManagement(start_time, end_time, max_orders_per_second=2)

    def tearDown(self):
        self.oms.stop()

    def test_order_queuing(self):
        order = OrderRequest(101, 50.5, 10, 'B', 1)
        self.oms.onData(order)
        self.assertEqual(len(self.oms.order_queue), 1)

    def test_order_modification(self):
        order1 = OrderRequest(101, 50.5, 10, 'B', 1)
        self.oms.onData(order1)
        order2 = OrderRequest(101, 55.0, 15, 'B', 1)  # Modify order
        self.oms.onData(order2)
        self.assertEqual(self.oms.order_queue[0].m_price, 55.0)
        self.assertEqual(self.oms.order_queue[0].m_qty, 15)

    def test_order_cancellation(self):
        order1 = OrderRequest(101, 50.5, 10, 'B', 1)
        self.oms.onData(order1)
        cancel_order = OrderRequest(101, 0, 0, 'B', 1)  # Cancel order
        self.oms.onData(cancel_order)
        self.assertEqual(len(self.oms.order_queue), 0)  # Order should be removed

    def test_order_rejection_outside_time_window(self):
        self.oms.start_time = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0).time()
        self.oms.end_time = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0).time()
        order = OrderRequest(101, 50.5, 10, 'B', 1)
        self.oms.onData(order)
        self.assertEqual(len(self.oms.order_queue), 0)

    def test_order_response_processing(self):
        order = OrderRequest(101, 50.5, 10, 'B', 1)
        self.oms.onData(order)
        self.oms.send(order)
        response = OrderResponse(1, ResponseType.Accept)
        self.oms.onDataResponse(response)
        self.assertEqual(len(self.oms.response_log), 1)
    
    if __name__ == "__main__":
        unittest.main()

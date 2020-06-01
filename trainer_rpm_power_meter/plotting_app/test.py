import unittest
from wifi_client import WifiClient
from time import sleep


class test_WifiClient(unittest.TestCase):

    def setUp(self):
        self.wc = WifiClient()
        print()

    def test_open_connection(self):
        self.wc.connect()

    def test_check_connection(self):
        self.assertTrue(hasattr(self.wc, "connected"))

    def test_use_deque(self):
        vals = [0, 1, 5, 6]
        self.wc.rpm_deque.extend(vals)
        for v in vals:
            self.assertEqual(
                v, self.wc.rpm_deque.popleft()
            )

    def test_request_next_period(self):
        if not self.wc.connected:
            self.wc.connect()
        self.wc.send("1")
        while not self.wc.rpm_deque:
            sleep(0.05)
        print(self.wc.rpm_deque)

    def test_close_connection(self):
        if self.wc.connected:
            self.wc.close()

    # def test_send_message(self):
    #     self.wc.send_message()


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit:
        pass

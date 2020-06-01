#!/usr/bin/env python3

from ws4py.client.threadedclient import WebSocketClient
from struct import unpack
import asyncio


class WifiClient(WebSocketClient):
    """
    Class that act like a WifiClient
    in order to get rotation_time data from wireless sensor
    over wifi
    The WiFiClient class is meant to be run on its
    own thread in order to poll the WiFiServer
    (in this case an esp8266 wifi model micro controller)
    however, it can be run on its own if the poll method
    is modified.
    """

    host = "ws://192.168.1.50:81/"

    def __init__(self):
        """
        initalize the WiFiClient using the IPaddress
        """
        super().__init__(self.host)
        self.is_connected = False
        self.rotation_time = 0
        self.timeout = 1.0
        self.loop = asyncio.get_event_loop()

    def opened(self):
        """
        override of the super's opended method
        sets self's is_connected status to true
        """
        print("websocket opened...")
        self.is_connected = True

    def closed(self, code: int, reason=None):
        """
        override of the super's opended method
        sets self's is_connected status to false
        """
        self.is_connected = False
        print(
            f"""connection closed
            code: {code}
            reason: {reason}"""
        )

    def received_message(self, m):
        """
        override of the super's received_message method
        sets self's rotation_time value if received before timeout

        args:
            m: ws4py messages.text_message, or messages.binary_message
        """
        if m.is_binary:
            self._received = True  # signal that message was received
            micros = unpack('L', m.data)[0]
            self.rotation_time = micros

    async def comm_loop(self):
        """
        asyncio event loop to control the sending
        of a character to the esp8266 wifi moduel
        and receiving a binary unsigned long from the esp8266
        """
        self.send("c")
        self._received = False
        while not self._received:
            await asyncio.sleep(0.05)

    def poll(self):
        """
        implements the comm_loop with the timeout
        """
        print("starting poll...")
        while True:
            try:
                self.loop.run_until_complete(
                    asyncio.wait_for(self.comm_loop(), self.timeout)
                )
            except asyncio.TimeoutError:
                self.rotation_time = 0

import datetime
import socket
import threading
from typing import Callable
from msu_ssc.ssc_logging import create_logger
from msu_ssc.time_util import utc
from msu_ssc.udp_mux import _shutdown_socket, _str_to_tup, _tup_to_str


logger = create_logger(__file__, level="DEBUG")


class OneWayUdpProxyThread(threading.Thread):
    def __init__(
        self,
        *,
        source_tup: tuple[str, int],
        destination_tup: tuple[str, int],
        daemon: bool = True,
        name: str = "proxy",
        **kwargs,
    ):
        name += f"({_tup_to_str(source_tup)}->{_tup_to_str(destination_tup)})"

        super().__init__(
            name=name,
            daemon=daemon,
            **kwargs,
        )
        self.source_tup = source_tup
        self.destination_tup = destination_tup
        self.source_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.total_packets = 0
        self.total_bytes = 0

    # def target

    def run(self):
        # BIND
        _shutdown_socket(self.source_socket)
        self.source_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info(
            f"Attempting to bind to UDP socket {_tup_to_str(self.source_tup)} for receiving. [{self.name}]"
        )
        self.source_socket.bind(self.source_tup)
        logger.info(f"Successfully bound receiving socket. [{self.name}]")

        # SERVE FOREVER
        self._mux_start_time = utc()
        logger.info(
            f"Ready to begin proxying at {self._mux_start_time.isoformat(timespec='seconds', sep=' ')}. [{self.name}]"
        )
        while True:
            data, source_address = self.source_socket.recvfrom(4096)
            self.route_packet(
                data=data,
            )

    def route_packet(
        self,
        *,
        data: bytes,
        **kwargs,
    ) -> None:
        """Route a given packet to the destination (or modify it, or whatever). Default behavior is to
        simply forward the packet and log a message.

        Child classes should override this class to change proxying functionality. This method is always called
        with keyword-only arguments."""
        logger.debug(
            f"Received {len(data)} bytes. Forwarding to {self.destination_tup} [{self.name}]"
        )
        sent_bytes = self.source_socket.sendto(data, self.destination_tup)

        self.total_bytes += sent_bytes
        self.total_packets += 1


class BidirectionalUdpProxy:
    def __init__(
        self,
        *,
        server_tup: tuple[str, int],
        client_tup: tuple[str, int],
    ):
        self.server_tup = server_tup
        self.client_tup = client_tup

        self.server_proxy = OneWayUdpProxyThread(
            daemon=True,
            source_tup=server_tup,
            destination_tup=client_tup,
            name="server_proxy",
        )
        self.client_proxy = OneWayUdpProxyThread(
            daemon=True,
            source_tup=client_tup,
            destination_tup=server_tup,
            name="client_proxy",
        )

        self.server_proxy.start()
        self.client_proxy.start()

    def __repr__(self):
        return f"{self.__class__.__name__}({_tup_to_str(self.server_tup)}<->{_tup_to_str(self.client_tup)})"


if __name__ == "__main__":
    import time
    import sys

    proxy = BidirectionalUdpProxy(
        server_tup=("127.0.0.1", 8002),
        client_tup=("127.0.0.1", 8003),
    )
    logger.info(proxy)

    # proxy = OneWayUdpProxyThread(
    #     source_tup=("127.0.0.1", 8002),
    #     destination_tup=("127.0.0.1", 8007),
    #     daemon=True,
    # )
    # proxy.start()
    # logger.info(proxy)
    sleep_secs = 1000000
    logger.debug(f"Sleeping {sleep_secs:,} secs")
    time.sleep(sleep_secs)
    logger.warning(f"Done sleeping. Exiting")
    sys.exit(1)


class UdpProxy:
    def __init__(
        self,
        *,
        server: tuple[str, int],
        client: tuple[str, int],
        daemon=True,
        reuse_server: bool = True,
        reuse_client: bool = True,
    ):
        self.server_sock_tup = server
        self.client_sock_tup = client
        self.daemon = daemon
        self.reuse_server = reuse_server
        self.reuse_client = reuse_client

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._bound = False
        # self._received_packet_count = 0
        # self._received_bytes_count = 0
        # self._transmitted_packet_count = 0
        # self._transmitted_bytes_count = 0

        self.thread = threading.Thread(
            name=f"udp-proxy-{_tup_to_str(self.server_sock_tup)}-{_tup_to_str(self.client_sock_tup)}",
            daemon=self.daemon,
            target=self.start_proxy,
        )
        self.thread.start()

        pass

    pass

    def one_way_proxy_factory(
        self,
        source_socket: socket.socket,
        destination_socket: socket.socket,
        routing_function: Callable[
            [
                bytes,  # data
                tuple[str, int] | None,  # Source address
                socket.socket,  # source socket
                tuple[str, int] | None,  # destination address
            ],
            None,
        ],
    ) -> Callable[[None], None]:
        def proxy() -> None:
            while True:
                data, source_address = source_socket.recvfrom(4096)
                routing_function(
                    data,
                    source_address,
                    source_socket,
                    destination_socket,
                )

        return proxy

    def route_server_packet(
        self,
        payload_data: bytes,
        receive_socket: socket.socket,
        transmit_address_tup: tuple[str, int],
    ) -> None:
        logger.debug(f"[server] RX {len(payload_data)} bytes")
        receive_socket.sendto(payload_data, transmit_address_tup)

    def start_proxy(self):
        logger.info(f"Beginning MUX setup")
        self.bind()

        server_proxy = self.one_way_proxy_factory(
            source_socket=self.server_socket,
            destination_socket=self.client_socket,
            routing_function=self.route_server_packet,
        )

        self.server_thread = threading.Thread(
            target=self.one_way_proxy_factory(self.server_sock_tup)
        )

        self._proxy_start_time = utc()
        logger.info(
            f"Ready to begin proxyinging at {self._proxy_start_time.isoformat(timespec='seconds', sep=' ')}."
        )
        while True:
            data, source_address = self.receive_socket.recvfrom(4096)
            self.handle_packet(data, source_address)
        pass

    def bind(self):
        pass


def main():
    proxy = UdpProxy(
        server=("127.0.0.1", 9002),
        client=("127.0.0.1", 9001),
    )
    pass


if __name__ == "__main__":
    import sys

    sys.exit(main())

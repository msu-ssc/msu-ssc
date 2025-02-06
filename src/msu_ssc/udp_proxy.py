import socket
import threading
from typing import Type, TypeAlias

from msu_ssc.ssc_logging import create_logger
from msu_ssc.time_util import utc
from msu_ssc.udp_mux import _shutdown_socket, _tup_to_str

logger = create_logger(__file__, level="DEBUG")


IPv4SockTup: TypeAlias = tuple[str, int]


class OneWayUdpProxyThread(threading.Thread):
    def __init__(
        self,
        *,
        source_tup: IPv4SockTup,
        destination_tup: IPv4SockTup,
        proxy_tup: IPv4SockTup,
        daemon: bool = True,
        name: str = "proxy",
        **kwargs,
    ):
        name += f"({_tup_to_str(proxy_tup)}->{_tup_to_str(destination_tup)})"

        super().__init__(
            name=name,
            daemon=daemon,
            **kwargs,
        )
        self.source_tup = source_tup
        self.destination_tup = destination_tup
        self.proxy_tup = proxy_tup
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.total_packets = 0
        self.total_bytes = 0

    # def target

    def run(self):
        # BIND
        logger.info(f"Attempting to bind to UDP socket {_tup_to_str(self.proxy_tup)} for receiving. [{self.name}]")
        _shutdown_socket(self.proxy_socket)
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.proxy_socket.bind(self.proxy_tup)
        logger.info(f"Successfully bound receiving socket {_tup_to_str(self.proxy_tup)}. [{self.name}]")

        # SERVE FOREVER
        self._mux_start_time = utc()
        logger.info(
            f"Ready to begin proxying at {self._mux_start_time.isoformat(timespec='seconds', sep=' ')}. [{self.name}]"
        )
        while True:
            data, source_address = self.proxy_socket.recvfrom(4096)
            # logger.info(f"{source_address=} {source_address==self.source_tup=} {source_address==self.destination_tup=}")
            self._receive_packet(
                data=data,
                source_address=source_address,
            )

    def handle_packet(
        self,
        *,
        data: bytes,
        destination_tup: IPv4SockTup,
        **kwargs,
    ):
        """Overload this one."""
        logger.debug(f"sending {len(data)} to {_tup_to_str(destination_tup)} [{self.name}]")
        self.proxy_socket.sendto(data, destination_tup)

    def _receive_packet(
        self,
        *,
        data: bytes,
        source_address: IPv4SockTup | None = None,
        debug: bool = True,
    ) -> None:
        if debug:
            message = f"Received {len(data)} bytes"
            if source_address:
                message += f" from {_tup_to_str(source_address)}."
            else:
                message += "."
            message += f" (total: {self.total_packets} packets; {self.total_bytes} bytes) "
            message += f"[{self.name}]"
            logger.debug(message)

        self.handle_packet(
            data=data,
            destination_tup=self.destination_tup,
        )
        self.total_bytes += len(data)
        self.total_packets += 1


class BidirectionalUdpProxy:
    thread_class: Type[OneWayUdpProxyThread] = OneWayUdpProxyThread

    def __init__(
        self,
        *,
        server_tup: tuple[str, int],
        client_tup: tuple[str, int],
        server_proxy_tup: tuple[str, int],
        client_proxy_tup: tuple[str, int],
    ):
        self.server_tup = server_tup
        self.client_tup = client_tup
        self.server_proxy_tup = server_proxy_tup
        self.client_proxy_tup = client_proxy_tup

        self.server_to_client = self.__class__.thread_class(
            daemon=True,
            source_tup=self.server_tup,
            destination_tup=self.client_tup,
            proxy_tup=self.client_proxy_tup,
            name="server_to_client",
        )
        self.client_to_server = self.__class__.thread_class(
            daemon=True,
            source_tup=self.client_tup,
            destination_tup=self.server_tup,
            proxy_tup=self.server_proxy_tup,
            name="client_to_server",
        )

        self.server_to_client.start()
        self.client_to_server.start()

        logger.debug(f"{self.server_to_client=} {type(self.server_to_client)=}")
        logger.debug(f"{self.client_to_server=} {type(self.client_to_server)=}")

    def __repr__(self):
        return f"{self.__class__.__name__}({_tup_to_str(self.server_tup)}<->{_tup_to_str(self.client_tup)})"


class OneWayUdpProxyThreadFailure(OneWayUdpProxyThread):
    """A proxy thread where every other packet will die"""

    def handle_packet(self, *, data: bytes, destination_tup: IPv4SockTup, **kwargs):
        if self.total_packets % 2 == 0:
            logger.info(f"INTENTIONAL FAILURE. packet index: {self.total_packets} [{self.name}]")
        else:
            logger.debug(f"Sending packet normally [{self.name}]")
            self.proxy_socket.sendto(data, destination_tup)


class BidirectionalUdpProxyFailure(BidirectionalUdpProxy):
    thread_class = OneWayUdpProxyThreadFailure


if __name__ == "__main__":
    import time

    proxy_class = BidirectionalUdpProxy
    # proxy_class = BidirectionalUdpProxyFailure

    proxy = proxy_class(
        server_tup=("127.0.0.1", 8003),
        client_tup=("127.0.0.1", 8002),
        server_proxy_tup=("127.0.0.1", 9003),
        client_proxy_tup=("127.0.0.1", 9002),
    )
    logger.info(proxy)
    sleep_secs = 1000000
    logger.debug(f"Sleeping {sleep_secs:,} secs")
    time.sleep(sleep_secs)
    logger.warning(f"Done sleeping. Exiting")

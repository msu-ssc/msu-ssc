import datetime
import logging
import socket
import threading
from typing import Iterable, Literal

logger = logging.getLogger("udp-mux")
logging.basicConfig(level="DEBUG")  # TODO: Fix logging


def _parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reuse-receive-socket",
        "-R",
        action="store_true",
        help="Reuse the socket that receives the segments when retransmitting them. This will cause the source port of the retransmitted packets to be the same as if the packet never passed through this muxer.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    pass


def socket_string(socket_tuple: tuple[str, int]) -> str:
    return f"{socket_tuple[0]}:{socket_tuple[1]}"


def _shutdown_socket(sock: socket.socket):
    try:
        sock.close()
        # sock.shutdown()
    except Exception as exc:
        logger.warning(f"Unable to shutdown socket {sock}", exc_info=exc)


class UdpMux:
    def __init__(
        self,
        receive_socket_tuple: tuple[str, int],
        transmit_socket_tuples: Iterable[tuple[str, int]] | None = None,
        *,
        daemon=True,
        reuse_receive_socket: bool = False,
    ) -> None:
        self.receive_socket_tuple = receive_socket_tuple
        self.transmit_socket_tuples = list(transmit_socket_tuples or [])
        self.daemon = daemon
        self.reuse_receive_socket = reuse_receive_socket

        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._bound = False
        self._received_packet_count = 0
        self._received_bytes_count = 0
        self._transmitted_packet_count = 0
        self._transmitted_bytes_count = 0

        self.thread = threading.Thread(
            name=f"udp-mux-{socket_string(self.receive_socket_tuple)}",
            daemon=self.daemon,
            target=self.start_mux,
        )

        self.thread.start()

    def start_mux(self) -> None:
        self._mux_start_time = datetime.datetime.now(tz=datetime.timezone.utc)
        logger.info(
            f"Beginning muxing at {self._mux_start_time.isoformat(timespec='seconds', sep=' ')}."
        )
        self.bind()

        while True:
            data, source_address = self.receive_socket.recvfrom(4096)
            self.handle_packet(data, source_address)

    def stop_mux(self) -> None:
        self._mux_stop_time = datetime.datetime.now(tz=datetime.timezone.utc)
        try:
            elapsed = (self._mux_stop_time - self._mux_start_time).total_seconds()
        except Exception:
            elapsed = 0
        logger.info(
            f"Stopping muxing at {self._mux_stop_time.isoformat(timespec='seconds', sep=' ')}. Muxed for {elapsed:.2f} seconds ({elapsed / 3600:.4f} hours)."
        )
        _shutdown_socket(self.receive_socket)
        if self.receive_socket is not self.transmit_socket:
            _shutdown_socket(self.transmit_socket)
        logger.debug(
            f"Received {self._received_packet_count} packets ({self._received_bytes_count} bytes). "
            + f"Transmitted {self._transmitted_packet_count} packets ({self._transmitted_bytes_count} bytes)."
        )

    def bind(self) -> None:
        # RECEIVE
        _shutdown_socket(self.receive_socket)
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info(
            f"Attempting to bind to UDP socket {socket_string(self.receive_socket_tuple)} for receiving."
        )
        self.receive_socket.bind(self.receive_socket_tuple)
        logger.info(f"Successfully bound receiving socket.")

        # TRANSMIT
        _shutdown_socket(self.transmit_socket)
        if self.reuse_receive_socket:
            logger.debug(
                f"Reusing receiving UDP socket {socket_string(self.receive_socket_tuple)} as transmitting socket."
            )
            self.transmit_socket = self.receive_socket
        else:
            send_socket_tuple = self.transmit_socket_tuples[0]
            logger.info(
                f"Attempting to bind to UDP socket {socket_string(send_socket_tuple)} for transmitting."
            )
            self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"Successfully bound transmitting socket.")
        self._bound = True

    def handle_packet(self, payload_data: bytes, source_address=None) -> None:
        self._received_packet_count += 1
        self._received_bytes_count += len(payload_data)
        logger.debug(
            f"Received {len(payload_data):,} bytes from {socket_string(source_address)}"
        )
        for transmit_socket_tuple in self.transmit_socket_tuples:
            attempted_transmitted_data_size = len(payload_data)
            logger.debug(
                f"  Sending {attempted_transmitted_data_size:,} bytes to {socket_string(transmit_socket_tuple)}"
            )
            actual_transmitted_data_size = self.transmit_socket.sendto(
                payload_data, transmit_socket_tuple
            )
            if actual_transmitted_data_size != attempted_transmitted_data_size:
                logger.error(
                    (
                        f"Error transmitting packet, originally from {source_address}, to {transmit_socket_tuple}. "
                        + f"Attempted to send {attempted_transmitted_data_size} bytes, actually sent {actual_transmitted_data_size} bytes."
                    ),
                    extra={
                        "payload": {payload_data},
                    },
                )
            self._transmitted_packet_count += 1
            self._transmitted_bytes_count += actual_transmitted_data_size

    def __enter__(self) -> "UdpMux":
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_mux()


receive_socket_tuple = ("127.0.0.1", 8002)
transmit_socket_tuples = [
    ("127.0.0.1", 8005),
    ("127.0.0.1", 8006),
]

with UdpMux(
    receive_socket_tuple=receive_socket_tuple,
    transmit_socket_tuples=transmit_socket_tuples,
    reuse_receive_socket=False,
    daemon=True,
) as mux:
    print(f"{mux=!r}")
    print(f"{mux=!s}")
    import time

    sleep = 3000000
    print(f"Sleeping {sleep:,} seconds...")
    time.sleep(sleep)
    print(f"Done sleeping {sleep:,} seconds...")


# recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# recv_socket.bind(receive_socket_tuple)

# print(f"Listening on UDP socket {receive_socket_tuple}")
# print(f"Repeating on UDP socket {transmit_socket_tuples}")

# loop_count = 0
# while True:
#     print(f"----- {loop_count=} -----")
#     loop_count += 1
#     data, address = recv_socket.recvfrom(4096)
#     print(f"Received {len(data):,} bytes from {address}")
#     for transmit_socket_tuple in transmit_socket_tuples:
#         print(f"  Sending {len(data):,} bytes to {transmit_socket_tuple}")
#         # send_socket.sendto(data, transmit_socket_tuple)
#         recv_socket.sendto(data, transmit_socket_tuple)

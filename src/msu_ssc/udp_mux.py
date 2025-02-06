import datetime
import socket
import threading
from typing import Iterable
from typing import Tuple
from typing import Union

from msu_ssc import ssc_log

# logger = create_logger(__file__, level="DEBUG")


def _tup_to_str(socket_tuple: Tuple[str, int]) -> str:
    return f"{socket_tuple[0]}:{socket_tuple[1]}"


def _str_to_tup(socket_str: str) -> Tuple[str, int]:
    host_str, port_str = socket_str.strip().split(":")
    return (host_str, int(port_str))


def _shutdown_socket(sock: socket.socket):
    try:
        sock.close()
    except Exception as exc:
        ssc_log.warning(f"Unable to shutdown socket {sock}", exc_info=exc)


class UdpMux:
    def __init__(
        self,
        receive_socket_tuple: Tuple[str, int],
        transmit_socket_tuples: Union[Iterable[Tuple[str, int]], None] = None,
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
            name=f"udp-mux-{_tup_to_str(self.receive_socket_tuple)}",
            daemon=self.daemon,
            target=self.start_mux,
        )

        self.thread.start()

    def start_mux(self) -> None:
        ssc_log.info(f"Beginning MUX setup")
        self.bind()
        self._mux_start_time = datetime.datetime.now(tz=datetime.timezone.utc)
        ssc_log.info(f"Ready to begin muxing at {self._mux_start_time.isoformat(timespec='seconds', sep=' ')}.")
        while True:
            data, source_address = self.receive_socket.recvfrom(4096)
            self.handle_packet(data, source_address)

    def stop_mux(self) -> None:
        self._mux_stop_time = datetime.datetime.now(tz=datetime.timezone.utc)
        try:
            elapsed = (self._mux_stop_time - self._mux_start_time).total_seconds()
        except Exception:
            elapsed = 0
        ssc_log.info(
            f"Stopping muxing at {self._mux_stop_time.isoformat(timespec='seconds', sep=' ')}. Muxed for {elapsed:.2f} seconds ({elapsed / 3600:.4f} hours)."
        )
        _shutdown_socket(self.receive_socket)
        if self.receive_socket is not self.transmit_socket:
            _shutdown_socket(self.transmit_socket)
        ssc_log.debug(
            f"Received {self._received_packet_count} packets ({self._received_bytes_count} bytes). "
            + f"Transmitted {self._transmitted_packet_count} packets ({self._transmitted_bytes_count} bytes)."
        )

    def bind(self) -> None:
        # RECEIVE
        _shutdown_socket(self.receive_socket)
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ssc_log.info(f"Attempting to bind to UDP socket {_tup_to_str(self.receive_socket_tuple)} for receiving.")
        self.receive_socket.bind(self.receive_socket_tuple)
        ssc_log.info(f"Successfully bound receiving socket.")

        # TRANSMIT
        _shutdown_socket(self.transmit_socket)
        if self.reuse_receive_socket:
            ssc_log.debug(
                f"Reusing receiving UDP socket {_tup_to_str(self.receive_socket_tuple)} as transmitting socket."
            )
            self.transmit_socket = self.receive_socket
        else:
            send_socket_tuple = self.transmit_socket_tuples[0]
            ssc_log.info(f"Attempting to bind to UDP socket {_tup_to_str(send_socket_tuple)} for transmitting.")
            self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ssc_log.info(f"Successfully bound transmitting socket.")
        self._bound = True

    def handle_packet(self, payload_data: bytes, source_address=None) -> None:
        self._received_packet_count += 1
        self._received_bytes_count += len(payload_data)
        ssc_log.debug(f"Received {len(payload_data):,} bytes from {_tup_to_str(source_address)}")
        for transmit_socket_tuple in self.transmit_socket_tuples:
            attempted_transmitted_data_size = len(payload_data)
            ssc_log.debug(
                f"  Sending {attempted_transmitted_data_size:,} bytes to {_tup_to_str(transmit_socket_tuple)}"
            )
            actual_transmitted_data_size = self.transmit_socket.sendto(payload_data, transmit_socket_tuple)
            if actual_transmitted_data_size != attempted_transmitted_data_size:
                ssc_log.error(
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


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "receive",
        action="store",
        help="UDP socket to receive on",
    )
    parser.add_argument(
        "--transmit",
        "-T",
        nargs="*",
        help="UDP sockets to retransmit on. Give as a list of separated sockets, like `-T 127.0.0.1:8001 127.0.0.1:8002`",
        default=(),
    )
    parser.add_argument(
        "--log-level",
        "-L",
        help="Console log level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        default="INFO",
        action="store",
    )
    parser.add_argument(
        "--reuse-socket",
        action="store_true",
        help=(
            "Reuse the socket that receives the segments when retransmitting them. "
            + "This will cause the source port of the retransmitted packets to be the same as if the packet never passed through this muxer.",
        ),
    )
    args = parser.parse_args()
    receive_socket_tuple = _str_to_tup(args.receive)
    transmit_socket_tuples = [_str_to_tup(sock_str) for sock_str in args.transmit]
    ssc_log.debug(f"Parsed command line arguments: {args!r}")
    ssc_log.debug(f"Parsed receive UDP socket: {receive_socket_tuple!r}")
    ssc_log.debug(f"Parsed transmit UCP socket(s): {transmit_socket_tuples!r}")

    with UdpMux(
        receive_socket_tuple=receive_socket_tuple,
        transmit_socket_tuples=transmit_socket_tuples,
        reuse_receive_socket=args.reuse_socket,
        daemon=True,
        log_level=args.log_level,
    ) as mux:  # noqa: F841
        import time

        time.sleep(5)
        pass

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

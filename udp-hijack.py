#!/usr/bin/env python3

import socket

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
speak_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

listen_host = "127.0.0.1"
speak_host = "127.0.0.1"
listen_port = 8002
speak_port = 8006

listen_socket_tup = (listen_host, listen_port)
listen_socket.bind(listen_socket_tup)

speak_socket_tup = (listen_host, speak_port)
speak_socket.bind(speak_socket_tup)

print("Listening on " + listen_host + ":" + str(listen_port))
print("Speaking on " + speak_host + ":" + str(speak_port))

loop_count = 0
while True:
    print(f"----- {loop_count=} -----")
    loop_count += 1
    payload, initial_source_address = listen_socket.recvfrom(1)
    print("Echoing data back to " + str(initial_source_address))
    print(f"Data received: {payload=}")
    print(f"{initial_source_address=} {type(initial_source_address)=}")
    print(f"{len(payload)=} {type(payload)=}")
    # sent = listen_socket.sendto(payload, initial_source_address)
    # print(f"{type(sent)=} {sent=}")

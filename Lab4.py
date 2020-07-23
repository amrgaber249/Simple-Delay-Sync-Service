import sys
import os
import threading
import socket
import time
import uuid
import struct
import datetime
import select

# https://bluesock.org/~willkg/dev/ansi.html
ANSI_RESET = "\u001B[0m"
ANSI_RED = "\u001B[31m"
ANSI_GREEN = "\u001B[32m"
ANSI_YELLOW = "\u001B[33m"
ANSI_BLUE = "\u001B[34m"

_NODE_UUID = str(uuid.uuid4())[:8]


def print_yellow(msg):
    print(f"{ANSI_YELLOW}{msg}{ANSI_RESET}")


def print_blue(msg):
    print(f"{ANSI_BLUE}{msg}{ANSI_RESET}")


def print_red(msg):
    print(f"{ANSI_RED}{msg}{ANSI_RESET}")


def print_green(msg):
    print(f"{ANSI_GREEN}{msg}{ANSI_RESET}")


def get_broadcast_port():
    return 35498


def get_node_uuid():
    return _NODE_UUID


class NeighborInfo(object):
    def __init__(self, delay, counter, ip=None, tcp_port=None):
        # Ip and port are optional, if you want to store them.
        self.delay = delay
        self.counter = counter
        self.ip = ip
        self.tcp_port = tcp_port


############################################
#######  Y  O  U  R     C  O  D  E  ########
############################################


# Don't change any variable's name.
# Use this hashmap to store the information of your neighbor nodes.
neighbor_information = {}
# Leave the server socket as global variable.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 0))

# Leave broadcaster as a global variable.
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setup the UDP socket
broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
broadcaster.bind(("", get_broadcast_port()))


def send_broadcast_thread():
    node_uuid = get_node_uuid()
    port = server.getsockname()[1]
    msg = f"{node_uuid} ON {port}"

    while True:
        # TODO: write logic for sending broadcasts.

        print_green(msg)
        broadcaster.sendto(msg.encode("utf-8"),
                           ('<broadcast>', get_broadcast_port()))
        time.sleep(1)   # Leave as is.


def receive_broadcast_thread():
    """
    Receive broadcasts from other nodes,
    launches a thread to connect to new nodes
    and exchange timestamps.
    """
    while True:
        # TODO: write logic for receiving broadcasts.
        data, (ip, port) = broadcaster.recvfrom(4096)
        decoded_data = data.decode("utf-8").split()
        recv_uuid = decoded_data[0]
        recv_tcp_port = int(decoded_data[2])
        recv_ip = str(ip)
        if recv_uuid != get_node_uuid():
            print_blue(f"RECV: {data} FROM: {ip}:{port}")
            thread = daemon_thread_builder(
                exchange_timestamps_thread, (recv_uuid, recv_ip, recv_tcp_port))
            thread.start()


def tcp_server_thread():
    """
    Accept connections from other nodes and send them
    this node's timestamp once they connect.
    """
    server.listen(10)
    while True:
        client_socket, (ip, port) = server.accept()
        print(f"Connection made with port: {port}")
        time_stamp = str(datetime.datetime.utcnow().timestamp())
        client_socket.send(time_stamp.encode("utf-8"))
        client_socket.close()

    pass


def exchange_timestamps_thread(other_uuid: str, other_ip: str, other_tcp_port: int):
    """
    Open a connection to the other_ip, other_tcp_port
    and do the steps to exchange timestamps.

    Then update the neighbor_info map using other node's UUID.
    """
    print_yellow(f"ATTEMPTING TO CONNECT TO {other_uuid}")
    client_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if should_update(other_uuid):
        try:
            client_tcp_socket.connect((other_ip, other_tcp_port))
        except ConnectionRefusedError as e:
            print(f"Other Node is down!")
            return
        data = client_tcp_socket.recv(4096)
        time_stamp = float(data.decode("utf-8"))
        curr_time_stamp = datetime.datetime.utcnow().timestamp()
        delay = curr_time_stamp - time_stamp
        print(f"delay is : {delay}")
        neighbor_information[other_uuid] = NeighborInfo(
            delay, 1, other_ip, other_tcp_port)
        client_tcp_socket.close()
    else:
        # 7zwed al counter bta3 albroadcoast counter
        neighbor_information[other_uuid].counter += 1
        print("already exists")
    pass


def should_update(other_uuid: str):
    if other_uuid not in neighbor_information or neighbor_information[other_uuid].counter >= 10:
        return True
    return False


def daemon_thread_builder(target, args=()) -> threading.Thread:
    """
    Use this function to make threads. Leave as is.
    """
    th = threading.Thread(target=target, args=args)
    th.setDaemon(True)
    return th


def entrypoint():
    threads = []
    threads.append(daemon_thread_builder(tcp_server_thread))
    threads.append(daemon_thread_builder(send_broadcast_thread))
    threads.append(daemon_thread_builder(receive_broadcast_thread))
    # threads.append(daemon_thread_builder(
    # exchange_timestamps_thread, ("", "", 0)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

############################################
############################################


def main():
    """
    Leave as is.
    """
    print("*" * 50)
    print_red("To terminate this program use: CTRL+C")
    print_red("If the program blocks/throws, you have to terminate it manually.")
    print_green(f"NODE UUID: {get_node_uuid()}")
    print("*" * 50)
    time.sleep(2)   # Wait a little bit.
    entrypoint()


if __name__ == "__main__":
    main()


import pickle
import socket
import time

from Actuator import *
from Elevator import Elevator
from ThreadManager import launch_thr

SEND_UDP = 11133
RECV_UDP = 11134
SEND_TCP = 11135
RECV_TCP = 11147


def launch_thr(target, args=None):
    """ Launch thread """
    if args is not None:
        t = threading.Thread(target=target, args=args)
    else:
        t = threading.Thread(target=target)
    t.start()


class Network:
    def __init__(self, id, num_floors):
        self.id = id
        self.order_timeout_secs = 60

        self.ips = {self.id: self.own_ip()}
        self.elevators = {id: Elevator()}
        self.hub_down = dict()  # KEY: floor, id  VALUE: boolean
        self.hub_up = dict()
        self.cab = dict()  # KEY: floor, id  VALUE: boolean

        self.cab[0] = False
        self.hub_up[0] = False

        self.cab[num_floors - 1] = False
        self.hub_down[num_floors - 1] = False

        for floor in range(1, num_floors - 1):
            self.cab[floor] = False
            self.hub_up[floor] = False
            self.hub_down[floor] = False

        self._sockets_init()

        launch_thr(self.receive_hub_order)
        launch_thr(self.receive_state)
        time.sleep(0.5)
        launch_thr(self.send_state)

    def _sockets_init(self):
        self.udp_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_recv.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_recv.bind(('', RECV_UDP))

        self.tcp_recv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.tcp_recv.bind(('', RECV_TCP))
        self.tcp_recv.listen(5)

        self.udp_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.tcp_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



    def own_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def winning_id(self, floor):
        minimum = 100000
        for id, elevator in self.elevators.items():
            cost = abs(floor - elevator.floor)
            if cost < minimum:
                minimum = cost
                winner = id

        print("winner: ", winner)
        return winner

    def receive_hub_order(self):
        while True:
            client_sock, address = self.tcp_recv.accept()

            msg = client_sock.recv(1024)
            l = list(str(msg, encoding='utf8'))
            type = int(l[0])
            floor = int(l[1])
            id = l[2:]
            id = ''.join(id)

            self.actuator.button_light_on(type, floor)

            if id == self.id:
                if type == Event.BUTTON_HUB_UP:
                    self.hub_up[floor] = time.time()
                else:
                    self.hub_down[floor] = time.time()

                self.actuator.event_queue.put(Event(Event.ASSIGN, floor))

            client_sock.close()

    def clear_hub_order(self, type, floor):
       self.udp_send.sendto(pickle.dumps((Event.CLEAR, type, floor)), ('<broadcast>', RECV_UDP))

    def send_hub_order(self, type, floor, id):
        ip = self.ips[id]
        tcp_send = socket.create_connection((ip, RECV_TCP))
        tcp_send.send(bytes(str(type) + str(floor) + str(id), 'utf8'))
        tcp_send.close()
        self.actuator.button_light_on(type, floor)
        if id == self.id:
            if type == Event.BUTTON_HUB_UP:
                self.hub_up[floor] = time.time()
            else:
                self.hub_down[floor] = time.time()

            self.actuator.event_queue.put(Event(Event.ASSIGN, floor))
        self.send_all_order(type, floor)

    def send_all_order(self, type, floor):
        self.udp_send.sendto(pickle.dumps((Event.NOTIFY, type, floor)), ('<broadcast>', RECV_UDP))

    def receive_state(self):
        while True:
            msg, address = self.udp_recv.recvfrom(2048)
            object = pickle.loads(msg)
            id = object[0]

            if object[0] == Event.CLEAR:
                self.actuator.button_light_off(object[1], object[2])

            elif object[0] == Event.NOTIFY:
                self.actuator.button_light_on(object[1], object[2])

            elif id != self.id:
                elevator = object[1]
                self.elevators.update({id: elevator})
                self.ips.update({id: address[0]})
            print(self.elevators)
            print(self.ips)

    def send_state(self):
        while True:
            time.sleep(1)
            self.udp_send.sendto(pickle.dumps((self.id, self.elevators[self.id])), ('<broadcast>', RECV_UDP))
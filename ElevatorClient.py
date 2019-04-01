import sys
import threading

import ElevatorClient
from Actuator import Actuator
from Elevator import Elevator
from Event import Event
from Network import Network


def get_direction(current_floor, target_floor):
    if current_floor == target_floor:
        return Actuator.DIR_STOP
    elif target_floor > current_floor:
        return Actuator.DIR_UP
    else:
        return Actuator.DIR_DOWN


def launch_thr(target, args=None):
    """ Launch thread """
    if args is not None:
        t = threading.Thread(target=target, args=args)
    else:
        t = threading.Thread(target=target)
    t.start()


if __name__ == "__main__":
    a = ElevatorClient.ElevatorClient(sys.argv[1], 4, 3)


class ElevatorClient:
    def __init__(self, id, num_floors, door_timeout_sec):
        self.id = id
        self.num_floors = num_floors

        self.actuator = None
        self.network = Network(id, num_floors)
        self.actuator = Actuator(num_floors, door_timeout_sec)
        self.network.actuator = self.actuator
        self.network.elevators[self.id].floor = self.actuator.find_floor()

        try:
            handle = open('./cab_orders.txt', 'r+')
            self.network.cab = eval(handle.readline())
            for floor, v in self.network.cab.items():
                if v:
                    self.actuator.button_light_on(Event.BUTTON_CAB, floor)
            self.actuator.event_queue.put(Event(Event.ASSIGN))
        except:
            pass

        launch_thr(self.actuator_events_handler)

    def open_door(self):
        print("OPEN DOOR")
        self.actuator.open_door()
        self.network.elevators[self.id].state = Elevator.DOOR_OPEN

    def wake_up(self):
        cab = {k: v for k, v in self.network.cab.items() if v}
        hub_down = {k: v for k, v in self.network.hub_down.items() if v}
        hub_up = {k: v for k, v in self.network.hub_up.items() if v}

        active = list(cab.keys()) + list(hub_down.keys()) + list(hub_up.keys())

        current_floor = self.network.elevators[self.id].floor = self.actuator.find_floor()
        direction = self.network.elevators[self.id].direction
        state = self.network.elevators[self.id].state

        try:
            hub_up = self.network.hub_up[current_floor]
        except KeyError:
            hub_up = False

        try:
            hub_down = self.network.hub_down[current_floor]
        except KeyError:
            hub_down = False

        try:
            cab = self.network.cab[current_floor]
        except KeyError:
            cab = False

        upper = lower = 0
        for floor in active:
            if floor > current_floor:
                upper += 1
            elif floor < current_floor:
                lower += 1

        # Current floor
        attend_up = attend_down = attend_cab = False

        if state == Elevator.MOVING:
            if direction != Actuator.DIR_DOWN and hub_up:
                attend_up = True

            if direction != Actuator.DIR_UP and hub_down:
                attend_down = True

            if direction == Actuator.DIR_UP and hub_down and not upper:
                attend_down = True

            if direction == Actuator.DIR_DOWN and hub_up and not lower:
                attend_up = True

            attend_cab = cab

        elif state == Elevator.IDLE and not lower and not upper:
                attend_up = hub_up
                attend_down = hub_down
                attend_cab = cab

        if attend_cab or attend_down or attend_up:
            self.open_door()

            if attend_up:
                self.actuator.button_light_off(Event.BUTTON_HUB_UP, current_floor)
                self.network.clear_hub_order(Event.BUTTON_HUB_UP, current_floor)
                self.network.hub_up[current_floor] = False


            if attend_down:
                self.actuator.button_light_off(Event.BUTTON_HUB_DOWN, current_floor)
                self.network.clear_hub_order(Event.BUTTON_HUB_DOWN, current_floor)
                self.network.hub_down[current_floor] = False

            if attend_cab:
                self.actuator.button_light_off(Event.BUTTON_CAB, current_floor)
                self.network.cab[current_floor] = False
                handle = open('./cab_orders.txt', 'w')
                handle.write(str(self.network.cab))
                handle.write('\n')
                handle.close()

        # Movement, next floor, or stay
        if state == Elevator.IDLE:
            if (direction == Actuator.DIR_UP and not upper and lower) or (direction == Actuator.DIR_DOWN and not lower and upper):
                print("Change dir")
                direction = direction * -1

            elif not lower and not upper:
                direction = Actuator.DIR_STOP

            elif (lower or upper) and direction == Actuator.DIR_STOP:
                print("Closest")
                # Calculate closest
                minimum = self.num_floors
                direction = Actuator.DIR_STOP

                for floor in active:
                    dist = abs(floor - current_floor)
                    if dist != 0 and dist < minimum:  # != 0 Avoid trolls and division 0
                        minimum = dist
                        direction = int((floor - current_floor) / dist)

            self.actuator.set_direction(direction)
            self.network.elevators[self.id].direction = direction

            if direction != Actuator.DIR_STOP:
                self.network.elevators[self.id].state = Elevator.MOVING

    def actuator_events_handler(self):
        while True:
            event = self.actuator.wait_event()
            # Control limits
            if event.type == Event.NEW_FLOOR:
                self.network.elevators[self.id].floor = event.floor

                # Reached limits
                if event.floor == 0 or event.floor == self.actuator.max_floor:
                    self.actuator.set_direction(Actuator.DIR_STOP)
                    self.network.elevators[self.id].direction = Actuator.DIR_STOP

            elif event.type == Event.BUTTON_CAB:
                self.network.cab[event.floor] = True
                self.actuator.button_light_on(Event.BUTTON_CAB, event.floor)
                handle =  open('./cab_orders.txt', 'w')
                handle.write(str(self.network.cab))
                handle.write('\n')
                handle.close()

            elif event.type == Event.BUTTON_HUB_UP or event.type == Event.BUTTON_HUB_DOWN:
                self.network.send_hub_order(event.type, event.floor, self.network.winning_id(event.floor))

            elif event.type == Event.DOOR_CLOSE:
                self.network.elevators[self.id].state = Elevator.IDLE

            # Orders, Movement
            if event.type == Event.BUTTON_CAB or event.type == Event.BUTTON_HUB_UP or event.type == Event.BUTTON_HUB_DOWN or event.type == Event.ASSIGN:
                if self.network.elevators[self.id].state == Elevator.IDLE:
                    self.wake_up()
            elif event.type == Event.NEW_FLOOR or Event.DOOR_CLOSE:
                self.wake_up()



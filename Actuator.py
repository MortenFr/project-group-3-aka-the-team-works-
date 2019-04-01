"""
void elevator_hardware_init();

void elevator_hardware_set_motor_direction(elevator_hardware_motor_direction_t dirn);
void elevator_hardware_set_button_lamp(elevator_hardware_button_type_t button, int floor, int value);
void elevator_hardware_set_floor_indicator(int floor);
void elevator_hardware_set_door_open_lamp(int value);
void elevator_hardware_set_stop_lamp(int value);

int elevator_hardware_get_button_signal(elevator_hardware_button_type_t button, int floor);
int elevator_hardware_get_floor_sensor_signal(void);
int elevator_hardware_get_stop_signal(void);
int elevator_hardware_get_obstruction_signal(void);
"""

import os
import threading
import time
from ctypes import *
from multiprocessing import Process, Queue, Lock

from Event import Event


def launch_thr(target, args=None):
    """ Launch thread """
    if args is not None:
        t = Process(target=target, args=(args[0], args[1],))
    else:
        t = Process(target=target)
    t.start()


def button_pushed(new_state, old_state):
    """ Check a newly pushed button """
    if new_state == Actuator.BUTTON_ON and old_state == Actuator.BUTTON_OFF:
        return True
    return False


class Driver:
    def __init__(self):
        os.system('./compile_library.sh')
        self.driver = CDLL('./driver.so')
        self.driver.elevator_hardware_init()
        self.lock = Lock()

    def elevator_hardware_set_motor_direction(self, dirn):
        self.lock.acquire()
        try:
            self.driver.elevator_hardware_set_motor_direction(dirn)
        finally:
            self.lock.release()

    def elevator_hardware_set_button_lamp(self, button, floor, light):
        self.lock.acquire()
        try:
            self.driver.elevator_hardware_set_button_lamp(button, floor, light)
        finally:
            self.lock.release()
        return

    def elevator_hardware_set_floor_indicator(self, floor):
        self.lock.acquire()
        try:
            self.driver.elevator_hardware_set_floor_indicator(floor)
        finally:
            self.lock.release()

    def elevator_hardware_set_door_open_lamp(self, light):
        self.lock.acquire()
        try:
            self.driver.elevator_hardware_set_door_open_lamp(light)
        finally:
            self.lock.release()
        return

    def elevator_hardware_get_button_signal(self, button, floor):
        self.lock.acquire()
        try:
            result = self.driver.elevator_hardware_get_button_signal(button, floor)
        finally:
            self.lock.release()
        return result

    def elevator_hardware_get_obstruction_signal(self):
        self.lock.acquire()
        try:
            result = self.driver.elevator_hardware_get_obstruction_signal()
        finally:
            self.lock.release()
        return result

    def elevator_hardware_get_stop_signal(self):
        self.lock.acquire()
        try:
            result = self.driver.elevator_hardware_get_stop_signal()
        finally:
            self.lock.release()
        return result

    def elevator_hardware_get_floor_sensor_signal(self):
        self.lock.acquire()
        try:
            result = self.driver.elevator_hardware_get_floor_sensor_signal()
        finally:
            self.lock.release()
        return result


class Actuator:
    # DIRECTIONS
    DIR_DOWN = -1
    DIR_STOP = 0
    DIR_UP = 1

    # LIGHTS
    LIGHT_ON = 1
    LIGHT_OFF = 0

    # BUTTONS
    BUTTON_ON = 1
    BUTTON_OFF = 0

    # FLOOR
    UNKNOWN_FLOOR = -1

    def __init__(self, num_floors, door_timeout_sec, ):
        self.driver = Driver()
        self.num_floors = num_floors
        self.max_floor = num_floors - 1
        self.door_timeout_sec = door_timeout_sec
        self.floor_event_enable = True
        self.door_open = False
        self.event_queue = Queue()

        self._lights_init()
        self._event_threads_init()

    def _lights_init(self):
        self.close_door()
        self.all_order_lights_off()
        floor = self.get_floor()
        if floor != Actuator.UNKNOWN_FLOOR:
            self.driver.elevator_hardware_set_floor_indicator(floor)

    def _event_threads_init(self):
        launch_thr(self._generate_floor_event)

        launch_thr(self._generate_hub_up_button_event, args=[Event.BUTTON_HUB_UP, 0])
        launch_thr(self._generate_cab_button_event, args=[Event.BUTTON_CAB, 0])

        launch_thr(self._generate_hub_down_button_event, args=[Event.BUTTON_HUB_DOWN, self.max_floor])
        launch_thr(self._generate_cab_button_event, args=[Event.BUTTON_CAB, self.max_floor])

        for floor in range(1, self.max_floor):
            launch_thr(self._generate_hub_down_button_event, args=[Event.BUTTON_HUB_DOWN, floor])
            launch_thr(self._generate_hub_up_button_event, args=[Event.BUTTON_HUB_UP, floor])
            launch_thr(self._generate_cab_button_event, args=[Event.BUTTON_CAB, floor])

    def _generate_floor_event(self):
        old = self.get_floor()
        while True:
            new = self.get_floor()
            if new != old and self.valid_floor(new) and self.floor_event_enable:
                self.driver.elevator_hardware_set_floor_indicator(new)
                self.event_queue.put(Event(Event.NEW_FLOOR, new))
            old = new

    def _generate_hub_up_button_event(self, button, floor):
        old = self.driver.elevator_hardware_get_button_signal(button, floor)
        while True:
            new = self.driver.elevator_hardware_get_button_signal(button, floor)
            if button_pushed(new, old):
                self.event_queue.put(Event(button, floor))
            old = new

    def _generate_hub_down_button_event(self, button, floor):
        old = self.driver.elevator_hardware_get_button_signal(button, floor)
        while True:
            new = self.driver.elevator_hardware_get_button_signal(button, floor)
            if button_pushed(new, old):
                self.event_queue.put(Event(button, floor))
            old = new

    def _generate_cab_button_event(self, button, floor):
        old = self.driver.elevator_hardware_get_button_signal(button, floor)
        while True:
            new = self.driver.elevator_hardware_get_button_signal(button, floor)
            if button_pushed(new, old):
                self.event_queue.put(Event(button, floor))
            old = new

    def valid_floor(self, floor):
        valid = False
        for f in range(0, self.num_floors):
            if floor == f:
                return True
        return valid

    def find_floor(self):
        floor = self.get_floor()
        if self.valid_floor(floor):
            return floor
        self.floor_event_enable = False
        for ms in range(1000):
            time.sleep(0.01)
            self.set_direction(Actuator.DIR_UP)
            floor = self.get_floor()
            if self.valid_floor(floor):
                self.set_direction(Actuator.DIR_STOP)
                self.floor_event_enable = True
                return floor

        for ms in range(1000):
            time.sleep(0.01)
            self.set_direction(Actuator.DIR_DOWN)
            floor = self.get_floor()
            if self.valid_floor(floor):
                self.set_direction(Actuator.DIR_STOP)
                self.floor_event_enable = True
                return floor
        self.floor_event_enable = True
        return Actuator.UNKNOWN_FLOOR

    def get_floor(self):
        floor = self.driver.elevator_hardware_get_floor_sensor_signal()
        if self.valid_floor(floor):
            return floor
        # SENSOR ERROR
        return Actuator.UNKNOWN_FLOOR

    def set_direction(self, direction):
        floor = self.get_floor()
        if floor == 0 and direction == Actuator.DIR_DOWN:
            direction = Actuator.DIR_STOP
        elif floor == self.max_floor and direction == Actuator.DIR_UP:
            direction = Actuator.DIR_STOP

        if direction != Actuator.DIR_STOP:  # Close door before moving
            self.close_door()
        self.driver.elevator_hardware_set_motor_direction(direction)

    def open_door(self):
        self.set_direction(Actuator.DIR_STOP)
        self.driver.elevator_hardware_set_door_open_lamp(Actuator.LIGHT_ON)
        self.door_open = True
        t = threading.Timer(self.door_timeout_sec, self.close_door, args=[True])  # Close door after door timeout
        t.start()

    def close_door(self, automatic=False):
        self.driver.elevator_hardware_set_door_open_lamp(Actuator.LIGHT_OFF)
        self.door_open = False
        if automatic:
            self.event_queue.put(Event(Event.DOOR_CLOSE))  # Throw event if automatic close door

    def all_order_lights_off(self):
        for floor in range(self.num_floors):
            self.button_light_off(Event.BUTTON_CAB, floor)

        for floor in range(1, self.num_floors):
            self.button_light_off(Event.BUTTON_HUB_DOWN, floor)

        for floor in range(0, self.max_floor):
            self.button_light_off(Event.BUTTON_HUB_UP, floor)

    def button_light_on(self, button, floor):
        if self.valid_floor(floor):
            self.driver.elevator_hardware_set_button_lamp(button, floor, Actuator.LIGHT_ON)

    def button_light_off(self, button, floor):
        if self.valid_floor(floor):
            self.driver.elevator_hardware_set_button_lamp(button, floor, Actuator.LIGHT_OFF)

    def wait_event(self):
        return self.event_queue.get(True)

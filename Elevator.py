from Actuator import Actuator


class Elevator:
    IDLE = 'IDLE'
    MOVING = 'MOVING'
    DOOR_OPEN = 'DOOR_OPEN'

    def __init__(self, state=IDLE, direction=Actuator.DIR_STOP, floor=0):
        self.state = state
        self.direction = direction
        self.floor = floor

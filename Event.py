class Event:
    BUTTON_HUB_UP = 0
    BUTTON_HUB_DOWN = 1
    BUTTON_CAB = 2
    REPRESS_HUB_UP = 'REPRESS_HUB_UP'
    REPRESS_HUB_DOWN = 'REPRESS_HUB_DOWN'
    REPRESS_CAB = 'REPRESS_HUB_CAB'
    DOOR_CLOSE = 'DOOR_CLOSE'
    NEW_FLOOR = 'NEW_FLOOR'
    ACK = 'ACK'
    RESTORE = 'RESTORE'
    CHECK_ALL = 'CHECK_ALL'

    HUB_DOWN_TAKEN = 'HUB_DOWN_TAKEN'
    HUB_UP_TAKEN = 'HUB_UP_TAKEN'

    STATE = 'STATE'
    INIT = 'INIT' \

    ASSIGN = 'ASSIGN'
    CLEAR = 'CLEAR'
    NOTIFY = 'NOTIFY'


    def __init__(self, type=None, floor=0, order=False):
        self.type = type
        self.floor = floor
        self.order = order

from Actuator import Actuator


class State:

    def __init__(self):
        # state variables
        self.current_floor = 0
        self.direction = 0
        self.orders = Orders()
        self.num_nodes = 0
        # self.door_open = False

        # if the elevator is initialized between floors
        # if self.current_floor == -1:
        #    self.current_floor = self.actuator.find_floor()


class Orders:

    ADD = 1
    REMOVE = 0

    def __init__(self):
        self.elevators = dict()         # KEY: id,        VALUE: floor
        self.hub_down = dict()          # KEY: floor, id  VALUE: boolean
        self.hub_up = dict()
        self.cab_orders = dict()        # KEY: floor, id  VALUE: boolean
        self.floors_with_orders = {}    # KEY: floor, id  VALUE: boolean

    def update_order(self, event, value, ID):

        if value == Orders.ADD:
            if event.type == Actuator.BUTTON_CAB:
                self.cab_orders[event.floor, ID] = 1
                self.floors_with_orders[event.floor, ID] = True

            elif event.type == Actuator.BUTTON_HUB_DOWN:
                self.hub_down[event.floor, ID] = 1
                self.floors_with_orders[event.floor, ID] = True

            elif event.type == Actuator.BUTTON_HUB_UP:
                self.hub_up[event.floor, ID] = 1
                self.floors_with_orders[event.floor, ID] = True

            print("cab_orders: ", self.cab_orders)
            print("hub_down: ", self.hub_down)
            print("hub_up: ", self.hub_up)

            # synchronize()
            # assign()

        elif value == Orders.REMOVE:
            if event.type == Actuator.BUTTON_CAB:
                try:
                    self.cab_orders.pop((event.floor, ID))
                    print("Removed cab order floor: ", event.floor)
                    self.floors_with_orders.pop((event.floor, ID))
                except KeyError:
                    pass

            elif event.type == Actuator.BUTTON_HUB_DOWN:
                try:
                    self.hub_down.pop((event.floor, ID))
                    print("Removed hub DOWN order floor: ", event.floor)
                    self.floors_with_orders.pop((event.floor, ID))
                except KeyError:
                    pass

            elif event.type == Actuator.BUTTON_HUB_UP:
                try:
                    self.hub_up.pop((event.floor, ID))
                    print("Removed hub UP order floor: ", event.floor)
                    self.floors_with_orders.pop((event.floor, ID))
                except KeyError:
                    pass

        # add synchronization algorithm

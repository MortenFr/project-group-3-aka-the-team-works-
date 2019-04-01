class Orders:
    def __init__(self, id, num_floors):
        self.num_floors = num_floors
        self.hub_down = dict()  # KEY: floor, id  VALUE: boolean
        self.hub_up = dict()
        self.cab = dict()  # KEY: floor, id  VALUE: boolean
        self.add_key(num_floors)

    def update(self, orders):
        self.hub_down.update(orders.hub_down.items())
        self.hub_up.update(orders.hub_up.items())
        self.cab.update(orders.cab.items())

    def add_key(self, num_floors):
        self.cab[0] = False
        self.hub_up[0] = False

        self.cab[num_floors - 1] = False
        self.hub_down[num_floors - 1] = False

        for floor in range(1, num_floors - 1):
            self.cab[floor] = False
            self.hub_up[floor] = False
            self.hub_down[floor] = False
import time

from Actuator import Actuator

TIMEOUT = 4

if __name__ == "__main__":
    a = Actuator(4, 3)

    a.all_order_lights_off()

    print("Test: Turn on light of pressed buttons")
    for i in range(15):
        event = a.wait_event()
        print(str(event.type) + str(event.floor))
        a.button_light_on(event.type, event.floor)

    print("Test: Turn off all order lights")
    a.all_order_lights_off()
    time.sleep(TIMEOUT)

    print("Test: Open door")
    a.open_door()
    print("Test: Wait for automatic door close")
    a.wait_event()

    print("Put the elevator in no floor")
    time.sleep(TIMEOUT)
    print("Test: Finding floor")
    print("Current floor = " + str(a.get_floor()))
    floor = a.find_floor()
    print("Found floor = " + str(floor))
    time.sleep(TIMEOUT)

    print("Put the elevator in floor 0 or 1 or 2")
    time.sleep(TIMEOUT)

    print("Test: Move to upper floor")
    floor = a.find_floor()
    a.set_direction(Actuator.DIR_UP)
    event = a.wait_event()
    a.set_direction(Actuator.DIR_STOP)
    assert event.floor == floor + 1

    time.sleep(TIMEOUT)
    print("Test: Move to lower floor")
    floor = a.get_floor()
    a.set_direction(Actuator.DIR_DOWN)
    event = a.wait_event()
    a.set_direction(Actuator.DIR_STOP)
    assert event.floor == floor - 1

    print("PASS")

#!/bin/bash
gcc -shared -Wl,-soname,driver -o driver.so -fPIC elevator_hardware.c



from machine import Pin
import time
import os
import _thread
import random
import gc
led1 = ""
led2 = ""
led3 = ""

led = Pin(25, Pin.OUT)

def blink_inf():
    global blinking
    
    while blinking:
        led.on()
        time.sleep(0.1)
        led.off()
        time.sleep(0.1)

print("BurmalPico")
print("RP2040 online")
print()

while True:
    command = input("burmal@pico:~$ ")
    
    if command == "led on":
        led.on()
        print("Light: ON")
        
    elif command == "led off":
        led.off()
        print("Light: OFF")

    elif command == "led blink":
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
        print("Blink complete")
        
    elif command == "led blink inf":
        blinking = True
        _thread.start_new_thread(blink_inf,())
        print("Inf blink: ON")
            
    elif command == "stop":
        blinking = False
        led.off()
        print ("Blink stopped")
        
    elif command.startswith("led bit save "):
        parts = command.split()

        if len(parts) == 5:
            number = parts[3]
            bits = parts[4]

            if number == "1":
                led1 = bits
                print("LED 1 saved")
            elif number == "2":
                led2 = bits
                print("LED 2 saved")
            elif number == "3":
                led3 = bits
                print("LED 3 saved")
            else:
                print("Invalid LED number")
        else:
            print("Usage: led bit save 1 101010")

    elif command == "led bit 1":
        for bit in led1:
            led.value(int(bit))
            time.sleep(0.1)
        led.off()

    elif command == "led bit 2":
        for bit in led2:
            led.value(int(bit))
            time.sleep(0.1)
        led.off()

    elif command == "led bit 3":
        for bit in led3:
            led.value(int(bit))
            time.sleep(0.1)
        led.off()

    elif command.startswith("led bit "):
        bits = command[8:]

        for bit in bits:
            if bit == "1":
                led.on()
            elif bit == "0":
                led.off()
            else:
                print("Invalid bit")
                break

            time.sleep(0.1)

        led.off()
            
        time.sleep(0.1)
            
        led.off()
        
    elif command == "led status":
        if led.value():
            print("led: ON")
        else:
            print("led: OFF")
            
    elif command == "reaction":
        print ("Get ready...")
        time.sleep(2)
        
        led.off()
        time.sleep(2)
        
        led.on()
        start = time.ticks_ms()
        
        input()
        
        reaction = time.ticks_diff(time.ticks_ms(), start)

        led.off()
        
        print("reaction time:", reaction, "ms")
        
    elif command == "fetch":
        print("##\  # #  ##\  #   #   #   #    ##\  @  /## /#\  | burmal@pico      1.00               ")
        print("# #  # #  # #  #\ /#  / \  #    # #     #   # #  | ------------------------------------")
        print("##\  # #  ##   # # #  ###  #    ##/  #  #   # #  | OS: BurmalPico                      ")
        print("# #  # #  # \  # # #  # #  #    #    #  #   # #  | RAM:", gc.mem_free(), "bytes        ")
        print("##/  \#/  # #  # # #  # #  ###  #    #  \## \#/  | LED:", "ON" if led.value() else "OFF")
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@| LARP MODE: ON                       ")
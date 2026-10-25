from machine import Pin, ADC, PWM
import machine
import time
import _thread
import gc
import os
import random

# Pico W: onboard LED via CYW43; if that fails, fall back to GP25 (plain Pico)
try:
    led = Pin("LED", Pin.OUT)
except (ValueError, TypeError):
    led = Pin(25, Pin.OUT)

# saved LED sequences: slot -> string of 0s and 1s
sequences = {"1": "", "2": "", "3": ""}

# blink generation: a blink thread keeps running only while its number matches blink_gen
blink_gen = 0
blink_running = False

START_MS = time.ticks_ms()

HELP = """Commands:
  help                      show this list
  fetch                     system summary: device, flash, RAM, firmware, chip, temp, uptime
  led on / led off          turn the LED on / off
  led blink                 one blink cycle (0.5 s)
  led blink inf             blink forever
  led fade                  smooth breathing effect via PWM (3 s)
  stop                      stop blinking, LED off
  led bits 1010             play a bit sequence
  led seq save 1 1010       save a sequence to slot 1-3
  led seq 1                 play slot 1
  reaction                  reaction test (press Enter when the LED lights up)
  ls                        files on flash with sizes
  game guess                guess a number 1-20 in 5 tries
  game memory               repeat LED sequences, they get longer
  reboot                    reboot the board"""

GAME_USAGE = "Usage: game guess | game memory"


def is_bits(s):
    return len(s) > 0 and all(c in "01" for c in s)


def stop_blink():
    global blink_gen, blink_running
    blink_gen += 1
    blink_running = False
    led.off()


def start_blink(interval):
    global blink_gen, blink_running
    blink_gen += 1
    blink_running = True
    _thread.start_new_thread(blink_worker, (blink_gen, interval))


def blink_worker(gen, interval):
    while gen == blink_gen:
        led.on()
        time.sleep(interval)
        led.off()
        time.sleep(interval)
    led.off()


def play(bits, step=0.1):
    for ch in bits:
        led.value(1 if ch == "1" else 0)
        time.sleep(step)
    led.off()


def cmd_fade(seconds=3):
    # PWM is needed to change brightness, not just switch the LED on and off
    stop_blink()
    pwm = PWM(led)
    pwm.freq(1000)
    steps = 60
    for i in range(steps):
        pwm.duty_u16(int(65535 * i / steps))
        time.sleep(seconds / (2 * steps))
    for i in range(steps, 0, -1):
        pwm.duty_u16(int(65535 * i / steps))
        time.sleep(seconds / (2 * steps))
    pwm.deinit()
    led.init(Pin.OUT)
    led.off()


def read_temp():
    adc = ADC(4)  # built-in RP2040 temperature sensor
    voltage = adc.read_u16() * 3.3 / 65535
    return 27 - (voltage - 0.706) / 0.001721  # formula from the RP2040 datasheet


def uptime_str():
    total = time.ticks_diff(time.ticks_ms(), START_MS) // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def cmd_fetch():
    u = os.uname()
    st = os.statvfs("/")  # (f_bsize, f_frsize, f_blocks, f_bfree, ...)
    flash_total = st[1] * st[2]
    flash_free = st[1] * st[3]
    ram_free = gc.mem_free()
    ram_total = ram_free + gc.mem_alloc()
    uid = "".join("%02x" % b for b in machine.unique_id())

    art = [
        r"##\  # #  ##\  #   #   #   #    ##\  @  /## /#\  |",
        r"# #  # #  # #  #\ /#  / \  #    # #     #   # #  |",
        r"##\  # #  ##   # # #  ###  #    ##/  #  #   # #  |",
        r"# #  # #  # \  # # #  # #  #    #    #  #   # #  |",
        r"##/  \#/  # #  # # #  # #  ###  #    #  \## \#/  |",
        r"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|",
    ]
    info = [
        "burmal@pico      1.00",
        "-" * 30,
        "Device:   BurmalPico",
        "Board:    " + u.machine,
        "Firmware: %s %s" % (u.sysname, u.release),
        "Flash:    %d KB total, %d KB free" % (flash_total // 1024, flash_free // 1024),
        "RAM:      %d KB total, %d KB free" % (ram_total // 1024, ram_free // 1024),
        "Chip ID:  " + uid,
        "CPU:      %d MHz, %.1f C" % (machine.freq() // 1000000, read_temp()),
        "Uptime:   " + uptime_str(),
        "LED:      " + ("ON" if led.value() else "OFF") + "   LARP MODE: ON",
    ]
    for i in range(max(len(art), len(info))):
        left = art[i] if i < len(art) else ""
        left = left + " " * (56 - len(left))
        right = info[i] if i < len(info) else ""
        print(left + " " + right)


def cmd_ls():
    files = os.listdir()
    if not files:
        print("flash is empty")
        return
    for name in sorted(files):
        print("%-16s %6d bytes" % (name, os.stat(name)[6]))


def cmd_reaction():
    print("Get ready...")
    time.sleep(2)
    led.off()
    time.sleep(2)
    led.on()
    start = time.ticks_ms()
    input()
    reaction = time.ticks_diff(time.ticks_ms(), start)
    led.off()
    print("reaction time:", reaction, "ms")


def game_guess():
    secret = random.randint(1, 20)
    tries = 5
    print("Guess the number from 1 to 20. You have", tries, "tries.")
    while tries > 0:
        raw = input("guess: ").strip()
        if not raw.isdigit():
            print("type a number")
            continue
        n = int(raw)
        tries -= 1
        if n == secret:
            print("You win!")
            for _ in range(3):
                led.on()
                time.sleep(0.15)
                led.off()
                time.sleep(0.15)
            return
        print("higher" if n < secret else "lower", "- tries left:", tries)
    print("Out of tries. The number was", secret)


def game_memory():
    print("Watch the LED (1 = on, 0 = off), then type the same sequence.")
    print("Ctrl+C to quit.")
    length = 1
    while True:
        seq = "".join(random.choice("01") for _ in range(length))
        time.sleep(0.8)
        play(seq, 0.4)
        time.sleep(0.3)
        guess = input("your sequence: ").strip()
        if guess == seq:
            print("correct!")
            length += 1
        else:
            print("wrong. It was", seq, "- score:", length - 1)
            return


def handle(cmd):
    parts = cmd.split()

    if cmd == "":
        return
    if cmd == "help":
        print(HELP)
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "led on":
        stop_blink()
        led.on()
        print("Light: ON")
    elif cmd == "led off":
        stop_blink()
        led.off()
        print("Light: OFF")
    elif cmd == "led blink":
        stop_blink()
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)
        print("Blink complete")
    elif cmd == "led blink inf":
        start_blink(0.1)
        print("Infinite blink: ON (type 'stop' to turn it off)")
    elif cmd == "led fade":
        cmd_fade(3)
        print("Fade done")
    elif cmd == "stop":
        stop_blink()
        print("Blink stopped")
    elif cmd.startswith("led bits "):
        bits = cmd[len("led bits "):].strip()
        if not is_bits(bits):
            print("Error: only 0 and 1 allowed, e.g. led bits 1010")
            return
        stop_blink()
        play(bits)
        print("Played:", bits)
    elif len(parts) == 4 and parts[:3] == ["led", "seq", "save"]:
        print("Usage: led seq save 1 1010")
    elif len(parts) == 5 and parts[:3] == ["led", "seq", "save"]:
        slot, bits = parts[3], parts[4]
        if slot not in sequences:
            print("Slot must be 1, 2 or 3")
        elif not is_bits(bits):
            print("Error: only 0 and 1 allowed")
        else:
            sequences[slot] = bits
            print("Slot", slot, "saved:", bits)
    elif len(parts) == 3 and parts[:2] == ["led", "seq"]:
        slot = parts[2]
        if slot not in sequences:
            print("Slot must be 1, 2 or 3")
        elif not sequences[slot]:
            print("Slot", slot, "is empty")
        else:
            stop_blink()
            play(sequences[slot])
            print("Played slot", slot)
    elif parts[:1] == ["game"]:
        if len(parts) != 2:
            print(GAME_USAGE)
        elif parts[1] == "guess":
            stop_blink()
            game_guess()
        elif parts[1] == "memory":
            stop_blink()
            game_memory()
        else:
            print(GAME_USAGE)
    elif cmd == "ls":
        cmd_ls()
    elif cmd == "reboot":
        print("rebooting...")
        time.sleep(0.5)
        machine.reset()
    elif cmd == "reaction":
        stop_blink()
        cmd_reaction()
    else:
        print("Unknown command:", cmd, "(type 'help' for the list)")


def main():
    print("BurmalPico")
    print("RP2040 online")
    print()
    while True:
        try:
            cmd = input("burmal@pico:~$ ").strip()
            handle(cmd)
        except KeyboardInterrupt:
            print()
            stop_blink()


main()

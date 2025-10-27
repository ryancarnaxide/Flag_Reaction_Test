

import RPi.GPIO as GPIO
import time
import random

# BCM pin list in M1..M10 order
PINS = [5, 6, 16, 17, 20, 21, 22, 23, 24, 25]

# Time between successive offs (seconds)
INTERVAL = 2.0

INVERT = False

def set_on(pin):
    GPIO.output(pin, GPIO.HIGH if not INVERT else GPIO.LOW)

def set_off(pin):
    GPIO.output(pin, GPIO.LOW if not INVERT else GPIO.HIGH)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Set pins as outputs and turn everything ON
    for p in PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
    # ensure ON according to our logic
    for p in PINS:
        set_on(p)

    print("All magnets ON. Randomly turning them OFF every {:.2f}s".format(INTERVAL))
    order = PINS.copy()
    random.shuffle(order)
    print("Random order (BCM):", order)

    try:
        for idx, p in enumerate(order, start=1):
            time.sleep(INTERVAL)
            set_off(p)
            print("Turned OFF {} ({} of {})".format(p, idx, len(PINS)))
        print("Done: all magnets OFF.")
    except KeyboardInterrupt:
        print("Interrupted by user - cleaning up.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()

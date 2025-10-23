"""
io_control.py
--------------
GPIO control helper for Raspberry Pi 5 / CM5 IO Board.

This module provides clean, reusable functions to control GPIO pins
using BCM numbering. It supports both individual and group control
of output pins at 3.3V logic level.

Usage Example:
    import io_control as io

    io.io_setup()
    io.io_all_on()
    io.io_all_off()
    io.io_pin_on(17)
    io.io_pin_off(17)
    io.io_cleanup()
"""

import RPi.GPIO as GPIO
import gpiozero

# -----------------------------------
# GLOBAL CONFIGURATION
# -----------------------------------
# Define all output pins you plan to use (BCM numbering)
OUTPUT_PINS = [5, 6, 16, 17, 20, 21, 22, 23, 24, 25]


# -----------------------------------
# SETUP
# -----------------------------------
def io_setup():
    """Initialize all GPIO pins for output (BCM mode)."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in OUTPUT_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    print(f"[SETUP] GPIO pins {OUTPUT_PINS} configured as OUTPUT.")


# -----------------------------------
# GROUP CONTROL
# -----------------------------------
def io_all_on():
    """Turn all defined output pins HIGH."""
    for pin in OUTPUT_PINS:
        GPIO.output(pin, GPIO.HIGH)
    print(f"[ALL HIGH] Pins {OUTPUT_PINS} set HIGH.")


def io_all_off():
    """Turn all defined output pins LOW."""
    for pin in OUTPUT_PINS:
        GPIO.output(pin, GPIO.LOW)
    print(f"[ALL LOW] Pins {OUTPUT_PINS} set LOW.")


# -----------------------------------
# INDIVIDUAL CONTROL
# -----------------------------------
def io_pin_on(pin):
    """Turn a single GPIO pin HIGH."""
    if pin in OUTPUT_PINS:
        GPIO.output(pin, GPIO.HIGH)
        print(f"[HIGH] GPIO{pin} set HIGH.")
    else:
        print(f"[WARN] GPIO{pin} not in OUTPUT_PINS list.")


def io_pin_off(pin):
    """Turn a single GPIO pin LOW."""
    if pin in OUTPUT_PINS:
        GPIO.output(pin, GPIO.LOW)
        print(f"[LOW] GPIO{pin} set LOW.")
    else:
        print(f"[WARN] GPIO{pin} not in OUTPUT_PINS list.")


# -----------------------------------
# CLEANUP
# -----------------------------------
def io_cleanup():
    """Reset all GPIO pins and release resources."""
    GPIO.cleanup()
    print("[CLEANUP] GPIO resources released.")

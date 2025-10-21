"""
io_control.py
--------------
GPIO control helper for Raspberry Pi Compute Module 5 IO Board (CM5IO).

This module provides simple functions to drive GPIO pins HIGH or LOW.
It assumes a 3.3 V logic level on the standard 40-pin HAT header.

Usage:
    import io_control
    io_control.io_setup(pin_number)
    io_control.io_high(pin_number)
    io_control.io_low(pin_number)
    io_control.io_cleanup()
"""

import RPi.GPIO as GPIO
import time

# -------------------------------
# GPIO Setup
# -------------------------------

def io_setup(pin):
    """Initialize a GPIO pin as output using BCM numbering."""
    GPIO.setmode(GPIO.BCM)       # Broadcom numbering
    GPIO.setup(pin, GPIO.OUT)
    print(f"[SETUP] GPIO{pin} configured as OUTPUT (3.3 V logic).")

# -------------------------------
# Control Functions
# -------------------------------

def io_high(pin):
    """Drive the specified GPIO pin HIGH (3.3 V)."""
    GPIO.output(pin, GPIO.HIGH)
    print(f"[HIGH] GPIO{pin} set HIGH.")

def io_low(pin):
    """Drive the specified GPIO pin LOW (0 V)."""
    GPIO.output(pin, GPIO.LOW)
    print(f"[LOW] GPIO{pin} set LOW.")

# -------------------------------
# Cleanup
# -------------------------------

def io_cleanup():
    """Release GPIO resources and reset pin states."""
    GPIO.cleanup()
    print("[CLEANUP] All GPIO pins reset.")

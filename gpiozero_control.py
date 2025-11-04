from gpiozero import LED
from random import shuffle
from time import sleep
import threading

# === GPIO Pin Mapping (adjust as needed) ===
PINS = [5, 6, 16, 17, 20, 21, 22, 23, 24, 25]
magnets = [LED(pin) for pin in PINS]

def all_on():
    """Turn ON all magnets."""
    for m in magnets:
        m.on()
    print("[GPIOZERO] All magnets ON.")

def all_off():
    """Turn OFF all magnets."""
    for m in magnets:
        m.off()
    print("[GPIOZERO] All magnets OFF.")

def drop_random_sequence(difficulty="Medium", on_complete=None):
    """
    Turn all magnets ON, then drop them randomly one by one
    with timing based on difficulty.
    
    :param difficulty: One of ["Easy", "Medium", "Hard", "Very Hard"]
    :param on_complete: Optional callback to run when finished.
    """
    # Define drop speed per difficulty
    drop_delay = {
        "Easy": 1.0,
        "Medium": 0.7,
        "Hard": 0.45,
        "Very Hard": 0.25
    }.get(difficulty, 0.6)

    def sequence():
        all_on()
        pins = list(magnets)
        shuffle(pins)
        for led in pins:
            sleep(drop_delay)
            led.off()
        print(f"[GPIOZERO] All magnets dropped ({difficulty}).")
        if callable(on_complete):
            on_complete()

    threading.Thread(target=sequence, daemon=True).start()

def cleanup():
    """Ensure all GPIOs are turned off and released."""
    all_off()
    print("[GPIOZERO] Cleanup done.")
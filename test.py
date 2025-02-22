
import time
from pynput import keyboard
import pyfirmata

arduino_port = '/dev/tty6'

# Initialize the board
board = pyfirmata.Arduino(arduino_port)

# Start an iterator thread to prevent serial buffer overflow
it = pyfirmata.util.Iterator(board)
it.start()

# Enable reading from analog pin A5
analog_pin = board.get_pin('a:5:i')  # 'a' for analog, '5' for pin 5, 'i' for input

# Read and print the analog values
try:
    while True:
        value = analog_pin.read()
        if value is not None:
            # Convert to a voltage value (assuming 10-bit ADC with 5V reference)
            voltage = value * 5.0
            print(f"Analog Pin 5 Value: {value}, Voltage: {voltage:.2f}V")
        
        # Delay to avoid spamming the output
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    board.exit()

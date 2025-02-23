# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean racetrack-counter-ui.py

import serial
import serial.tools.list_ports

import tkinter as tk
import time

# Baud rate
baud_rate = 9600

# Threshold value (when the light sensor is shadowed)
shadow_threshold = 700  # Adjust based on your sensor readings

# Timer variables
start_time = None
elapsed_time = None
ready_to_stop = False
ready_to_start_again = True

def find_arduino():
    """Detects the Arduino's COM port and returns the port name."""
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        if "Arduino" in port.description or "usbmodem" in port.device or "usbserial" in port.device:
            print(f"Arduino found on {port.device}")
            return port.device

    print("No Arduino detected. Check your connections.")
    return None

# Auto-detect the Arduino port
arduino_port = find_arduino()

if arduino_port:
    # Open serial connection
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)  # Allow time for the connection to establish
    print("Connected to Arduino!")
else:
    board = None
    analog_pin = None

try:
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode("utf-8").strip()
            try:
                voltage = float(line)
            except ValueError:
                continue
            print(f"\r{voltage:.2f}, ", end="", flush=True)
            # Start the time if the sensor is shadowed
            if voltage <= shadow_threshold:
                if not ready_to_stop and start_time is None and ready_to_start_again:
                    start_time = time.time()
                    elapsed_time = None
                    print("\nTimer started!")
            # Stop the timer if the sensor is shadowed again
                elif ready_to_stop:
                    elapsed_time = time.time() - start_time
                    print(f"\nTimer stopped! Total time: {elapsed_time:.2f} seconds")
                    start_time = None
                    ready_to_stop = False
                    ready_to_start_again = False
            # Restore states when the sensor is lit
            if voltage >= 800:
                # If timer is running, allow the next shadow to stop the timer
                if start_time is not None:
                    ready_to_stop = True
                # If the timer is not running, allow the next shadow to start the timer
                if start_time is None and not ready_to_start_again:
                    ready_to_start_again = True
                    print("Ready to start again")
            # print the elapsed time
            if start_time is not None:
                print(f"\r{time.time() - start_time:.2f}s", end="", flush=True)

except KeyboardInterrupt:
    print("\nStopping...")
    arduino.close()
    





# class TimerUI:
#     def __init__(self):
#         self.root = tk.Tk()
#         self.root.title("Simple Sensor UI")
#         self.root.geometry("400x200")
        
#         self.running = True
        
#         self.label = tk.Label(self.root, text="Measured value: 0", font=("Arial", 20))
#         self.label.pack(pady=20)
        
#         self.quit_button = tk.Button(self.root, text="Quit", command=self.root.destroy, font=("Arial", 15))
#         self.quit_button.pack(pady=10)
        
#         self.update_sensor_value()
#         self.root.mainloop()

#     def update_sensor_value(self):
#         """Updates the sensor value from Arduino and displays it in the UI."""
#         if self.running and board and analog_pin:
#             sensor_value = analog_pin.read()
#             if sensor_value is not None:
#                 # Convert sensor value to a readable format (0-1023 scale)
#                 sensor_readout = int(sensor_value * 1023)
#                 self.label.config(text=f"Measured value: {sensor_readout}")
#             else:
#                 self.label.config(text="Waiting for data...")
            
#         self.root.after(500, self.update_sensor_value)  # Update every 500ms

# # Start the UI
# TimerUI()

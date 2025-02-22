import serial
import time

# Replace 'COM3' with your Arduino's port (e.g., '/dev/ttyUSB0' on Linux)
arduino_port = "/dev/tty.usbmodem21201"
baud_rate = 9600

# Threshold value (when the light sensor is shadowed)
shadow_threshold = 700  # Adjust based on your sensor readings

# Timer variables
start_time = None
elapsed_time = None
ready_to_stop = False
ready_to_start_again = True

# Open serial connection
ser = serial.Serial(arduino_port, baud_rate, timeout=1)
time.sleep(2)  # Allow time for the connection to establish

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").strip()
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
    ser.close()
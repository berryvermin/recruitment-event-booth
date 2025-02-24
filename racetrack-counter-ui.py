# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean racetrack-counter-ui.py

import tkinter as tk
import time
import serial
import threading

class RacetrackUI:
    def __init__(self, arduino_port="COM6", baud_rate=9600):
        # Initialize UI
        self.root = tk.Tk()
        self.root.title("Simple Sensor UI")
        self.root.geometry("800x400")
        
        # Initialize Arduino connection
        self.arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
        self.bright_level = 600
        self.dim_level = 250
        self.shadow_threshold = (self.dim_level + self.bright_level) / 2 if self.dim_level and self.bright_level else 200

        # Timing variables
        self.start_time = None
        self.second_crossing = None
        self.timer_running = False

        self.create_main_screen()
        
        self.root.mainloop()

    def create_main_screen(self):
        """Sets up the main screen widgets."""
        self.name_var = tk.StringVar()

        self.name_label = tk.Label(self.root, text="Enter your name:", font=("Arial", 15))
        self.name_label.pack(pady=5)

        self.name_entry = tk.Entry(self.root, textvariable=self.name_var, font=("Arial", 15))
        self.name_entry.pack(pady=5)

        self.calibrate_button = tk.Button(self.root, text="Calibrate", command=self.calibrate, font=("Arial", 10))
        self.calibrate_button.place(x=10, y=10)

        self.calibration_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.calibration_label.place(x=10, y=370)

        self.start_button = tk.Button(self.root, text="Start", command=self.start_countdown, font=("Arial", 15))
        self.start_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", command=self.root.destroy, font=("Arial", 15))
        self.quit_button.pack(pady=10)

    def calibrate(self):
        self.calib_window = tk.Toplevel(self.root)
        self.calib_window.title("Calibration")
        self.calib_window.geometry("400x200")

        self.calib_label = tk.Label(self.calib_window, text="Clear sensor", font=("Arial", 15))
        self.calib_label.pack(pady=20)
        self.calib_window.update()

        time.sleep(2)
        self.bright_level = self.measure_light()

        self.calib_label.config(text="Cover sensor")
        self.calib_window.update()

        time.sleep(2)
        self.dim_level = self.measure_light()
        print(self.bright_level, self.dim_level)

        self.calib_label.config(text="Calibration complete!")
        self.calib_window.after(2000, self.calib_window.destroy)
        self.calibration_label.config(text="Done calibrating")
        self.root.after(2000, lambda: self.calibration_label.config(text=""))

    def measure_light(self):
        values = []
        self.calib_label.config(text="Measuring...")
        self.calib_window.update()

        start_time = time.time()
        self.arduino.reset_input_buffer()  # Clear any previous data in buffer
        while time.time() - start_time < 2:
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode("utf-8").strip()
                try:
                    voltage = float(line)
                    values.append(voltage)
                except ValueError:
                    continue

        avg_value = sum(values) / len(values) if values else 0
        return avg_value

    def start_countdown(self):
        self.name_label.pack_forget()
        self.name_entry.pack_forget()
        self.calibrate_button.pack_forget()
        self.calibration_label.pack_forget()
        self.start_button.pack_forget()
        self.quit_button.pack_forget()

        # Create a separate window for countdown and measured value
        self.countdown_window = tk.Toplevel(self.root)
        self.countdown_window.title("Countdown and Measurement")
        self.countdown_window.geometry("400x200")

        self.label = tk.Label(self.countdown_window, text="", font=("Arial", 20))
        self.label.pack(pady=20)

        self.countdown(3)

    def countdown(self, count):
        if count > 0:
            self.label.config(text=f"Starting in {count}...")
            self.countdown_window.after(1000, self.countdown, count - 1)
        else:
            self.label.config(text="Starting measurement!")
            self.running = True
            self.sensor_thread = threading.Thread(target=self.read_sensor, daemon=True)
            self.sensor_thread.start()

    def read_sensor(self):
        self.arduino.reset_input_buffer()  # Clear any previous data in buffer
        while self.running:
            # Continuously clear the buffer to prevent old data from being processed
            self.arduino.reset_input_buffer()
            time.sleep(0.01) # FIXME: This does not work properly yet. See what could be done to fix it.
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode("utf-8").strip()
                try:
                    voltage = float(line)
                except ValueError:
                    continue

                self.update_ui(voltage)

                if voltage <= self.shadow_threshold:
                    # Start the time if the sensor is shadowed for the first time
                    if self.start_time is None:
                        self.start_time = time.time()
                        self.timer_running = True
                    # Stop the timer if the sensor is shadowed again
                    elif self.second_crossing:
                        self.second_crossing = time.time()
                        elapsed_time = self.second_crossing - self.start_time
                        self.running = False
                        self.show_result_screen(elapsed_time)

                if voltage >= self.shadow_threshold:
                    # If timer is running, allow the next shadow to stop the timer
                    if self.timer_running is True:
                        self.second_crossing = True

    def update_ui(self, voltage):
        self.countdown_window.after(0, self.label.config, {"text": f"Measured value: {voltage:.2f}"})
        print(voltage)

    def show_result_screen(self, elapsed_time): # TODO: Push results to gsheet
        # Create a new window for the result
        result_window = tk.Toplevel(self.root)
        result_window.title("Measurement Result")
        result_window.geometry("400x200")

        name = self.name_var.get()
        result_label = tk.Label(result_window, text=f"{name}, your time: {elapsed_time:.2f} sec", font=("Arial", 15))
        result_label.pack(pady=20)

        # Add an Exit button to return to the main screen
        exit_button = tk.Button(result_window, text="Exit", command=lambda: self.return_to_main(result_window), font=("Arial", 15))
        exit_button.pack(pady=10)

    def return_to_main(self, result_window):
        # Close the result window
        result_window.destroy()

        # Reset timer variables
        self.start_time = None
        self.second_crossing = None
        self.timer_running = False

        # Re-display the main screen widgets
        self.create_main_screen()


    def stop(self):
        self.running = False
        self.arduino.close()
        self.root.quit()

if __name__ == "__main__":
    RacetrackUI()

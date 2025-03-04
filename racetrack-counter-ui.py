# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean racetrack-counter-ui.py

import asyncio
import requests
import serial
import threading
import time
import tkinter as tk

class RacetrackUI:
    def __init__(self, arduino_port="COM6", baud_rate=115200):
        # Initialize UI
        self.root = tk.Tk()
        self.root.title("Simple Sensor UI")
        self.root.geometry("800x400")
        
        # Initialize Arduino connection
        self.arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
        self.bright_level = 600
        self.dim_level = 250
        self.shadow_threshold = (self.dim_level + self.bright_level) / 2
        self.number_laps = 10

        self.create_main_screen()
        
        self.root.mainloop()

    def create_main_screen(self):
        """Sets up the main screen widgets."""
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.track_var = tk.StringVar()

        self.name_label = tk.Label(self.root, text="Enter your name:", font=("Arial", 15))
        self.name_label.pack(pady=5)

        self.name_entry = tk.Entry(self.root, textvariable=self.name_var, font=("Arial", 15))
        self.name_entry.pack(pady=5)

        self.email_label = tk.Label(self.root, text="Enter your email:", font=("Arial", 15))
        self.email_label.pack(pady=5)

        self.email_entry = tk.Entry(self.root, textvariable=self.email_var, font=("Arial", 15))
        self.email_entry.pack(pady=5)

        self.track_label = tk.Label(self.root, text="Enter track name:", font=("Arial", 15))
        self.track_label.pack(pady=5)

        self.track_entry = tk.Entry(self.root, textvariable=self.track_var, font=("Arial", 15))
        self.track_entry.pack(pady=5)

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

        self.calib_label = tk.Label(self.calib_window, text="Clear sensor please", font=("Arial", 15))
        self.calib_label.pack(pady=20)
        self.calib_window.update()

        time.sleep(3)
        self.bright_level = self.measure_light()

        self.calib_label.config(text="Cover sensor please")
        self.calib_window.update()

        time.sleep(3)
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
        self.email_label.pack_forget()
        self.email_entry.pack_forget()
        self.track_label.pack_forget()
        self.track_entry.pack_forget()
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

        # Timing variables
        timer_running = False
        start_time = None
        
        # Temporary parameters
        voltage = None
        lap_count = 0
        previous_light = "bright"

        while self.running:
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode("utf-8").strip()
                try:
                    voltage = float(line)
                except ValueError:
                    continue
            
            if voltage is not None:
                self.root.after(0, self.update_ui, voltage, lap_count) # TODO: Add timer + previous laptimes to UI

                if voltage <= self.shadow_threshold and previous_light == "bright":
                    if not timer_running:
                        timer_running = True
                        start_time = time.time()
                    lap_count += 1
                    if lap_count >= self.number_laps + 1:
                        elapsed_time = time.time() - start_time
                        self.running = False
                        timer_running = False
                        self.show_result_screen(elapsed_time)
                    previous_light = "dim"

                if voltage >= self.shadow_threshold:
                    previous_light = "bright"

    def update_ui(self, voltage, lap_count):
        self.countdown_window.after(0, self.label.config, {"text": f"Measured value: {voltage:.2f}\nCurrent lap: {lap_count}"})

    def show_result_screen(self, elapsed_time): # TODO: Add all previous laptimes to the result screen
        # Create a new window for the result
        self.result_window = tk.Toplevel(self.root)
        self.result_window.title("Measurement Result")
        self.result_window.geometry("400x200")

        name = self.name_var.get()
        email = self.email_var.get()
        track = self.track_var.get()
        result_label = tk.Label(self.result_window, text=f"{name}, your time: {elapsed_time:.2f} sec", font=("Arial", 15))
        result_label.pack(pady=20)
        
        # Add an Exit button to return to the main screen
        exit_button = tk.Button(self.result_window, text="Exit", command=lambda: self.return_to_main(name, email, track, elapsed_time), font=("Arial", 15))
        exit_button.pack(pady=10)
        
    def return_to_main(self, name, email, track, elapsed_time):
        # Push results to Google Sheets
        self.push_to_gsheet(name, email, track, elapsed_time)
        # Close the result window
        self.result_window.destroy()
        self.countdown_window.destroy()

        # Reset timer variables
        self.start_time = None
        self.second_crossing = None
        self.timer_running = False

        # Re-display the main screen widgets
        self.create_main_screen()

    def push_to_gsheet(self, name, email, track, elapsed_time):
        url = "https://script.google.com/macros/s/AKfycbyUeNjw-wHF3ODJ8TyBLEv41bUDjciQFqEs-wXTWizN1E8xFT3KzA9a11YNHTarRBxUPw/exec"

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        hundredths = int((elapsed_time * 100) % 100)
        formatted_time = f"{minutes:02}:{seconds:02}:{hundredths:02}"

        payload = {
            "sheet": "Gamification",
            "action": "add",
            "values": {
                "Timestamp": timestamp,
                "Name": name,
                "E-mail": email,
                "Track": track,
                "Time": formatted_time,
            }
        }
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, json=payload, headers=headers)

    def stop(self):
        self.running = False
        self.arduino.close()
        self.root.quit()

if __name__ == "__main__":
    RacetrackUI()

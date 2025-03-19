# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean racetrack-counter-ui.py

import requests
import serial
import serial.tools.list_ports
import threading
import time
import tkinter as tk
from tkinter import messagebox
import webbrowser


def find_arduino():
    """Detects the Arduino's COM port and returns the port name."""
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if (
            "Arduino" in port.description
            or "usbmodem" in port.device
            or "usbserial" in port.device
        ):
            print(f"Arduino found on {port.device}")
            return port.device

    print("No Arduino detected. Check your connections.")
    return None

def center_window(window, window_width, window_height):
    # Center the window on the screen
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    window.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")


class RacetrackUI:  # TODO (nice-to-have): Auto full screen / hide X button
    # TODO (nice-to-have): Add sound effects for countdown and lap detection
    def __init__(self, baud_rate=115200):
        # Initialize UI
        self.root = tk.Tk()
        self.root.title("Racetrack timer UI")
        center_window(self.root, 800, 400)

        # Initialize Arduino connection
        arduino_port = find_arduino()
        self.arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
        self.bright_level = 600
        self.dim_level = 100
        self.shadow_threshold = (self.dim_level + self.bright_level) / 2
        self.number_laps = 10
        self.ui_update_period = 0.1
        self.debounce_time = 0.5

        self.create_main_screen()

        self.root.mainloop()

    def create_main_screen(self):
        """Sets up the main screen widgets."""
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.track_var = tk.StringVar()
        self.consent_var = tk.BooleanVar()

        self.name_label = tk.Label(
            self.root, text="Enter your name:", font=("Arial", 15)
        )
        self.name_label.pack(pady=5)

        self.name_entry = tk.Entry(
            self.root, textvariable=self.name_var, font=("Arial", 15)
        )
        self.name_entry.pack(pady=5)

        self.email_label = tk.Label(
            self.root, text="Enter your email:", font=("Arial", 15)
        )
        self.email_label.pack(pady=5)

        self.email_entry = tk.Entry(
            self.root, textvariable=self.email_var, font=("Arial", 15)
        )
        self.email_entry.pack(pady=5)

        self.consent_check = tk.Checkbutton(
            self.root,
            text="I consent to the collection of my information for the purpose of contacting me for relevant job opportunities. My information will be stored for 2 years. I can withdraw my consent at any time.",
            variable=self.consent_var,
            font=("Arial", 10),
            wraplength=400,
        )
        self.consent_check.pack(pady=10)

        self.privacy_statement = tk.Label(
            self.root,
            text="Check out the privacy statement for more information on how Picnic handles your personal data.",
            font=("Arial", 10),
            fg="blue",
            cursor="hand2",
        )
        self.privacy_statement.pack(pady=5)
        self.privacy_statement.bind(
            "<Button-1>", lambda e: self.open_privacy_statement()
        )

        # self.track_label = tk.Label(self.root, text="Enter track name:", font=("Arial", 15))
        # self.track_label.pack(pady=5)

        # self.track_entry = tk.Entry(self.root, textvariable=self.track_var, font=("Arial", 15))
        # self.track_entry.pack(pady=5)

        self.calibrate_button = tk.Button(
            self.root, text="Calibrate", command=self.calibrate, font=("Arial", 10)
        )
        self.calibrate_button.place(x=10, y=10)

        self.calibration_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.calibration_label.place(x=10, y=370)

        self.start_button = tk.Button(
            self.root, text="Start", command=self.validate_inputs, font=("Arial", 15)
        )
        self.start_button.pack(pady=10)

        self.quit_button = tk.Button(
            self.root, text="Quit", command=self.root.destroy, font=("Arial", 15)
        )
        self.quit_button.pack(pady=10)

    def open_privacy_statement(self):
        webbrowser.open("https://jobs.picnic.app/en/privacy-policy")

    def validate_inputs(self):
        """Validates the input fields before starting the measurement."""
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        consent = self.consent_var.get()
        # track = self.track_var.get().strip()

        if not name:
            messagebox.showerror("Input Error", "Name cannot be empty.")
            return
        if not email or "@" not in email or "." not in email:
            messagebox.showerror("Input Error", "Please enter a valid email address.")
            return
        if not consent:
            messagebox.showerror("Input Error", "Please check the consent box.")
            return
        # if not track:
        #     tk.messagebox.showerror("Input Error", "Track name cannot be empty.")
        #     return

        self.start_measurement()

    def calibrate(self):
        self.calib_window = tk.Toplevel(self.root)
        self.calib_window.title("Calibration")
        center_window(self.calib_window, 400, 200)

        self.calib_label = tk.Label(
            self.calib_window, text="Clear sensor please", font=("Arial", 15)
        )
        self.calib_label.pack(pady=20)
        self.calib_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.calib_window.update()

        time.sleep(3)
        self.bright_level = self.measure_light()

        self.calib_label.config(text="Cover sensor please")
        self.calib_window.update()

        time.sleep(3)
        self.dim_level = self.measure_light()
        self.shadow_threshold = (self.dim_level + self.bright_level) / 2
        print(f"Bright level: {self.bright_level:.0f}, dim level: {self.dim_level:.0f}, shadow threshold: {self.shadow_threshold:.0f}")

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

    def start_measurement(
        self,
    ):
        self.name_label.pack_forget()
        self.name_entry.pack_forget()
        self.email_label.pack_forget()
        self.email_entry.pack_forget()
        self.consent_check.pack_forget()
        self.privacy_statement.pack_forget()
        # self.track_label.pack_forget()
        # self.track_entry.pack_forget()
        self.calibrate_button.pack_forget()
        self.calibration_label.pack_forget()
        self.start_button.pack_forget()
        self.quit_button.pack_forget()

        # Create a separate window for measurement
        self.measurement_window = tk.Toplevel(self.root)
        self.measurement_window.title("Measurement")
        center_window(self.measurement_window, 400, 200)        

        self.label = tk.Label(self.measurement_window, text="", font=("Arial", 20))
        self.label.pack(pady=20)

        self.running = True
        self.sensor_thread = threading.Thread(target=self.read_sensor, daemon=True)
        self.sensor_thread.start()

    def read_sensor(self):
        self.arduino.reset_input_buffer()  # Clear any previous data in buffer

        # Timing variables
        timer_running = False
        last_ui_update_time = time.time()
        start_time = 0
        last_lap_time = 0
        
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
                current_time = time.time()
                print(f"Measured value: {voltage:.2f}")

                # Detect light-to-dark transition (shadow detected), with at least 0.5 seconds between laps
                if voltage <= self.shadow_threshold and previous_light == "bright" and current_time - last_lap_time >= self.debounce_time:
                    if not timer_running:
                        timer_running = True
                        start_time = current_time
                    lap_count += 1
                    print(f"Lap count switch to: {lap_count}, time: {(current_time - start_time):.2f}")
                    if lap_count >= self.number_laps + 1:
                        elapsed_time = current_time - start_time
                        self.running = False
                        timer_running = False
                        self.show_result_screen(elapsed_time)
                    previous_light = "dim"
                    last_lap_time = current_time

                # Detect dark-to-light transition (reset state)
                if voltage >= self.shadow_threshold:
                    previous_light = "bright"

                # UI update only every self.ui_update_period seconds
                if current_time - last_ui_update_time > self.ui_update_period:
                    self.root.after(0, self.update_ui, lap_count, start_time)
                    last_ui_update_time = current_time
                
                # Reset voltage so we only trigger this loop when values come in
                voltage = None
                time.sleep(0.005)

    def update_ui(self, lap_count, start_time):
        header = "Race underway!"
        if start_time == 0:
            elapsed_time = 0
            header = "Ready when you are!"
        else:
            elapsed_time = time.time() - start_time
        self.measurement_window.after(
            0, 
            self.label.config,
            {
                "text": f"{header}\n\nElapsed time: {elapsed_time:.1f} s\nCurrent lap: {lap_count} / {self.number_laps}"
            },
        )

    def show_result_screen(self, elapsed_time):
        # Create a new window for the result
        self.result_window = tk.Toplevel(self.root)
        self.result_window.title("Measurement Result")
        center_window(self.result_window, 400, 200)

        name = self.name_var.get()
        email = self.email_var.get()
        result_label = tk.Label(
            self.result_window,
            text=f"{name}, your time: {elapsed_time:.2f} sec",
            font=("Arial", 15),
        )
        result_label.pack(pady=20)

        # Add a button to discard the measurement and return to the main screen
        discard_button = tk.Button(
            self.result_window,
            text="Discard measurement",
            command=self.return_to_main,
            font=("Arial", 15),
        )
        discard_button.pack(pady=10)

        # Add a button to upload the time to the leaderboard and exit
        upload_button = tk.Button(
            self.result_window,
            text="Upload time to leaderboard and exit",
            command=lambda: self.return_to_main(
                name=name, email=email, track=1, elapsed_time=elapsed_time
            ),
            font=("Arial", 15),
        )
        upload_button.pack(pady=10)

    def return_to_main(self, name=None, email=None, track=None, elapsed_time=None):
        if name and email and track and elapsed_time:
            # Push results to Google Sheets
            self.push_to_gsheet(name, email, track, elapsed_time)
        
        # Close the result window
        self.result_window.destroy()
        self.measurement_window.destroy()

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
            "sheet": "Track",
            "action": "add",
            "values": {
                "Timestamp": timestamp,
                "Name": name,
                "E-mail": email,
                "Track": track,
                "Time": formatted_time,
            },
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

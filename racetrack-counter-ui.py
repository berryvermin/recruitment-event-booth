# Should be exported as a standalone executable
# Can be done by running: pyinstaller --onefile --console --clean racetrack-counter-ui.py

import tkinter as tk
import time

class TimerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Simple sensor UI")
        self.root.geometry("400x200")
        
        self.start_time = time.time()
        self.running = True
        
        self.label = tk.Label(self.root, text="Measured value: 0", font=("Arial", 20))
        self.label.pack(pady=20)
        
        self.quit_button = tk.Button(self.root, text="Quit", command=self.root.destroy, font=("Arial", 15))
        self.quit_button.pack(pady=10)
        
        self.update_timer()
        self.root.mainloop()

    def update_timer(self):
        if self.running:
            sensor_readout = int(time.time() - self.start_time)
            self.label.config(text=f"Measured value: {sensor_readout}")
            self.root.after(1000, self.update_timer)

# Start the timer UI
TimerUI()

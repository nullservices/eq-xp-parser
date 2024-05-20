import time
import re
import tkinter as tk
from threading import Thread
from tkinter import font, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
import csv
from datetime import datetime

# Configuration file path
config_file_path = "config.json"

# Regular expression patterns to match log entries
xp_gain_pattern = re.compile(r'\[.*\] You gain experience! \((.*?)%\)')
kill_pattern = re.compile(r'\[.*\] You have slain (.*)!')
death_pattern = re.compile(r'You have been slain')
zone_pattern = re.compile(r'\[.*\] You have entered (.*).')

# Initialize variables to keep track of XP, kills, deaths, and zones
total_xp = 0.0
kill_count = 0
death_count = 0
last_xp_gain = 0.0
last_xp_time = ""
last_mob_killed = ""
current_zone = "Unknown"
start_time = time.time()
session_log = []
csv_file = None
csv_writer = None
logging_active = False

# Load display preferences
display_preferences = {
    "XP per Hour": True,
    "Last XP Gained": True,
    "Last Mob Killed": True,
    "Total XP Gained": True,
    "Total Mobs Killed": True,
    "Total Deaths": True,
    "Current Zone": True
}

# Variables to hold the state of checkboxes
checkbox_vars = {}

def load_config():
    """Load the configuration from a file."""
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save the configuration to a file."""
    with open(config_file_path, 'w') as f:
        json.dump(config, f)

def select_log_file():
    """Open a file dialog to select the log file."""
    return filedialog.askopenfilename(title="Select Log File", filetypes=[("Log files", "*.txt"), ("All files", "*.*")])

def initialize_log_file():
    """Initialize the log file path, prompting the user to select it if not set."""
    config = load_config()
    log_file_path = config.get("log_file_path")
    if not log_file_path or not os.path.exists(log_file_path):
        if messagebox.askyesno("Select Log File", "Log file not found. Do you want to select a log file?"):
            log_file_path = select_log_file()
            if not log_file_path:
                messagebox.showerror("Error", "Log file must be selected to run the application.")
                root.quit()
            config["log_file_path"] = log_file_path
            save_config(config)
        else:
            messagebox.showerror("Error", "Log file must be selected to run the application.")
            root.quit()
    return log_file_path

log_file_path = initialize_log_file()

def extract_character_and_server_names(log_file_path):
    """Extract character and server names from the log file name."""
    basename = os.path.basename(log_file_path)
    match = re.match(r'eqlog_(.+)_(.+)\.txt', basename)
    if match:
        return match.group(1), match.group(2)
    return None, None

character_name, server_name = extract_character_and_server_names(log_file_path)

def generate_log_filename():
    """Generate a CSV log filename based on the character and server names and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_log_{character_name}_{server_name}_{timestamp}.csv"

def start_session_log():
    """Start the session log by opening a CSV file in append mode."""
    global csv_file, csv_writer
    filename = generate_log_filename()
    csv_file = open(filename, 'a', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Type", "Timestamp", "Zone", "XP Gain", "Mob Killed"])
    messagebox.showinfo("Log Started", f"Session log started: {filename}")

def close_session_log():
    """Close the session log."""
    global csv_file
    if csv_file:
        csv_file.close()
        csv_file = None
        messagebox.showinfo("Log Closed", "Session log closed.")

def toggle_logging():
    global logging_active
    if logging_active:
        close_session_log()
        toggle_log_button.config(text="Start Logging Session to CSV", bg="#FF6347")
    else:
        start_session_log()
        toggle_log_button.config(text="Stop Logging Session to CSV", bg="green")
    logging_active = not logging_active

def monitor_log_file():
    global total_xp, kill_count, death_count, last_xp_gain, last_xp_time, last_mob_killed, current_zone, start_time, session_log, csv_writer
    with open(log_file_path, 'r') as file:
        # Move the cursor to the end of the file
        file.seek(0, 2)

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.01)  # Reduce sleep interval for more frequent checking
                continue
            
            # Check for XP gain
            xp_match = xp_gain_pattern.search(line)
            if xp_match:
                last_xp_gain = float(xp_match.group(1))
                last_xp_time = time.strftime("%Y-%m-%d %H:%M:%S")
                total_xp += last_xp_gain
                kill_count += 1
                update_gui()
            
            # Check for kills
            kill_match = kill_pattern.search(line)
            if kill_match and last_xp_gain != 0.0:
                mob_name = kill_match.group(1)
                last_mob_killed = mob_name
                session_log.append(("Kill", last_xp_time, current_zone, last_xp_gain, mob_name))
                if csv_writer:
                    csv_writer.writerow(["Kill", last_xp_time, current_zone, last_xp_gain, mob_name])
                last_xp_gain = 0.0  # Reset the last_xp_gain to avoid multiple associations
                update_gui()
            
            # Check for deaths
            if death_pattern.search(line):
                death_count += 1
                session_log.append(("Death", time.strftime("%Y-%m-%d %H:%M:%S"), current_zone, "", ""))
                if csv_writer:
                    csv_writer.writerow(["Death", time.strftime("%Y-%m-%d %H:%M:%S"), current_zone, "", ""])
                update_gui()
            
            # Check for zone changes
            zone_match = zone_pattern.search(line)
            if zone_match:
                current_zone = zone_match.group(1)
                session_log.append(("Zone", time.strftime("%Y-%m-%d %H:%M:%S"), current_zone, "", ""))
                if csv_writer:
                    csv_writer.writerow(["Zone", time.strftime("%Y-%m-%d %H:%M:%S"), current_zone, "", ""])
                update_gui()

            # Update GUI to show XP per hour
            update_gui()

def update_gui():
    elapsed_time = (time.time() - start_time) / 3600  # Convert to hours
    xp_per_hour = total_xp / elapsed_time if elapsed_time > 0 else 0
    if display_preferences["XP per Hour"]:
        xp_per_hour_label.config(text=f"XP per Hour: {xp_per_hour:.2f}%")
        xp_per_hour_label.grid()
    else:
        xp_per_hour_label.grid_remove()
    if display_preferences["Last XP Gained"]:
        last_xp_gained_label.config(text=f"Last XP Gained: {last_xp_gain}%")
        last_xp_gained_label.grid()
    else:
        last_xp_gained_label.grid_remove()
    if display_preferences["Last Mob Killed"]:
        last_mob_killed_label.config(text=f"Last Mob Killed: {last_mob_killed}")
        last_mob_killed_label.grid()
    else:
        last_mob_killed_label.grid_remove()
    if display_preferences["Total XP Gained"]:
        total_xp_gained_label.config(text=f"Total XP Gained: {total_xp:.2f}%")
        total_xp_gained_label.grid()
    else:
        total_xp_gained_label.grid_remove()
    if display_preferences["Total Mobs Killed"]:
        total_kills_label.config(text=f"Total Mobs Killed: {kill_count}")
        total_kills_label.grid()
    else:
        total_kills_label.grid_remove()
    if display_preferences["Total Deaths"]:
        total_deaths_label.config(text=f"Total Deaths: {death_count}")
        total_deaths_label.grid()
    else:
        total_deaths_label.grid_remove()
    if display_preferences["Current Zone"]:
        current_zone_label.config(text=f"Current Zone: {current_zone}")
        current_zone_label.grid()
    else:
        current_zone_label.grid_remove()
    root.update_idletasks()  # Ensure immediate update of the GUI

def reset_counters():
    global total_xp, kill_count, death_count, last_xp_gain, last_xp_time, last_mob_killed, current_zone, start_time, session_log
    total_xp = 0.0
    kill_count = 0
    death_count = 0
    last_xp_gain = 0.0
    last_xp_time = ""
    last_mob_killed = ""
    current_zone = "Unknown"
    start_time = time.time()
    session_log = []
    update_gui()

def start_monitoring():
    monitor_thread = Thread(target=monitor_log_file)
    monitor_thread.daemon = True
    monitor_thread.start()

def open_help_popup():
    help_popup = tk.Toplevel(root)
    help_popup.overrideredirect(True)
    help_popup.geometry("300x300")
    help_popup.configure(bg=background_color)

    def start_move_help(event):
        help_popup.x = event.x
        help_popup.y = event.y

    def stop_move_help(event):
        help_popup.x = None
        help_popup.y = None

    def on_motion_help(event):
        x = (event.x_root - help_popup.x)
        y = (event.y_root - help_popup.y)
        help_popup.geometry("+%s+%s" % (x, y))

    help_popup.bind("<ButtonPress-1>", start_move_help)
    help_popup.bind("<ButtonRelease-1>", stop_move_help)
    help_popup.bind("<B1-Motion>", on_motion_help)
    
    close_button = tk.Button(help_popup, text="X", font=custom_font, command=help_popup.destroy, bg="red", fg="white", relief="flat")
    close_button.place(x=270, y=10)
    
    select_file_button = tk.Button(help_popup, text="Select New Log File", font=custom_font, command=change_log_file, bg="#FF6347", fg="white", relief="flat")
    select_file_button.pack(pady=10)

    view_button = tk.Button(help_popup, text="Toggle Display", font=custom_font, command=lambda: open_view_popup(help_popup), bg="#FF6347", fg="white", relief="flat")
    view_button.pack(pady=10)

    global toggle_log_button
    toggle_log_button = tk.Button(help_popup, text="Start Logging Session to CSV", font=custom_font, command=toggle_logging, bg="#FF6347", fg="white", relief="flat")
    toggle_log_button.pack(pady=10)

    close_app_button = tk.Button(help_popup, text="Close App", font=custom_font, command=root.quit, bg="#FF6347", fg="white", relief="flat")
    close_app_button.pack(pady=10)
    
    creator_label = tk.Label(help_popup, text="Created by: well_below_average", font=custom_font, fg="white", bg=background_color)
    creator_label.pack(side="bottom", pady=10)

def open_view_popup(parent):
    view_popup = tk.Toplevel(parent)
    view_popup.overrideredirect(True)
    view_popup.geometry("250x300")
    view_popup.configure(bg=background_color)

    def start_move_view(event):
        view_popup.x = event.x
        view_popup.y = event.y

    def stop_move_view(event):
        view_popup.x = None
        view_popup.y = None

    def on_motion_view(event):
        x = (event.x_root - view_popup.x)
        y = (event.y_root - view_popup.y)
        view_popup.geometry("+%s+%s" % (x, y))

    view_popup.bind("<ButtonPress-1>", start_move_view)
    view_popup.bind("<ButtonRelease-1>", stop_move_view)
    view_popup.bind("<B1-Motion>", on_motion_view)

    close_button = tk.Button(view_popup, text="X", font=custom_font, command=view_popup.destroy, bg="red", fg="white", relief="flat")
    close_button.place(x=210, y=10)

    tk.Label(view_popup, text="Toggle Display", font=custom_font, fg="white", bg=background_color).pack(pady=10)

    for key in display_preferences.keys():
        var = tk.BooleanVar(value=display_preferences[key])
        checkbox_vars[key] = var
        cb = tk.Checkbutton(view_popup, text=key, font=custom_font, variable=var, fg="white", bg=background_color, command=lambda k=key, v=var: update_display_preference(k, v))
        cb.pack(anchor='w')

    close_button = tk.Button(view_popup, text="Close", font=custom_font, command=view_popup.destroy, bg="#FF6347", fg="white", relief="flat")
    close_button.pack(pady=10, side="bottom")

def update_display_preference(key, var):
    display_preferences[key] = var.get()
    update_gui()

def change_log_file():
    new_log_file_path = select_log_file()
    if new_log_file_path:
        global log_file_path, character_name, server_name
        log_file_path = new_log_file_path
        character_name, server_name = extract_character_and_server_names(log_file_path)
        config = {"log_file_path": log_file_path}
        save_config(config)

def start_move(event):
    root.x = event.x
    root.y = event.y

def stop_move(event):
    root.x = None
    root.y = None

def on_motion(event):
    x = (event.x_root - root.x)
    y = (event.y_root - root.y)
    root.geometry("+%s+%s" % (x, y))

# Set up the GUI
root = tk.Tk()
root.title("EverQuest Log Monitor")

# Remove the window title bar
root.overrideredirect(True)

# Set the window to be transparent
root.attributes('-alpha', 0.9)

# Set the window to be on top of all other windows
root.attributes('-topmost', True)

# Allow moving the window
root.bind("<ButtonPress-1>", start_move)
root.bind("<ButtonRelease-1>", stop_move)
root.bind("<B1-Motion>", on_motion)

# Customize font
custom_font = font.Font(family="Helvetica", size=14, weight="bold")

# Set background color
background_color = "#1E1E1E"
root.configure(bg=background_color)

# Add a frame for better layout management
frame = tk.Frame(root, bg=background_color)
frame.pack(padx=20, pady=20)

# Add labels with custom styling
xp_per_hour_label = tk.Label(frame, text="XP per Hour: 0.00%", font=custom_font, fg="white", bg=background_color)
xp_per_hour_label.grid(row=0, column=0, pady=5, sticky="w")

last_xp_gained_label = tk.Label(frame, text="Last XP Gained: 0.00%", font=custom_font, fg="white", bg=background_color)
last_xp_gained_label.grid(row=1, column=0, pady=5, sticky="w")

last_mob_killed_label = tk.Label(frame, text="Last Mob Killed: ", font=custom_font, fg="white", bg=background_color)
last_mob_killed_label.grid(row=2, column=0, pady=5, sticky="w")

total_xp_gained_label = tk.Label(frame, text="Total XP Gained: 0.00%", font=custom_font, fg="white", bg=background_color)
total_xp_gained_label.grid(row=3, column=0, pady=5, sticky="w")

total_kills_label = tk.Label(frame, text="Total Mobs Killed: 0", font=custom_font, fg="white", bg=background_color)
total_kills_label.grid(row=4, column=0, pady=5, sticky="w")

total_deaths_label = tk.Label(frame, text="Total Deaths: 0", font=custom_font, fg="white", bg=background_color)
total_deaths_label.grid(row=5, column=0, pady=5, sticky="w")

current_zone_label = tk.Label(frame, text="Current Zone: Unknown", font=custom_font, fg="white", bg=background_color)
current_zone_label.grid(row=6, column=0, pady=5, sticky="w")

# Add Reset button
reset_button = tk.Button(frame, text="Reset Session", font=custom_font, command=reset_counters, bg="#FF6347", fg="white", relief="flat")
reset_button.grid(row=7, column=0, pady=20)

# Add Help button
help_button = tk.Button(root, text="?", font=custom_font, command=open_help_popup, bg="#FF6347", fg="white", relief="flat")
help_button.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

# Load and display an image (e.g., an icon or background image)
# Ensure you have an image file named 'background.png' in the same directory as your script
try:
    background_image = Image.open("background.png")
    background_image = background_image.resize((400, 200), Image.ANTIALIAS)
    background_photo = ImageTk.PhotoImage(background_image)
    background_label = tk.Label(root, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
except FileNotFoundError:
    print("Background image not found. Skipping background image.")

# Start monitoring the log file
start_monitoring()

# Run the GUI main loop
root.mainloop()

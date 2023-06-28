# just a spam file to test sections of code

import pystray
import tkinter as tk
from pystray import MenuItem as item
from PIL import Image

# creating a function to open the config dialog
def open_config_dialog():
    # creating a test tkinter window to test the config dialog
    root = tk.Tk()
    root.title('Test Window')
    root.geometry('590x470')
    root.resizable(False, False)

    # creating a frame for the config dialog
    config_frame = tk.Frame(root)
    config_frame.pack()

    # creating a label for the config dialog
    config_label = tk.Label(config_frame, text="Enter your input here:")
    config_label.pack(side=tk.LEFT)

    # creating an entry for the config dialog
    config_entry = tk.Entry(config_frame)
    config_entry.pack(side=tk.LEFT)

    # creating a button for the config dialog
    config_button = tk.Button(root, text="Save")
    config_button.pack()

    # creating a button for the config dialog
    config_button = tk.Button(root, text="Reset")
    config_button.pack()

    root.mainloop()


def on_config(icon, item):
    open_config_dialog()

def on_exit(icon, item):
    icon.stop()

menu = (  
    item('Config', on_config),
    item('Exit', on_exit)
    )

trayimg = Image.open('images\icon-128.png')
menu_icon = pystray.Icon("menuicon", trayimg, "Biome", menu)

menu_icon.run()
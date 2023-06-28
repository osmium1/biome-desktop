import os
import pystray
import tkinter as tk 
import tkinter.messagebox
from PIL import Image
from pystray import MenuItem as item
from CustomFont import RenderFont, render_text
import ipaddress
import sys
import re


# creating flags
global config_dialog_open
global ip_address_saved
config_dialog_open = False

#checking if the ip address file is present at the start of the program 
try:
    with open('ip_address.txt', 'r') as f:
        stored_ip = f.read()
        if stored_ip:
            ip_address_saved = True
        else:
            ip_address_saved = False
except FileNotFoundError:
    ip_address_saved = False

# creating a RenderFont object with the font file and the color of the text
customfont1 = RenderFont(filename='fonts\Joystix Monospace.ttf', fill=(0, 0, 0))


def on_exit():
    # check if config dialog is open 
    if config_dialog_open:
        #display a message box to the user asking them to close the config dialog first
        tk.messagebox.showinfo('Biome', 'Please close the config window before exiting')
        return
    else: 
        print('Tray icon exited')
        menu_icon.stop()
        sys.exit()


def on_config():
    # check if config dialog is open
    if config_dialog_open:
        pass
    else:
        open_config_dialog()

def validate_ip_address(ip_address):
    # Validates an IP address with a port number.
    # Returns True if the IP address is valid and contains a valid port number,
    # otherwise returns False.
    try:
        ip, port = ip_address.split(":")
        ip_obj = ipaddress.ip_address(ip)
        if port.isdigit():
            return True
        else:
            return False
    except ValueError:
        return False
   

def open_config_dialog():

    global config_dialog_open
    config_dialog_open = True

    def save_ip_address():
        global ip_address_saved
        entered_ip = ip_entry.get()
        if validate_ip_address(entered_ip):
            # Save the IP address to a local file
            with open('ip_address.txt', 'w') as f:
                f.write(entered_ip)
                ip_address_saved = True
            ip_entry.config(state='disabled')  # Disable the entry field
            save_button.config(state='disabled')  # Disable the save button
            reset_button.config(state='normal')  # Enable the reset button
        else:
            warning_label.config(text="Invalid IP address")
            warning_label.after(3000, lambda: warning_label.config(text=""))

    def reset_ip_address():
        global ip_address_saved
        ip_entry.config(state='normal')  # Enable the entry field
        ip_entry.delete(0, tk.END)  # Clear the entered IP address
        # Delete the IP address file
        try:
            os.remove('ip_address.txt')
            ip_address_saved = False
        except FileNotFoundError:
            pass


    dialog = tk.Tk()
    dialog.title('Biome Config')
    dialog.geometry('590x470')
    dialog.resizable(False, False)

    titleimg = render_text(customfont1, font_size=60, displaytext='Biome', style='bold')
    titlelabel = tk.Label(dialog, image=titleimg)
    titlelabel.pack()

    ip_frame = tk.Frame(dialog)
    ip_frame.pack()

    ip_label = tk.Label(ip_frame, text="Enter IP Address:")
    ip_label.pack(side=tk.LEFT)

    ip_entry = tk.Entry(ip_frame)
    ip_entry.pack(side=tk.LEFT)

    save_button = tk.Button(dialog, text="Save", command=save_ip_address)
    save_button.pack()

    reset_button = tk.Button(dialog, text="Reset", command=reset_ip_address)
    reset_button.pack()

    warning_label = tk.Label(dialog, fg='red')
    warning_label.pack()

    # Check if an IP address is already stored
    if ip_address_saved:
        #reading the ip address from the file and saving it to stored_ip
        with open('ip_address.txt', 'r') as f:
            stored_ip = f.read()
        ip_entry.insert(0, stored_ip)
        ip_entry.config(state='disabled')
        save_button.config(state='disabled')
        reset_button.config(state='normal')
    else:
        reset_button.config(state='disabled')
        save_button.config(state='normal')

    def on_closing():
        global config_dialog_open
        config_dialog_open = False
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", on_closing)
    dialog.focus_force()
    dialog.mainloop()




menu = (  
    item('Config', on_config),
    item('Exit', on_exit)
    )

trayimg = Image.open('images\icon-128.png')
menu_icon = pystray.Icon("menuicon", trayimg, "Biome", menu)

menu_icon.run()
import os
import pystray
import tkinter as tk 
from PIL import Image
import tkinter.messagebox
from CustomFont import RenderFont, render_text
from pystray import MenuItem as item
import subprocess
import ipaddress
import re


# creating flags
global config_dialog_open
global ip_address_saved
config_dialog_open = False
  
try:
    #checking if the ip address file is present at the start of the program
    with open('ip_address.txt', 'r') as f:
        stored_ip = f.read()
        if stored_ip:
            ip_address_saved = True
        else:
            ip_address_saved = False
except FileNotFoundError:
    ip_address_saved = False


# creating a RenderFont object with the font file
customfont1 = RenderFont(filename='fonts\Joystix Monospace.ttf', fill=(0, 0, 0))


def fetch_clipboard():
    # fetches the most recently copied item from clipboard
    tempwindow = tk.Tk()
    clipboarditem = tempwindow.clipboard_get()
    tempwindow.destroy()
    return clipboarditem


def find_token(clipboard_item):
    # Check if the string matches the pattern "token=XXXXXXSG" anywhere in it
    pattern = r"token=[A-Z0-9]+SG"
    match = re.search(pattern, clipboard_item)
    
    if match:
        # extract token
        token = match.group()
        return token[6:]
    elif clipboard_item.endswith("SG"):
        # only token was copied, extract token
        return clipboard_item
    else:
        # clipboard does not contain the token or link anywhere in it
        return "no_token_found"


def get_token():    
    # fetching
    try:
        clipb_item = fetch_clipboard()
    except:
        print("either clipboard is empty or there was an error in fetching item")
    
    # finding token
    token = find_token(clipb_item)
    if token == "no_token_found":
        tk.messagebox.showinfo('Biome', 'Tree token was not found in your clipboard, please copy it and try again')
        pass
    else :
        # initial checks passed, token achieved
        transmit_link(token)

def trigger_transmission_script(ip_address, token):
    # code to trigger transmission script and send the link to mobile server
    command = ["TransmissionScript.bat", ip_address, token]
    try:
        subprocess.check_output(command, universal_newlines=True, stderr=subprocess.STDOUT)
        print("Link transmitted to {} with token {}".format(ip_address, token))
    except subprocess.CalledProcessError as e:
        print("Link transmission failed")
        print("Tried transmission to {} with token {}".format(ip_address, token))
        print("Error:", e.output)

def transmit_link(tkn):
    global ip_address_saved

    def check_connection():
        # code to check if the server is running and ready to recieve
        # needs server side code to be implemented first, currently returns true by default
        return True
    
    # proceeding if ip address is saved
    if ip_address_saved:
        try:
            #reading the ip address from the file and saving it to stored_ip
            with open('ip_address.txt', 'r') as f:
                stored_ip = f.read()
            print(f'IP Address retrieved: {stored_ip}')
            if check_connection():
                # all checks passed, triggering transmission script
                trigger_transmission_script(stored_ip, tkn)
            else:
                tk.messagebox.showinfo('Biome', 'Could not connect to the server, please check if the biome app server is running on your mobile and your devices are on the same network')
                return
        except FileNotFoundError:
            print("IP Address file not found")
            tk.messagebox.showinfo('Biome', 'IP Address file not found, please save the IP address again')
            ip_address_saved = False
            return
    else:
        print("IP Address not saved")
        tk.messagebox.showinfo('Biome', 'IP Address not saved, please save the IP address first')
        return
    

def on_exit():
    # check if config dialog is open 
    if config_dialog_open:
        #display a message box to the user asking them to close the config dialog first
        tk.messagebox.showinfo('Biome', 'Please close the config window before exiting')
        return
    else: 
        print('Tray icon exited')
        menu_icon.stop()
        os._exit(0)


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
        save_button.config(state='normal')  # Enable the save button
        reset_button.config(state='disabled')  # Disable the reset button
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
    item('Send Link', get_token, default=True),
    item('Config', on_config),
    item('Exit', on_exit)
    )

trayimg = Image.open('images\icon-128.png')
menu_icon = pystray.Icon("menuicon", trayimg, "Biome", menu, HAS_DEFAULT_ACTION=True)

menu_icon.run()


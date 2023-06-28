import pystray
import tkinter as tk 
import tkinter.messagebox
from PIL import Image
from pystray import MenuItem as item
from CustomFont import RenderFont, render_text
import sys

# creating a flag to know if the config dialog is open or not
global config_dialog_open
config_dialog_open = False

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
    

def open_config_dialog():    
    global config_dialog_open
    config_dialog_open = True

    # create the dialog window 
    dialog = tk.Tk()
    dialog.title('Biome Config')
    dialog.geometry('590x470')
    dialog.resizable(False, False)

    # making a title label for the dialog window
    titleimg = render_text(customfont1, font_size=60, displaytext='Biome', style='bold')
    titlelabel = tk.Label(dialog, image=titleimg)
    titlelabel.pack()
    
    # set the dialog open flag to false when user closes the dialog window
    def on_closing():
        global config_dialog_open
        config_dialog_open = False
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", on_closing)
    dialog.mainloop()

menu = (  
    item('Config', on_config),
    item('Exit', on_exit)
    )

trayimg = Image.open('images\icon-128.png')
menu_icon = pystray.Icon("menuicon", trayimg, "Biome", menu)

menu_icon.run()
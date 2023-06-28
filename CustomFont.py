# This file contains RenderFont class which is used to render text using a custom font
# how to use:
# import RenderFont and render_text from this file
# create a RenderFont object with the font file
# use render_text function to render the text
# the output is a tkinter image object

# [step 1] font = RenderFont(filename='fontname.ttf', fill=(0, 0, 0))

# [step 2] saving the rendered image in a variable (this is a tkinter image object)
# img = render_text(customfont1, font_size=30, displaytext='Settings', style='bold')

from PIL import Image, ImageDraw, ImageFont, ImageTk

class RenderFont:

    def __init__(self, filename, fill=(0, 0, 0)):

        # constructor for RenderFont
        # filename: the filename to the ttf font file
        # fill: the color of the text

        self._file = filename
        self._fill = fill
        self._image = None
        
    def get_render(self, font_size, txt, style="normal"):

        # returns a transparent PIL image that contains the text
        # font_size: the size of text
        # txt: the actual text
        # type_: the type of the text, "normal" or "bold"

        if type(txt) is not str:
            raise TypeError("text must be a string")

        if type(font_size) is not int:
            raise TypeError("font_size must be a int")

        width = len(txt)*font_size
        height = font_size+5

        font = ImageFont.truetype(font=self._file, size=font_size)
        self._image = Image.new(mode='RGBA', size=(width, height), color=(255, 255, 255))

        rgba_data = self._image.getdata()
        newdata = []

        for item in rgba_data:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newdata.append((255, 255, 255, 0))

            else:
                newdata.append(item)

        self._image.putdata(newdata)

        draw = ImageDraw.Draw(im=self._image)

        if style == "normal":
            draw.text(xy=(width/2, height/2), text=txt, font=font, fill=self._fill, anchor='mm')
        elif style == "bold":
            draw.text(xy=(width/2, height/2), text=txt, font=font, fill=self._fill, anchor='mm', 
            stroke_width=1, stroke_fill=self._fill)

        return self._image
    

# defining a function to directly return the image which takes the created RenderFont object, font size, text to display, style of text as arguments
def render_text(fontobject, font_size, displaytext, style):
    img = fontobject.get_render(font_size=font_size, txt=displaytext, style=style)
    return ImageTk.PhotoImage(img)
    
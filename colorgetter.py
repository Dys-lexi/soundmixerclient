import os
import win32ui
import win32gui
import win32con
from PIL import Image
from collections import Counter

def extract_icon(exe_file):
    #print(exe_file)
    try:
        large, small = win32gui.ExtractIconEx(exe_file, 0)
        

        hicon = large[0]
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hicon)
        im = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGBA',
            (32, 32),
            im,
            'raw',
            'BGRA',
            0,
            1
        )
        win32gui.DestroyIcon(hicon)
    except:
        return 0
    return img


def get_most_common_color(exe_file):
    img = extract_icon(exe_file)
    if not img:
        return (-1,-1,-1)
    img = list(img.getdata())
    img = [x[:-1] for x in img]
    img = [tuple(round(x/10)*10 for x in y) for y in img]
    img2 = list(img)
    min = 50
    img = [x for x in img if (x[0]>min or x[1]>min or x[2]>min) and (x[0]!=x[1]!=x[2])]
    img3 = list(img)
    img = [x for x in img if abs(x[0]-x[1])>50 or abs(x[0]-x[2])>50 or abs(x[1]-x[2])>50]
    if len(img) < 30:
        img = list(img3)
    if len(img) < 30:
        img = list(img2)
    color = Counter(img).most_common(1)[0][0]
    return color

if __name__ == "__main__":
    exe_file = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    color = get_most_common_color(exe_file)
    print(color)

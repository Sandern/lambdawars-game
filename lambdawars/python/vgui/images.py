""" Small module to store bitmap images. Might be merged with another module later """
from vgui.controls import BitmapImage

imagedb = {}

def GetImage(path):
    if not path:
        return None
    if path in imagedb:
        return imagedb[path]
    imagedb[path] = BitmapImage(0, path)
    return imagedb[path]
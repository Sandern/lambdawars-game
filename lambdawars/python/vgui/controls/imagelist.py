from vgui.controls import IImage

class BlankImage(IImage):
    """ blank image, intentially draws nothing """
    def Paint(self):
        pass
    def SetPos(self, x, y):
        pass
    def GetContentSize(self):
        return 0, 0
    def GetSize(self):
        return 0, 0
    def SetSize(self, wide, tall):
        pass
    def SetColor(self, col):
        pass

class ImageList(object):
    def __init__(self, deleteImagesWhenDone):
        super(ImageList, self).__init__()
        
        self.images = []
        
        self.deleteimageswhendone = deleteImagesWhenDone
        self.AddImage(BlankImage())

    def AddImage(self, image):
        """ adds a new image to the list, returning the index it was placed at """
        self.images.append(image)
        return len(self.images)-1

    def SetImageAtIndex(self, index, image):
        """ sets an image at a specified index, growing and adding NULL images if necessary """
        # allocate more images if necessary
        while len(self.images) <= index:
            self.images.append(None)

        self.images[index] = image

    def GetImageCount(self):
        """ returns the number of images """
        return len(self.images)

    def GetImage(self, imageIndex):
        """ gets an image, imageIndex is of range [0, GetImageCount) """
        return self.images[imageIndex]

    def IsValidIndex(self, imageIndex):
        """ returns true if an index is valid """
        try:
            self.images[imageIndex]
            return True
        except IndexError:
            return False



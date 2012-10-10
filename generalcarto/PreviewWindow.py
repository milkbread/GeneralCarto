from gi.repository import Gtk
import mapnik

class PreviewWindow(Gtk.Window):
    def __init__(self, preview_image):
        self.previewImage = preview_image
        Gtk.Window.__init__(self, title="Preview for extent")
        self.box = Gtk.VBox(spacing=2)
        self.add(self.box)
                        
        self.image = Gtk.Image()
        self.initImage()
        self.box.pack_start(self.image, True, True, 0)
        
        #This is very necessary for an additional windwo...it handles the click on the close button of the window
        self.connect("delete-event", self.closedThisWindow)
        self.closed = True
        
    def closedThisWindow(self, one, two):
        self.closed = True
        self.hide()
        return True #this prevents the window from getting destroyed
        
    def getStatus(self):
        return self.closed
        
    def initImage(self):
        self.image.set_from_file("./data/media/back.png")        
        
    def on_button_reload_clicked(self, widget):
        self.reloadImage()
        
    def getWindow(self):
        return self
        
    def reloadImage(self):
        self.image.set_from_file(self.previewImage)
        
    def showWindow(self):
        self.show_all()
        self.closed = False
        
    def hideWindow(self):
        self.hide()
        self.closed = True
    

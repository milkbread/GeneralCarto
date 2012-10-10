from gi.repository import Gtk
import mapnik

class PreviewWindow(Gtk.Window):
    def __init__(self, preview_image):
        self.previewImage = preview_image
        Gtk.Window.__init__(self, title="Quick preview")
        self.box = Gtk.VBox(spacing=2)
        self.add(self.box)
                        
        self.image = Gtk.Image()
        self.initImage()
        self.box.pack_start(self.image, True, True, 0)
        
        #self.button_reload = Gtk.Button(label="Reload")
        #self.button_reload.connect("clicked", self.on_button_reload_clicked)
        #self.box.pack_start(self.button_reload, True, True, 0)
        
        self.connect("delete-event", self.closedThisWindow)
        self.closed = False
        
    def closedThisWindow(self, one, two):
        self.closed = True
        self.hide()
        return True
        
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
    

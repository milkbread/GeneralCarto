from gi.repository import Gtk
import mapnik
from generalcarto import functions
from generalcarto import rendering

class ExtentWindow(Gtk.Window):
    
    def __init__(self, logfiles, preview_image,  name = "extent_window", file = "./data/ui/Toolbars.glade"):
        self.logfiles = logfiles
        self.previewImage = preview_image
                
        #basics for loading a *.glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(file)
        self.window = self.builder.get_object(name)
        
        self.initializeContents()
        
        self.window.connect("delete-event", self.closedThisWindow)
        self.closed = False

        
    def closedThisWindow(self, one, two):
        self.closed = True
        self.window.hide()
        return True
        
    def getStatus(self):
        return self.closed

    def getWindow(self):
        return self.window
        
    def initializeMapfile(self, mapfile, preview_window_class):
        self.comboboxtext_shape.remove_all()
        self.comboboxtext_postgis.remove_all()
        
        self.preview_window_class = preview_window_class
        self.preview_window_class.initImage()
        
        
        self.mapfile = mapfile
        self.fillComboboxes(mapfile)
        self.window.show_all()
        
        
    def initializeContents(self):
        self.comboboxtext_shape = self.builder.get_object('comboboxtext_shape')
        self.comboboxtext_shape.connect("changed", self.on_comboboxtext_shape_changed)
        self.comboboxtext_postgis = self.builder.get_object('comboboxtext_postgis')
        self.comboboxtext_postgis.connect("changed", self.on_comboboxtext_postgis_changed)
        self.label_srs = self.builder.get_object('label_srs')
        self.label_chosen_extent = self.builder.get_object('label_chosen_extent')
        self.entry_lllo = self.builder.get_object('entry_lllo')
        self.entry_urlo = self.builder.get_object('entry_urlo')
        self.entry_llla = self.builder.get_object('entry_llla')
        self.entry_urla = self.builder.get_object('entry_urla')

    #lets user choose a shapefile, which will be taken to automatically get an extent of the data
    def on_comboboxtext_shape_changed(self, widget):
        self.shapeName = self.comboboxtext_shape.get_active_text()         
        for layer in self.m.layers.__iter__():
            params = layer.datasource.params()
            if params.get('type') == 'shape' and self.extractFileName(params.get('file')) == self.shapeName:
                self.setExtent(layer)
                self.label_chosen_extent.set_text('Extent of %s datasource: \n%s\n(modifiable)'%(params.get('type'), self.shapeName))
                
        # TODO(Ralf) Please implement the quick preview as extra window.
        self.showPreview(self.mapfile)
    
    #lets user choose a table, which will be taken to automatically get an extent of the data
    def on_comboboxtext_postgis_changed(self, widget):
        table = self.comboboxtext_postgis.get_active_text()         
        for layer in self.m.layers.__iter__():
            params = layer.datasource.params()
            if params.get('type') == 'postgis':
                content = 'DB: %s\nTable: %s '%(params.get('dbname'), params.get('table'))
                if content == table:
                    self.setExtent(layer)
                    self.label_chosen_extent.set_text('Extent of %s datasource: \n%s\n(modifiable)'%(params.get('type'), content))
        # TODO(Ralf) Please implement the quick preview as extra window.
        self.showPreview(self.mapfile)
    
    def on_button2_clicked(self, widget):
        self.label2.set_label("Directly changed")

    def on_button3_clicked(self, widget):
        self.label2.set_label("Changed by additional button")


    def changeLabelFromOutside(self, input):
        self.label2.set_label(input)

    def closeWindow(self):
        self.destroy()
    
    def getExtentFromBoxes(self):
        return self.calculateExtent()
        
    def calculateExtent(self):
        c0 = self.prj.forward(mapnik.Coord(float(self.entry_lllo.get_text()),float(self.entry_llla.get_text())))
        c1 = self.prj.forward(mapnik.Coord(float(self.entry_urlo.get_text()),float(self.entry_urla.get_text()))) 
        return (float(c0.x), float(c1.x), float(c0.y), float(c1.y))
        
    def fillComboboxes(self, mapfile):
        
        self.m = mapnik.Map(256,256)
        mapnik.load_map(self.m,mapfile)
        self.prj = mapnik.Projection(self.m.srs)
        for layer in self.m.layers.__iter__():
            self.params = layer.datasource.params()
            type = self.params.get('type')
            if type == 'shape':
                name = self.extractFileName(self.params.get('file'))
                self.comboboxtext_shape.append_text(name)
                self.label_srs.set_text(layer.srs)
            elif type == 'postgis':
                content = 'DB: %s\nTable: %s '%(self.params.get('dbname'), self.params.get('table'))
                self.comboboxtext_postgis.append_text(content)
                self.label_srs.set_text(layer.srs)
            else:
                functions.writeToLog('Please implement the datasourcetype: ('+ type +') to "GeneralcartoWindow.on_comboboxtext_file_changed", it is not done yet!', self.logfiles)
                self.label_srs.set_text('')
                
        
                
    def extractFileName(self, fileString):
        name = fileString.split('/')
        if len(name) < 2:
            name = self.params.get('file').split('\\')
        return name[len(name)-1]
        
    #shows user the extent of chosen datasource in geographical LonLat-Format
    def setExtent(self, chosen_layer):
        try:
            #... of a given shapefile
            #extent = gdal.getExtentFromShape(self.shapefile)
            extent = chosen_layer.datasource.envelope()
            
            #convert extent to geographical coordinates...for displaying them to the user
            c0 = self.prj.inverse(mapnik.Coord(round(extent[0],20),round(extent[1],20)))
            c1 = self.prj.inverse(mapnik.Coord(round(extent[2],20),round(extent[3],20)))            

            #fill the entries with the values of the found extent            
            self.entry_lllo.set_text(str(c0.x))
            self.entry_urlo.set_text(str(c1.x))
            self.entry_llla.set_text(str(c0.y))
            self.entry_urla.set_text(str(c1.y)) 

            functions.writeToLog('Extent successfully determined!', self.logfiles) 
            self.ui.entry_chosen.set_text(self.shapeName)
        except:
            functions.writeToLog('Unable to get extent of shapefile!', self.logfiles) 
            
    #Perform a simple rendering of a single *.png self.image file
    def showPreview(self, mapfile):
        rendering.simpleRendering(self.previewImage, mapfile, self.calculateExtent())
        self.preview_window_class.reloadImage()
        self.preview_window_class.getWindow().show_all()
        
    

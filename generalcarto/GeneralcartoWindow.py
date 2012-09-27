# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('generalcarto')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('generalcarto')

from generalcarto_lib import Window
from generalcarto.AboutGeneralcartoDialog import AboutGeneralcartoDialog
from generalcarto.PreferencesGeneralcartoDialog import PreferencesGeneralcartoDialog
from generalcarto.TilesDialog import TilesDialog
from generalcarto.StyleditDialog import StyleditDialog
from generalcarto import gdal_functions as gdal
from generalcarto import rendering
from generalcarto import functions as func
from generalcarto import postgreFunctions as postgres
import mapnik
from quickly import prompts
from quickly.widgets.dictionary_grid import DictionaryGrid
import glob
import os
import time
import sys

import ogr

from generalcarto.old_and_test_functions import test_multiprocessing

   
        
# See generalcarto_lib.Window.py for more details about how this class works
class GeneralcartoWindow(Window):
    __gtype_name__ = "GeneralcartoWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(GeneralcartoWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutGeneralcartoDialog
        self.PreferencesDialog = PreferencesGeneralcartoDialog 
        
        ####
        #initialize some global variables
        self.checkbutton_open = False        
        self.shapefile = ''
        
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
                
        #initialize the entries for the (simple) self.image size
        self.ui.image1.clear()

        #initialize the entry for the zoomlevels for the tile rendering
        self.ui.entry1.set_text('0')
        self.ui.entry2.set_text('18') 
      
        print 'Mapnik_version = %s' %mapnik.mapnik_version()
        if mapnik.mapnik_version() < 200100:
            print "You're having a too old version of mapnik...install minimum version 2.1.0!!!"
            sys.exit()
        
    ####let the user choose a directory that contains one or more mapnik style files
    def on_button_style_clicked(self, widget, data=None):  
        #let the user choose a self.path with the directory chooser
        response, self.path = prompts.choose_directory()

        #make certain the user said ok before working
        if response == Gtk.ResponseType.OK:
           
           #make a list of the supported xml files
           dicts = dict()
           counter = 0
           #iterate through root directory
           for files in glob.glob(self.path + "/*.xml"):
                    if files.endswith('.xml'):
                        #create a URI in a format gstreamer likes
                        file_uri = self.path
                        fileSplit = files.split(self.path + "/")                        
                        dicts[str(counter)] = fileSplit[1]    
                        counter = counter + 1   
           keylist = dicts.keys()
           keylist.sort() 

            #fill the combotextbox with the xml-files of the initially user-chosen directory
        for key in keylist: 
                #print key, value
               self.ui.comboboxtext_file.append_text(dicts[key])    

    #set style and shape when combobox has changed
    def on_comboboxtext_file_changed(self, widget, data=None):
        self.ui.comboboxtext_shape.remove_all()
        self.ui.comboboxtext_postgis.remove_all()
        #get the chosen stylefile
        self.mapfile = self.ui.comboboxtext_file.get_active_text() 
        #print  self.path+'/'+self.mapfile

        #open style file if user wants to
        if self.checkbutton_open == True:
            os.system('gedit --new-window ' + self.path+'/'+self.mapfile)
        
        self.m = mapnik.Map(256,256)
        mapnik.load_map(self.m,self.path+'/'+self.mapfile)
        self.prj = mapnik.Projection(self.m.srs)
        for layer in self.m.layers.__iter__():
            params = layer.datasource.params()
            type = params.get('type')
            if type == 'shape':
                self.ui.comboboxtext_shape.append_text(params.get('file'))
                self.ui.label_srs.set_text(layer.srs)
            elif type == 'postgis':
                content = 'DB: %s\nTable: %s '%(params.get('dbname'), params.get('table'))
                self.ui.comboboxtext_postgis.append_text(content)
                self.ui.label_srs.set_text(layer.srs)
            else:
                func.writeToLog('Please implement the datasourcetype: ('+ type +') to "GeneralcartoWindow.on_comboboxtext_file_changed", it is not done yet!')
                self.ui.label_srs.set_text('')
  
    #lets user choose a shapefile, which will be taken to automatically get an extent of the data
    def on_comboboxtext_shape_changed(self, widget, data=None):
        
        self.shapefile = self.ui.comboboxtext_shape.get_active_text()         
        for layer in self.m.layers.__iter__():
            params = layer.datasource.params()
            if params.get('type') == 'shape' and params.get('file') == self.shapefile:
                self.setExtent(layer)
        self.showPreview()
    #lets user choose a table, which will be taken to automatically get an extent of the data
    def on_comboboxtext_postgis_changed(self, widget, data=None):
        
        table = self.ui.comboboxtext_postgis.get_active_text()         
        for layer in self.m.layers.__iter__():
            params = layer.datasource.params()
            if params.get('type') == 'postgis':
                content = 'DB: %s\nTable: %s '%(params.get('dbname'), params.get('table'))
                if content == table:
                    self.setExtent(layer)
        self.showPreview()
        
    #Display map tiles with a on-the fly rendering of the concrete 9 tiles that will be displayed
    def on_button_tiles_clicked(self, widget, data=None):
     if self.mapfile != '':
      #if self.shapefile != '':
        extent = []
        
        #get/set the bounding box/extent
        try:            
            c0 = self.prj.forward(mapnik.Coord(float(self.ui.entry_lllo.get_text()),float(self.ui.entry_llla.get_text())))
            c1 = self.prj.forward(mapnik.Coord(float(self.ui.entry_urlo.get_text()),float(self.ui.entry_urla.get_text()))) 
            extent = (float(c0.x), float(c1.x), float(c0.y), float(c1.y))
            print extent
        except:
            self.ui.label8.set_text('Emtpty entry or not as float!')
            self.ui.image1.clear()
        #Go on if extent was setted, respectively no error occured
        if extent != '':    
        #    try:  
#                print 'bbox:'+str(bbox)
                #initialize the information that will be send to the ui
                mapfile = self.path+'/'+self.mapfile
                tile_dir = self.path+'/tiles/'     #'/home/ralf/Software/Quickly/testdaten/tiles/'
                maxZoom = self.ui.entry2.get_text()
                minZoom = self.ui.entry1.get_text()
                #collect all in one string, as this seems to be the only way
                sending = str(extent) + ':' + mapfile + ':' + tile_dir + ':' + minZoom + ':' + maxZoom 
                #print sending
                tiler =  TilesDialog(sending)
                result = tiler.run() 
                #close the dialog, and check whether to proceed        
                tiler.destroy()
                if result != Gtk.ResponseType.OK:
                    return                   
         #   except:
          #      self.ui.label8.set_text('Extent has only emtpty entries or is not given as float!')
           #     self.ui.image1.clear()
      #else:
       # self.ui.label8.set_text('Please choose a shape file!')
     else:
        self.ui.label8.set_text('Please choose a style file!')

        
    def on_checkbutton_open_toggled(self, widget, data=None):
        if self.checkbutton_open == True:
            self.checkbutton_open = False 
        elif self.checkbutton_open == False:
            self.checkbutton_open = True

    def on_button_styledit_clicked(self, widget, data=None):
        if self.mapfile != '':
            styler = StyleditDialog(self.path+'/'+self.mapfile)
            result = styler.run() 
            #close the dialog, and check whether to proceed        
            styler.destroy()
            if result != Gtk.ResponseType.OK:
                return  
                
###Additional Functions

    #Perform a simple rendering of a single *.png self.image file
    def showPreview(self):
        self.image = self.path+'/user_image.png'
        
        try:
            c0 = self.prj.forward(mapnik.Coord(float(self.ui.entry_lllo.get_text()),float(self.ui.entry_llla.get_text())))
            c1 = self.prj.forward(mapnik.Coord(float(self.ui.entry_urlo.get_text()),float(self.ui.entry_urla.get_text()))) 
            extent = (float(c0.x), float(c1.x), float(c0.y), float(c1.y))
            rendering.simpleRendering(self.image, self.path+'/'+self.mapfile, extent)
            self.ui.image1.set_from_file(self.image)  
            #self.ui.label2.set_text('Saved to: ' + self.image)          
        except:
            self.ui.label8.set_text('Extent has emtpty entries or not as float!')
            self.ui.image1.clear()
            
    #shows user the extent of chosen datasource in geographical LonLat-Format
    def setExtent(self, chosen_layer):
        try:
            #... of a given shapefile
            #extent = gdal.getExtentFromShape(self.shapefile)
            extent = chosen_layer.datasource.envelope()
            print extent
            #convert extent to geographical coordinates...for displaying them to the user
            c0 = self.prj.inverse(mapnik.Coord(round(extent[0],20),round(extent[1],20)))
            c1 = self.prj.inverse(mapnik.Coord(round(extent[2],20),round(extent[3],20)))            

            #fill the entries with the values of the found extent            
            self.ui.entry_lllo.set_text(str(c0.x))
            self.ui.entry_urlo.set_text(str(c1.x))
            self.ui.entry_llla.set_text(str(c0.y))
            self.ui.entry_urla.set_text(str(c1.y)) 

            self.ui.label2.set_text('Extent successfully determined!') 
            splitted = self.shapefile.split('/')
            pure_name = splitted[len(splitted)-1]
            self.ui.entry_chosen.set_text(pure_name)
        except:
            self.ui.label2.set_text('Unable to get extent of shapefile!') 


###Testfunctions

    def on_button_short_clicked(self, widget, data=None):
        sending = 'Tool for tile-based on-the-fly-generalisation   \n+(1324637.159999081, 1405011.9800014955, 6477402.360002069, 6546380.469994396):/home/klammer/Software/Quickly/generalcarto/data/media/testdaten/mercator_polygon/slippy_vogtland_with_shapes.xml:/home/klammer/Software/Quickly/generalcarto/data/media/testdaten/mercator_polygon/tiles/:0:18'
        #sending = '(1324637.159999081, 1405011.9800014955, 6477402.360002069, 6546380.469994396):/home/klammer/Software/Quickly/generalcarto/data/media/testdaten/mercator_polygon/vogtland_style_PC-version_withoutpostgre.xml:/home/klammer/Software/Quickly/generalcarto/data/media/testdaten/mercator_polygon/tiles/:0:18'
        
        tiler =  TilesDialog(sending)
        result = tiler.run() 
        #close the dialog, and check whether to proceed        
        tiler.destroy()
        if result != Gtk.ResponseType.OK:
            return 

    def on_button_postgis_clicked(self, widget, data=None):
        #postgres.makePostgresTable()
        
        #postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_2190_1382_12.gml')
   #     postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4376_2766_13.gml')
    #    postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4375_2768_13.gml')
     #   postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4375_2767_13.gml')
      #  postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4375_2766_13.gml')
       # postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4374_2767_13.gml')
        #postgres.writeToPostgres('/home/klammer/Software/Quickly/generalcarto/data/media/cache/xmlfiles/result_4374_2766_13.gml')
        #postgres.postgresTest()
        
        params = {'port': u'5432', 'host': u'localhost', 'user': u'gisadmin', 'table': u'vgtl_lines', 'password': u'tinitus', 'type': u'postgis', 'dbname': u'meingis'}
        extent = (1369751.5468703583, 6457400.14953169, 1408887.3053523686, 6496535.908013698)
        filter = 'true'
        postgres.getDataInfos(params, extent, filter)

    def on_button_mapnik_clicked(self, widget, data=None):
        #rendering.testMapnik()
        test_multiprocessing()
        #rendering.qickTest()
        
        
        
            
    
        

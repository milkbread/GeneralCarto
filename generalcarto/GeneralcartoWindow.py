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
from generalcarto.ExtentWindow import ExtentWindow
from generalcarto.TilesWindow import TilesWindow
from generalcarto.ToolsWindow import ToolsWindow
from generalcarto.PreviewWindow import PreviewWindow 
from generalcarto.StylingWindow import StylingWindow 
from generalcarto.InfoWindow import InfoWindow 

   
        
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
        
        #initialize the entry for the zoomlevels for the tile rendering
        self.ui.entry1.set_text('0')
        self.ui.entry2.set_text('18') 
      
        print 'Mapnik_version = %s' %mapnik.mapnik_version()
        if mapnik.mapnik_version() < 200100:
            print "You're having a too old version of mapnik...install minimum version 2.1.0!!!"
            sys.exit()
         
        #initialize the size of the tile buffer
        self.buffer_size = 128   
        self.ui.entry_buffer.set_text(str(self.buffer_size))
        
            
        home = os.getenv("HOME")
        self.generalHome = home + '/GeneralCarto/'
        if not os.path.isdir(self.generalHome):
            os.mkdir(self.generalHome)
        self.logs = self.generalHome + 'log-files/'
        if not os.path.isdir(self.logs):
            os.mkdir(self.logs)
        self.tile_dir = self.generalHome + 'tiles/' 
        if not os.path.isdir(self.tile_dir):
            os.mkdir(self.tile_dir)
        self.previewImage = self.generalHome + "user_image.png"
        self.path = ""
        
        self.menuItemIndicator = "<  "
        
        self.loadWindows()
        self.ui.spinner1.set_visible(False)
        
        
###Listeners
    ####let the user choose a directory that contains one or more mapnik style files
    def on_button_style_clicked(self, widget, data=None):  
        self.ui.comboboxtext_file.remove_all()
        
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
        #get the chosen stylefile
        mapfile_file = self.ui.comboboxtext_file.get_active_text()
        self.mapfile = self.path+'/'+mapfile_file 
        self.mapnik_map = mapnik.Map(256,256)
        mapnik.load_map(self.mapnik_map, self.mapfile)
        
        #open style file if user wants to
        if self.checkbutton_open == True:
            os.system('gedit --new-window ' + self.mapfile)
        
        self.windowClassExtent.initializeMapfile(self.mapnik_map, self.mapfile, self.windowClassPreview)
        
    def on_button_show_tiles_clicked(self, widget, data=None):
        #This is a debugging boolean...set it to True and you can access it quickly
        quick = False
        
        try:
            extent = self.windowClassExtent.getExtentFromBoxes()        
            maxZoom = int(self.ui.entry2.get_text())
            minZoom = int(self.ui.entry1.get_text())
            buffer = int (self.ui.entry_buffer.get_text())
            self.windowClassTiles.initializeParameters(extent, self.mapnik_map, self.tile_dir, minZoom, maxZoom, buffer, self.generalHome, self.logs)
        except:
            mapnik_map = mapnik.Map(256, 256)
            self.mapnik_map = mapnik_map
            mapnik.load_map(mapnik_map,'/home/klammer/Software/Quickly/generalcarto/data/media/XML-files/slippy_vogtland_with_shapes.xml')  
            self.windowClassTiles.initializeTilesWindow(self.windowClassStyling, self.windowClassInfo)
            self.windowClassTiles.initializeParameters((1323598.4969301731, 1399812.8074293039, 6476253.225965643, 6563857.1150525035), mapnik_map,  '/home/klammer/GeneralCarto/tiles/', 0, 18, self.ui.entry_buffer.get_text(), '/home/klammer/GeneralCarto/',  '/home/klammer/GeneralCarto/log-files/')
            
        
        self.windowClassPreview.hideWindow()
        self.windowClassTools.initializeTilesWindow(self.windowClassTiles)
        self.windowClassTools.showWindow()
        self.windowClassStyling.initializeStylingWindow(self.mapnik_map, self.windowClassTiles, self.windowClassInfo)
        self.windowClassStyling.showWindow()
      
        

                
###Listeners and functions for communicating the external windows            
    def loadWindows(self):
        #initialize the external windows
        self.openPreviewWindow() 
        self.openExtentWindow()
        self.openTileWindow()
        self.openToolsWindow()
        self.openStylingWindow()
        self.openInfoWindow()
        
    def on_mnu_info_activate(self, widget, data=None):
        if self.windowClassInfo.getStatus() == True:
            self.windowClassInfo.showWindow()
        elif self.windowClassInfo.getStatus() == False:
            self.windowClassInfo.hideWindow()        
    def openInfoWindow(self):
        self.windowClassInfo = InfoWindow(self.logs, self)
        
    def on_mnu_extent_activate(self, widget, data=None):
        if self.windowClassExtent.getStatus() == True:
            self.windowClassExtent.showWindow()
        elif self.windowClassExtent.getStatus() == False:
            self.windowClassExtent.hideWindow() 
    def openExtentWindow(self):
        self.windowClassExtent = ExtentWindow(self.logs, self.previewImage, self)
        
    def on_mnu_preview_activate(self, widget, data=None):
        if self.windowClassPreview.getStatus() == True:
            self.windowClassPreview.showWindow()
        elif self.windowClassPreview.getStatus() == False:
            self.windowClassPreview.hideWindow()
    def openPreviewWindow(self):
        self.windowClassPreview = PreviewWindow(self.previewImage, self)
        
    def on_mnu_tiles_activate(self, widget, data=None):
        if self.windowClassTiles.getStatus() == True:
            self.windowClassTiles.showWindow()
        elif self.windowClassTiles.getStatus() == False:
            self.windowClassTiles.hideWindow() 
    def openTileWindow(self):
        self.windowClassTiles = TilesWindow(self.logs, self)
        
    def on_mnu_tools_activate(self, widget, data=None):
        if self.windowClassTools.getStatus() == True:
            self.windowClassTools.showWindow()
        elif self.windowClassTools.getStatus() == False:
            self.windowClassTools.hideWindow() 
    def openToolsWindow(self):
        self.windowClassTools = ToolsWindow(self.logs, self)
        
    def on_mnu_styling_activate(self, widget, data=None):
        if self.windowClassStyling.getStatus() == True:
            self.windowClassStyling.showWindow()
        elif self.windowClassStyling.getStatus() == False:
            self.windowClassStyling.hideWindow() 
    def openStylingWindow(self):
        self.windowClassStyling = StylingWindow(self.logs, self)
    
    def on_button_window_clicked(self, widget, data=None):
        print self.windowClassExtent.getStatus()  
        
    def on_mnu_export_mapfile_activate(self, widget, data=None):
        name = 'GeneralCarto-last-mapfile.xml'
        wobj = open(self.logs+name, 'w')
        wobj.write(mapnik.save_map_to_string(self.mapnik_map))
        wobj.close
        self.ui.label_status.set_text("Mapfile '%s' was exported to: \n\t%s" %(name, self.logs))
        
                
                
###Additional Functions
  
        
    def on_checkbutton_open_toggled(self, widget, data=None):
        if self.checkbutton_open == True:
            self.checkbutton_open = False 
        elif self.checkbutton_open == False:
            self.checkbutton_open = True

    def on_button_styledit_clicked(self, widget, data=None):
        if self.mapfile != '':
            styler = StyleditDialog(self.mapfile)
            result = styler.run() 
            #close the dialog, and check whether to proceed        
            styler.destroy()
            if result != Gtk.ResponseType.OK:
                return    
    
###Test- & Old functions

    #Display map tiles by an on-the fly rendering of the concrete 9 tiles that will be displayed
    def on_button_tiles_clicked(self, widget, data=None):
     if self.mapfile != '':
      #if self.shapefile != '':
        extent = []
        
        #get/set the bounding box/extent
        try:            
            #c0 = self.prj.forward(mapnik.Coord(float(self.ui.entry_lllo.get_text()),float(self.ui.entry_llla.get_text())))
            #c1 = self.prj.forward(mapnik.Coord(float(self.ui.entry_urlo.get_text()),float(self.ui.entry_urla.get_text()))) 
            #extent = (float(c0.x), float(c1.x), float(c0.y), float(c1.y))
            #print extent
            extent = self.windowClassExtent.getExtentFromBoxes()
        except:
            #self.ui.label8.set_text('Emtpty entry or not as float!')
            self.ui.image1.clear()
        #Go on if extent was setted, respectively no error occured
        if extent != '':    
        #    try:  
#                print 'bbox:'+str(bbox)
                #initialize the information that will be send to the ui
                mapfile = self.mapfile
                maxZoom = self.ui.entry2.get_text()
                minZoom = self.ui.entry1.get_text()
                #collect all in one string, as this seems to be the only way
                title = 'Tool for tile-based on-the-fly-generalisation   \n+'
                sending = title + str(extent) + ':' + self.mapfile + ':' + self.tile_dir + ':' + minZoom + ':' + maxZoom + ':' + self.generalHome + ':' + self.logs
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
    #else:
        #self.ui.label8.set_text('Please choose a style file!')

    def on_button_short_clicked(self, widget, data=None):
        sending = 'Tool for tile-based on-the-fly-generalisation   \n+(1324637.159999081, 1405011.9800014955, 6477402.360002069, 6546380.469994396):/home/klammer/Software/Quickly/generalcarto/data/media/XML-files/slippy_vogtland_with_shapes.xml:/home/klammer/GeneralCarto/tiles/:0:18:'+self.generalHome+':'+self.logs
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
        
        
        
            
    
        

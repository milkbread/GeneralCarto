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
from generalcarto import rendering
from generalcarto import TileObjects as tiling
from generalcarto import PreferenceObjects as preferences
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
from generalcarto.WPSWindow import WPSWindow 


from generalcarto import WPScommunication as WPScom
from multiprocessing import Pool
from generalcarto import postgreFunctions    
        
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
         
        #initialize the size of the tile buffer
        self.ui.entry_buffer.set_text(str(128))
        #initialize all folders
        self.folders = preferences.FilesNLogs()
        #initialize all definitions
        self.definitions = preferences.Definitions()
        self.menuItemIndicator = self.definitions.getIndicator()
      
        #initialize the entry for the zoomlevels for the tile rendering
        self.ui.entry1.set_text(self.definitions.getZoomRange()[0])
        self.ui.entry2.set_text(self.definitions.getZoomRange()[1]) 
      
        #check the installed mapnik version
        if mapnik.mapnik_version() < self.definitions.getMinMapnikVersion()[0]:
            print self.definitions.getMinMapnikVersion()[1]
            self.folders.writeToLog(self.definitions.getMinMapnikVersion()[1])
            sys.exit()
        
        self.tileButtonVisibility(False)
        self.initializedMapfile = False
        self.initialLoad = True
        
        
###Listeners
    ####let the user choose a directory that contains one or more mapnik style files
    def on_button_style_clicked(self, widget, data=None): 
        #clean up the combobox
        self.ui.comboboxtext_file.remove_all()
        
        #let the user choose a path with the directory chooser
        response, path = prompts.choose_directory()
        self.folders.setUserPath(path)
        #make certain the user said ok before working
        if response == Gtk.ResponseType.OK:
            #make a list of the supported xml files
            dicts = dict()
            counter = 0
            #iterate through root directory
            for files in glob.glob(self.folders.getUserPath() + "*.xml"):
                if files.endswith('.xml'):
                    #create a URI in a format gstreamer likes
                    file_uri = self.folders.getUserPath()
                    fileSplit = files.split(self.folders.getUserPath())                    
                    dicts[str(counter)] = fileSplit[1]    
                    counter = counter + 1   
            keylist = dicts.keys()
            keylist.sort() 
            #fill the combobox with file names
            for key in keylist: 
                   #print key, value
                   self.ui.comboboxtext_file.append_text(dicts[key])   

            self.ui.label_status.set_text("Chosen path: %s"%self.folders.getUserPath())
        else:
            self.ui.label_status.set_text("No directory chosen")

    #set style and shape when combobox has changed
    def on_comboboxtext_file_changed(self, widget, data=None):
        #get the chosen stylefile
        self.folders.setMapfile(self.ui.comboboxtext_file.get_active_text())
        self.mapnik_map = mapnik.Map(256,256)
        mapnik.load_map(self.mapnik_map, self.folders.getMapfileHome())
        
        #open style file if user wants to
        if self.checkbutton_open == True:
            os.system(self.definitions.getEditor() + ' --new-window ' + self.folders.getMapfileHome())
    
        if self.initialLoad == False:            
            self.destroyWindows()
        else:
            self.initialLoad = False
        self.loadWindows()
        
        self.mapfileInitialized()
        self.tileButtonVisibility(False)
    
    def mapfileInitialized(self):
        
        self.windowClassExtent.initializeMapfile(self.mapnik_map, self.folders.getMapfileHome(), self.windowClassPreview)
        self.windowClassExtent.showWindow()
        self.initializedMapfile = True
        if self.windowClassStyling.getStatus() == False:
            print "Style window reloaded"
            self.windowClassStyling.initializeStylingWindow(self.mapnik_map, self.windowClassTiles, self.windowClassInfo)
        
    def on_button_show_tiles_clicked(self, widget, data=None):
        
        #initialize the Tiling Parameters - tiling.TilingParams(extent, minZoom, maxZoom, mapnik_map)
        self.tileParams = tiling.TilingParams(self.windowClassExtent.getExtentFromBoxes() , int(self.ui.entry1.get_text()), int(self.ui.entry2.get_text()), self.mapnik_map)
        self.tileParams.setBufferSize(int(self.ui.entry_buffer.get_text()))
        #initialize the Tiles Window and its parameters
        self.windowClassTiles.initializeTilesWindow(self.windowClassStyling, self.windowClassInfo)
        self.windowClassTiles.initializeParameters(self.tileParams, self.folders)
        #initialize the Tools Window with the TilesWindow and show it
        self.windowClassTools.initializeTilesWindow(self.windowClassTiles)
        self.windowClassTools.showWindow()
        #close the Preview Window
        self.windowClassPreview.hideWindow()
        
###Listeners and functions for the communicating with the external windows            
    #initialize the external windows
    def loadWindows(self):
        self.openPreviewWindow() 
        self.openExtentWindow()
        self.openTileWindow()
        self.openToolsWindow()
        self.openStylingWindow()
        self.openInfoWindow()
        self.openWPSWindow()
        
    #destroy the external Windows
    def destroyWindows(self):
        self.windowClassExtent.destroyWindow()
        self.windowClassInfo.destroyWindow()
        self.windowClassWPS.destroyWindow()
        self.windowClassPreview.destroyWindow()
        self.windowClassTiles.destroyWindow()
        self.windowClassTools.destroyWindow()
        self.windowClassStyling.destroyWindow()
    
    #WPS Window
    def openWPSWindow(self):
        self.windowClassWPS = WPSWindow(self.folders, self.folders.getXMLFilesHome(), self)
    def on_mnu_geom_trans_activate(self, widget, data=None):
        if self.windowClassWPS.getStatus() == True and self.windowClassTiles.getInitializationStatus() == True:
            self.on_openingGeneralisationWindows(2)
        elif self.windowClassWPS.getStatus() == False:
            self.windowClassWPS.hideWindow()        
    #Information Retrieval Window    
    def openInfoWindow(self):
        self.windowClassInfo = InfoWindow(self.folders.getLogfilesHome(), self)
    def on_mnu_geom_info_activate(self, widget, data=None):
        if self.windowClassInfo.getStatus() == True and self.windowClassTiles.getInitializationStatus() == True:
            self.on_openingGeneralisationWindows(1)
        elif self.windowClassInfo.getStatus() == False:
            self.windowClassInfo.hideWindow()        
    #Function that opens the Styling Window for WPS or InformationRetrieval
    def on_openingGeneralisationWindows(self, aim): #aim: 1 InfoRetrieveal, 2 WPS
        self.showStylingWindow(aim)
        self.windowClassExtent.hideWindow()
    
    #Styling Window
    def openStylingWindow(self):
        self.windowClassStyling = StylingWindow(self.folders.getLogfilesHome(), self)
    def on_mnu_styling_activate(self, widget, data=None):
        if self.windowClassStyling.getStatus() == True:
            self.windowClassStyling.showWindow()
        elif self.windowClassStyling.getStatus() == False:
            self.windowClassStyling.hideWindow() 
    #Function
    def showStylingWindow(self, aim): #aim: 1 InfoRetrieveal, 2 WPS
        if self.initializedMapfile == True:
            self.windowClassStyling.initializeStylingWindow(self.mapnik_map, self.windowClassTiles, self.windowClassInfo, self.windowClassWPS, aim)
            self.windowClassStyling.showWindow()
    
    #Extent Window
    def openExtentWindow(self):
        self.windowClassExtent = ExtentWindow(self.folders, self.folders.getPreviewImage(), self)
    def on_mnu_extent_activate(self, widget, data=None):
        if self.windowClassExtent.getStatus() == True:
            self.windowClassExtent.showWindow()
        elif self.windowClassExtent.getStatus() == False:
            self.windowClassExtent.hideWindow() 
     
    #Preview Window
    def openPreviewWindow(self):
        self.windowClassPreview = PreviewWindow(self.folders.getPreviewImage(), self)
    def on_mnu_preview_activate(self, widget, data=None):
        if self.windowClassPreview.getStatus() == True:
            self.windowClassPreview.showWindow()
        elif self.windowClassPreview.getStatus() == False:
            self.windowClassPreview.hideWindow()
    
    #Tiles Visualisation Window
    def openTileWindow(self):
        self.windowClassTiles = TilesWindow(self.folders.getLogfilesHome(), self)
    def on_mnu_tiles_activate(self, widget, data=None):
        if self.windowClassTiles.getStatus() == True:
            self.windowClassTiles.showWindow()
        elif self.windowClassTiles.getStatus() == False:
            self.windowClassTiles.hideWindow() 
     
    #Tools Window
    def openToolsWindow(self):
        self.windowClassTools = ToolsWindow(self.folders.getLogfilesHome(), self)
    def on_mnu_tools_activate(self, widget, data=None):
        if self.windowClassTools.getStatus() == True:
            self.windowClassTools.showWindow()
        elif self.windowClassTools.getStatus() == False:
            self.windowClassTools.hideWindow() 
        
    #Export the current mapfile
    def on_mnu_export_mapfile_activate(self, widget, data=None):
        name = 'GeneralCarto-last-mapfile.xml'
        wobj = open(self.folders.getLogfilesHome()+name, 'w')
        wobj.write(mapnik.save_map_to_string(self.mapnik_map))
        wobj.close
        self.ui.label_status.set_text("Mapfile '%s' was exported to: \n\t%s" %(name, self.folders.getLogfilesHome()))  
   
    #set the Button for showing the tiles in-/visible ... depends on selection of a proper bbox
    def tileButtonVisibility(self, visibility):
        self.ui.button_show_tiles.set_child_visible(visibility)
                
###Additional Functions
  
    #used to evaluate if style file should be opened in editor
    def on_checkbutton_open_toggled(self, widget, data=None):
        if self.checkbutton_open == True:
            self.checkbutton_open = False 
        elif self.checkbutton_open == False:
            self.checkbutton_open = True

    
       
    
###Test- & Old functions

    def on_button_window_clicked(self, widget, data=None):
        
   #     server = 'http://localhost:8080/wps-dev/wps'
        #server = 'http://kartographie.geo.tu-dresden.de/webgen_wps/wps'
    #    result = WPScom.doWPSProcess([(1369751.5468703583, 6457400.14953169, 1408887.3053523686, 6496535.908013698), u'/home/klammer/Software/Quickly/generalcarto/data/media/shapefiles/vgtl_polygons.shp', 'ch.unizh.geo.webgen.service.BuildingSimplification', server, 'WebGen_WPS_547_346_10.xml', '/home/klammer/GeneralCarto/xmlfiles/', "([building]='yes')", [('minlength', 'minimum length', '10.0')], [547, 346], '/home/klammer/GeneralCarto/log-files/'])
     #   print result[0]
        
        #postgreFunctions.makePostgresTable()
        
  #      results = [('', 0, ''), ('', 0, ''), ('', 0, ''), ('', 0, ''), ('/home/klammer/GeneralCarto/xmlfiles/result_273_172_9.gml', 985, 'LineString'), ('/home/klammer/GeneralCarto/xmlfiles/result_273_173_9.gml', 23, 'LineString'), ('', 0, ''), ('', 0, ''), ('', 0, '')]
   #     self.table_name = 'generalized_line_cache'
    #    WPSWindow(self.folders.getLogfilesHome(), self.folders.getXMLFilesHome(), self).writeResultToDB(results, self.table_name)


        TileCalcs = tiling.TileCalculations((11.8722539115, 50.1713213772, 12.584850326, 50.678205265399974),0,18)
        #TileCalcs.printTileRangeParameters(self.folders.getGeneralHome(), 'Extent-Tile-Params.txt')
        #print TileCalcs.getAllTilesOfOneZoomlevel(9)
        print TileCalcs.findStartZoomlevel(2,2)

    def on_button_styledit_clicked(self, widget, data=None):
        if self.folders.getMapfileHome() != '':
            styler = StyleditDialog(self.folders.getMapfileHome())
            result = styler.run() 
            #close the dialog, and check whether to proceed        
            styler.destroy()
            if result != Gtk.ResponseType.OK:
                return 
    
    def on_button_short_clicked(self, widget, data=None):
        sending = 'Tool for tile-based on-the-fly-generalisation   \n+(1324637.159999081, 1405011.9800014955, 6477402.360002069, 6546380.469994396):/home/klammer/Software/Quickly/generalcarto/data/media/XML-files/slippy_vogtland_with_shapes.xml:/home/klammer/GeneralCarto/tiles/:0:18:'+self.folders.getGeneralHome()+':'+self.folders.getLogfilesHome()
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
        
        
        
            
    
        

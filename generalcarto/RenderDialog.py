# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

from gi.repository import Gtk # pylint: disable=E0611

from generalcarto_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('generalcarto')

from generalcarto import gdal_functions as gdal
from generalcarto import rendering
from generalcarto.TilesDialog import TilesDialog
from generalcarto import functions as func

import mapnik2 as mapnik

from quickly import prompts
from quickly.widgets.dictionary_grid import DictionaryGrid
import glob
import os
    

class RenderDialog(Gtk.Dialog):
    __gtype_name__ = "RenderDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated RenderDialog object.
        """

        ####let the user choose a directory that contains one or more mapnik style files
        global path
        path = ''

        #let the user choose a path with the directory chooser
        response, path = prompts.choose_directory()

        #make certain the user said ok before working
        if response == Gtk.ResponseType.OK:
           
           #make a list of the supported xml files
           global dicts
           dicts = dict()
           counter = 0
           #iterate through root directory
           for files in glob.glob(path + "/*.xml"):
                    if files.endswith('.xml'):
                        #create a URI in a format gstreamer likes
                        file_uri = path
                        fileSplit = files.split(path + "/")                        
                        dicts[str(counter)] = fileSplit[1]    
                        counter = counter + 1   
           global keylist            
           keylist = dicts.keys()
           keylist.sort()   
        ####
        #initialize some global variables
        global image
        image = ''
        global checkbutton
        checkbutton = False
        global checkbutton_open
        checkbutton_open = False
        global shapefile
        shapefile = ''
        global new_stylesheet
        new_stylesheet = ''        
        global projection 
        projection = '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs'
        
        builder = get_builder('RenderDialog')
        new_object = builder.get_object('render_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a RenderDialog object with it in order to
        finish initializing the start of the new RenderDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)

        #fill the combotextbox with the xml-files of the initially user-chosen directory
        for key in keylist: 
	           #print key, value
               self.ui.comboboxtext1.append_text(dicts[key])
                
        #initialize the entries for the (simple) image size
        self.ui.entry_height.set_text('256')
        self.ui.entry_width.set_text('256')
        self.ui.image1.clear()

        #initialize the entry for the zoomlevels for the tile rendering
        self.ui.entry1.set_text('0')
        self.ui.entry2.set_text('18')

    #set style and shape when combobox has changed
    def on_comboboxtext1_changed(self, widget, data=None):
        #get the chosen stylefile
        global new_stylesheet
        new_stylesheet = self.ui.comboboxtext1.get_active_text() 
        user_xml = new_stylesheet
        #get all shapefiles of the chosen stylefile
        shape = func.getShapefile(path+'/'+new_stylesheet)
        self.ui.comboboxtext2.remove_all()
        dicts2 = dict()
        for i in xrange(len(shape)):
                        dicts2[i] = shape[i]
        keylist2 = dicts2.keys()
        keylist2.sort()   
        for key in keylist2: 
	           #print key, value
               self.ui.comboboxtext2.append_text(dicts2[key])

        #open style file if user wants to
	    if checkbutton_open == True:
            os.system('gedit --new-window ' + path+'/'+new_stylesheet)
        
        
    #lets user choose a shapefile, which will be taken to automatically get an extent of the data
    def on_comboboxtext2_changed(self, widget, data=None):
        global shapefile
        shapefile = self.ui.comboboxtext2.get_active_text() 
        
    #Display map tiles with a on-the fly rendering of the concrete 9 tiles that will be displayed
    def on_button_tiles_clicked(self, widget, data=None):
     if new_stylesheet != '':
      if shapefile != '':
        extent = []
        # Get the extent...
        if checkbutton == True:
            try:
                #... of a given shapefile
                extent = gdal.getExtentFromShape(shapefile)
                #fill the entries with the values of the found extent            
                self.ui.entry_lllo.set_text(str(extent[0]))
                self.ui.entry_urlo.set_text(str(extent[1]))
                self.ui.entry_llla.set_text(str(extent[2]))
                self.ui.entry_urla.set_text(str(extent[3])) 
            except:
               self.ui.label8.set_text('Unable to get extent of shapefile!')                       
        else:
            #...from the manual setted entries
            try:
                extent = (float(self.ui.entry_lllo.get_text()), float(self.ui.entry_urlo.get_text()), float(self.ui.entry_llla.get_text()), float(self.ui.entry_urla.get_text()))
            except:
                self.ui.label8.set_text('Emtpty entry or not as float!')
                self.ui.image1.clear()
        #Go on if extent was setted, respectively no error occured
        if extent != '':    
            try:  
#                print 'bbox:'+str(bbox)
                #initialize the information that will be send to the ui
                mapfile = path+'/'+new_stylesheet
                tile_dir = path+'/tiles/'     #'/home/ralf/Software/Quickly/testdaten/tiles/'
                maxZoom = self.ui.entry2.get_text()
                minZoom = self.ui.entry1.get_text()
                #collect all in one string, as this seems to be the only way
                sending = str(extent) + ':' + mapfile + ':' + tile_dir + ':' + minZoom + ':' + maxZoom 

                tiler =  TilesDialog(sending)
                result = tiler.run() 
                #close the dialog, and check whether to proceed        
                tiler.destroy()
                if result != Gtk.ResponseType.OK:
                    return                   
            except:
                self.ui.label8.set_text('Extent has only emtpty entries or is not given as float!')
                self.ui.image1.clear()
      else:
        self.ui.label8.set_text('Please choose a shape file!')
     else:
        self.ui.label8.set_text('Please choose a style file!')


    #Perform a simple rendering of a single *.png image file
    def on_button_render_clicked(self, widget, data=None):       
      if new_stylesheet != '':
        global image
        image = path+'/user_image.png'
        size = (int(self.ui.entry_height.get_text()),int(self.ui.entry_width.get_text()))        
        
        if checkbutton == True:
            extent = gdal.getExtentFromShape(shapefile)
            rendering.complexRun(image, path+'/'+new_stylesheet, extent, size)
            self.ui.image1.set_from_file(image)
            self.ui.entry_lllo.set_text(str(extent[0]))
            self.ui.entry_urlo.set_text(str(extent[1]))
            self.ui.entry_llla.set_text(str(extent[2]))
            self.ui.entry_urla.set_text(str(extent[3]))
            self.ui.label_result.set_text('Saved to: ' + image)
            
        else:
            
            try:
                extent = (float(self.ui.entry_lllo.get_text()), float(self.ui.entry_urlo.get_text()), float(self.ui.entry_llla.get_text()), float(self.ui.entry_urla.get_text()))
                rendering.complexRun(image, path+'/'+new_stylesheet, extent, size)
                self.ui.image1.set_from_file(image)  
                self.ui.label_result.set_text('Saved to: ' + image)              
            except:
                self.ui.label8.set_text('Emtpty entry or not as float!')
                self.ui.image1.clear()

      else:
        self.ui.label8.set_text('Please choose a style file!')


    def on_btn_ok_clicked(self, widget, data=None):
        """The user has elected to save the changes.

        Called before the dialog returns Gtk.ResponseType.OK from run().
        """

        pass

    def on_btn_cancel_clicked(self, widget, data=None):
        """The user has elected cancel changes.

        Called before the dialog returns Gtk.ResponseType.CANCEL for run()
        """
        pass

    def on_checkbutton1_toggled(self, widget, data=None):
        global checkbutton
        if checkbutton == True:
            checkbutton = False 
        elif checkbutton == False:
            checkbutton = True

    def on_checkbutton_open_toggled(self, widget, data=None):
        global checkbutton_open
        if checkbutton_open == True:
            checkbutton_open = False 
        elif checkbutton_open == False:
            checkbutton_open = True

    def getResult(self):
        if image != '':
            return image
        else:
            return 'None'


if __name__ == "__main__":
    dialog = RenderDialog()
    dialog.show()
    Gtk.main()

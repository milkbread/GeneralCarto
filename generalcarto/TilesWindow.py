from gi.repository import Gtk
import mapnik
import time
import os

from generalcarto import rendering
from generalcarto import functions

class TilesWindow(Gtk.Window):
    
    def __init__(self, logfiles, main_window, name = "TileWindow", file = "./data/ui/TileWindow.glade"):
        self.logfiles = logfiles
        self.main_window = main_window
                
        #basics for loading a *.glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(file)
        self.window = self.builder.get_object(name)
        
        self.initializeContents()
        
        #This is very necessary for an additional windwo...it handles the click on the close button of the window
        self.window.connect("delete-event", self.closedThisWindow)
        self.closed = True
        self.initialized = False
 
###Initializations 
    def initializeContents(self):
        self.image1 = self.builder.get_object('image1')
        self.image2 = self.builder.get_object('image2')
        self.image3 = self.builder.get_object('image3')
        self.image4 = self.builder.get_object('image4')
        self.image5 = self.builder.get_object('image5')
        self.image6 = self.builder.get_object('image6')
        self.image7 = self.builder.get_object('image7')
        self.image8 = self.builder.get_object('image8')
        self.image9 = self.builder.get_object('image9')
        self.label_scale = self.builder.get_object('label_scale')
        self.label_zoom = self.builder.get_object('label_zoom')
        
    def initializeParameters(self, extent, mapnik_map, tile_dir, minZoom, maxZoom, buffer_size, generalHome, log_files):
        self.logs = log_files
        self.tile_dir = tile_dir
        self.minZoom = minZoom
        self.maxZoom = maxZoom
        functions.writeToLog('TilesWindow was initialized', self.logs, True)
        
        #initialize the map
        self.mapnik_map = mapnik_map
        #get the projection of the mapfile
        prj = mapnik.Projection(self.mapnik_map.srs)
        #calculate the necessary tiles, depending on the given extent
        bbox = self.getGeoCodedBbox(extent, prj)
        self.all_tiles = rendering.calcNecTiles(bbox, tile_dir, minZoom, maxZoom)
        #save start zoom
        self.start_zoom = self.all_tiles[0][2]
        #find all x and y names of the necessary tiles and...               
        self.x, self.y = self.findNames()
        #get the central tile
        central_tile = functions.getZentralTile(self.x,self.y)
        self.central_tile_global = central_tile
        #render the the central and all 8 surrounding tiles
        first_zentral_uri = self.all_tiles[0][3]
        zoom = self.start_zoom        
        #initialize the zoomfactor, that is relative to the start zoom
        self.zoomFactor = 0  
        #render the first displayed tiles
        rendered_tiles = self.render_on_demand(first_zentral_uri, self.start_zoom, central_tile)
        #show the initially rendered tiles
        self.show_tiles(rendered_tiles)
        #show the initially zoomfactor
        self.label_zoom.set_text(str(self.start_zoom))
        
        if self.closed == True:
            self.showWindow()
            
        self.initialized = True
        
###Listeners
    def showWindow(self):
        self.main_window.ui.mnu_tiles.set_label(self.main_window.menuItemIndicator + self.main_window.ui.mnu_tiles.get_label())
        self.window.show_all()
        self.closed = False
        
    def hideWindow(self):
        self.main_window.ui.mnu_tiles.set_label(self.main_window.ui.mnu_tiles.get_label().split(self.main_window.menuItemIndicator)[1])
        self.window.hide()
        self.closed = True
        
    def getStatus(self):
        return self.closed
        
    def getInitializationStatus(self):
        return self.initialized
        
    def closedThisWindow(self, window, event):
        self.hideWindow()
        return True #this prevents the window from getting destroyed
        
###Window management
    #displays the rendered tiles
    def show_tiles(self, rendered_tiles):
         
        self.image1.set_from_file(rendered_tiles[0]) 
        self.image2.set_from_file(rendered_tiles[1]) 
        self.image3.set_from_file(rendered_tiles[2]) 
        self.image4.set_from_file(rendered_tiles[3]) 
        self.image5.set_from_file(rendered_tiles[4]) 
        self.image6.set_from_file(rendered_tiles[5]) 
        self.image7.set_from_file(rendered_tiles[6]) 
        self.image8.set_from_file(rendered_tiles[7]) 
        self.image9.set_from_file(rendered_tiles[8])
        
###Functions
    def getMapnikMap(self):
        return self.mapnik_map

    #that function is only a help to be able to switch between 'render_on_demand_as_loop' and 'render_on_demand_as_multiprocessing'
    def render_on_demand(self, tile_uri, zoom, central_tile):
        start_time = time.time()
        result, scale = self.render_on_demand_as_loop(tile_uri, zoom, central_tile)
        self.label_scale.set_text("1 : " + str(int(round(scale,0))))
        #set log-output
        functions.writeToLog('Render on demand was used - it took:'+str(round(time.time()-start_time, 3)) + ' seconds!',self.logs)
        functions.writeToLog('   --> zentral tile:%s & zoomfactor: %s' %(str(central_tile), str(zoom)),self.logs)
        return result
    
        
    def render_on_demand_as_loop(self, tile_uri, zoom, central_tile):
        rendered_tiles = []
        tileBunch = self.getTileBunch(central_tile)
        for tile in tileBunch:
            if not os.path.isdir(tile_uri + '/' + str(tile[0])):
                os.mkdir(tile_uri + '/' + str(tile[0]))
            uri = tile_uri + '/' + str(tile[0]) + '/' + str(tile[1]) + '.png'
            arg = (self.tile_dir, mapnik.save_map_to_string(self.mapnik_map), self.maxZoom, uri,tile[0], tile[1], zoom)
            scale = rendering.pure_tile_rendering(arg)
            rendered_tiles.append(uri)
        return rendered_tiles, scale
        
    def getTileBunch(self, central_tile):
        all_tiles = []
        for k in range(-1,2):
            for l in range(-1,2):
                one_tile = []
                one_tile.append(central_tile[0]+k)
                one_tile.append(central_tile[1]+l)
                all_tiles.append(one_tile)
        return all_tiles
        
    def findNames(self):
        x = []
        x.append(self.all_tiles[0][0])
        y = []
        y.append(self.all_tiles[0][1])
        for i in range(1, len(self.all_tiles)):
            if (self.all_tiles[i])[0] > (self.all_tiles[i-1])[0]:
                x.append(self.all_tiles[i][0])
        for j in range(1,len(x)):
            if (self.all_tiles[j])[1] > (self.all_tiles[j-1])[1]:
                y.append(self.all_tiles[j][1])
        return x, y
        
    def getGeoCodedBbox(self, extent, prj):
        c0 = prj.inverse(mapnik.Coord(float(extent[0]),float(extent[2])))
        c1 = prj.inverse(mapnik.Coord(float(extent[1]),float(extent[3])))
        return (c0.x, c0.y, c1.x, c1.y)
        
        #right
    def navigate(self, direction):
        start_time = time.time()        
        #zoom is relative to start and zoomfactor
        zoom = self.start_zoom + self.zoomFactor
        #change the x values for new tiles
        if direction == 'right':
            self.x.append(self.x[len(self.x)-1]+1)   
            self.x.pop(0)
        elif direction == 'left':
            self.x.insert(0, self.x[0]-1)
            self.x.pop(len(self.x)-1)
        elif direction == 'up':
            self.y.insert(0, self.y[0]-1)
            self.y.pop(len(self.y)-1)
        elif direction == 'down':
            self.y.append(self.y[len(self.y)-1]+1)   
            self.y.pop(0)
        #set new zentral tile
        self.central_tile_global = functions.getZentralTile(self.x,self.y)
        self.finalVisuals(zoom)
        
    def scaling(self, direction):
        start_time = time.time()        
        #zoom is relative to start and zoomfactor - so zoomfactor has to be...
        if direction == 'in':
        #...increased when zooming in
            self.zoomFactor = self.zoomFactor + 1
            if self.start_zoom + self.zoomFactor == int(self.maxZoom+1):
                self.zoomFactor = self.zoomFactor - 1
            self.central_tile_global = ((self.central_tile_global[0]*2)+1,(self.central_tile_global[1]*2)+1)
        elif direction == 'out':
        #...decreased when zooming out
            self.zoomFactor = self.zoomFactor - 1
            self.central_tile_global = ((self.central_tile_global[0]/2),(self.central_tile_global[1]/2))
        zoom = self.start_zoom + self.zoomFactor
        #clear all x
        for i in xrange(len(self.x)):
            self.x.pop()
        #clear all y
        for i in xrange(len(self.y)):
            self.y.pop()
        #fill x and y with new tiles
        for i in range(-1,2):
            self.x.append(self.central_tile_global[0]+i)
            self.y.append(self.central_tile_global[1]+i)
        #make dir if it doesn't exist
        if not os.path.isdir(self.tile_dir + str(zoom)):
            os.mkdir(self.tile_dir + str(zoom))
        self.finalVisuals(zoom)
            
    def finalVisuals(self, zoom):
        #set tile uri
        tile_uri = self.tile_dir + str(zoom)
        #render the new tiles
        rendered_tiles = self.render_on_demand(tile_uri, zoom, self.central_tile_global)
        #show the new tiles
        self.show_tiles(rendered_tiles)
        

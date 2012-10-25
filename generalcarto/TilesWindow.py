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
        
        #This is very necessary for an additional window...it handles the click on the close button of the window
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
        
    def initializeTilesWindow(self, styling_window, info_window):
        self.styling_window = styling_window
        self.info_window = info_window
        
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
        self.prj = prj
        #calculate the necessary tiles, depending on the given extent
        bbox = self.getGeoCodedBbox(extent, prj)
        all_tiles, first_zentral_uri, self.start_zoom= rendering.calcNecTiles(bbox, tile_dir, minZoom, maxZoom)
        #get all x and y names of the necessary tiles for the next step... 
        self.x, self.y = self.getNames(all_tiles)
        #...finding the central tile
        central_tile = functions.getZentralTile(self.x,self.y)
        self.central_tile_global = central_tile
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
        self.styling_window.showPreviewBox(True)
        
###Listeners
    def showWindow(self):
        self.main_window.ui.mnu_tiles.set_label(self.main_window.menuItemIndicator + self.main_window.ui.mnu_tiles.get_label())
        self.window.show_all()
        self.closed = False
        
    def hideWindow(self):
        self.main_window.ui.mnu_tiles.set_label(self.main_window.ui.mnu_tiles.get_label().split(self.main_window.menuItemIndicator)[1])
        self.window.hide()
        self.closed = True

    def destroyWindow(self):
        self.window.destroy()
        if self.closed == False:
            self.main_window.ui.mnu_tiles.set_label(self.main_window.ui.mnu_tiles.get_label().split(self.main_window.menuItemIndicator)[1])
        
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
        
        if self.styling_window.rule_chosen == True and self.info_window.getStatus() == False:
            self.info_window.initializeInfoWindow(self.mapnik_map, self, self.styling_window)
        
###Functions
    #Functions for InfoWindow
    def getParameterForGeneralisation(self):
        return self.getTileBunch(self.central_tile_global), self.maxZoom
        
    def getExtents(self, tile, tileproj):
            z = self.start_zoom + self.zoomFactor
           #print tile
            p0 = (tile[0] * 256, (tile[1] + 1) * 256)
            p1 = ((tile[0] + 1) * 256, tile[1] * 256)
            # Convert to LatLong (EPSG:4326)
            l0 = tileproj.fromPixelToLL(p0, z)
            l1 = tileproj.fromPixelToLL(p1, z)
            # Convert to map projection (e.g. mercator co-ords EPSG:900913)
            c0 = self.prj.forward(mapnik.Coord(l0[0],l0[1]))
            c1 = self.prj.forward(mapnik.Coord(l1[0],l1[1]))
        
            tile_extent = (c0.x,c0.y, c1.x,c1.y)
            return tile_extent, z
        
    #**********

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
        
    def getNames(self, all_tiles):
        x = []
        x.append(all_tiles[0][0])
        y = []
        y.append(all_tiles[0][1])
        for i in range(1, len(all_tiles)):
            if (all_tiles[i])[0] > (all_tiles[i-1])[0]:
                x.append(all_tiles[i][0])
        for j in range(1,len(x)):
            if (all_tiles[j])[1] > (all_tiles[j-1])[1]:
                y.append(all_tiles[j][1])
        return x, y
        
    def getGeoCodedBbox(self, extent, prj):
        c0 = prj.inverse(mapnik.Coord(float(extent[0]),float(extent[2])))
        c1 = prj.inverse(mapnik.Coord(float(extent[1]),float(extent[3])))
        return (c0.x, c0.y, c1.x, c1.y)
        
    def getGlobalCentralTile(self):
        return self.central_tile_global
        
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
        self.label_zoom.set_text(str(zoom))
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
        
    def addPreviewToMap(self, name, scaleDenoms, filter, symbol_type, datasource, layerSRS, prevColor):
        s = mapnik.Style()
        r = mapnik.Rule()
        if symbol_type == 'polygon':
            polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(prevColor))
            r.symbols.append(polygon_symbolizer)
        elif symbol_type == 'line':
            line_symbolizer = mapnik.LineSymbolizer(mapnik.Color(prevColor),3)
            r.symbols.append(line_symbolizer)
#        elif symbol_type == 'text':
 #           t = mapnik.TextSymbolizer('FIELD_NAME', 'DejaVu Sans Book', 10, Color('black'))
  #          t.halo_fill = Color('white')
   #         t.halo_radius = 1
    #        t.label_placement = label_placement.LINE_PLACEMENT
     #       r.symbols.append(line_symbolizer)
        else:
            print symbol_type, 'has to be implemented to preview!!!'
        if filter != None:
            #f = mapnik.Expression("[waterway] != ''") #'Expression' stands for 'Filter' as this will be replaced in Mapnik3
            r.filter = filter#f
            r.min_scale = scaleDenoms[0]
            r.max_scale = scaleDenoms[1]
        s.rules.append(r)
        
        proof = self.mapnik_map.append_style(name,s)
        layer = mapnik.Layer('world')
        layer.datasource = datasource[1]
        layer.srs = layerSRS
        layer.styles.append(name)
        self.mapnik_map.layers.append(layer)
        
    def addPreviewOfGeneralizedGeometriesToMap(self, table_name, symbol_type, layerSRS, name):
        genColor = 'rgb(0%,0%,100%)'
        s = mapnik.Style()
        r = mapnik.Rule()
        if symbol_type == 'polygon':
            polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color(genColor))
            r.symbols.append(polygon_symbolizer)
        elif symbol_type == 'line':
            line_symbolizer = mapnik.LineSymbolizer(mapnik.Color(genColor),2)
            r.symbols.append(line_symbolizer)
        else:
            print symbol_type, 'has to be implemented to preview!!!'
        s.rules.append(r)
        self.mapnik_map.append_style(name,s)
        
        lyr = mapnik.Layer('Generalized geometry from PostGIS')
        lyr.datasource = mapnik.PostGIS(host='localhost',user='gisadmin',password='tinitus',dbname='meingis',table='(select geom from '+ table_name +' ) as geometries')
        lyr.srs = layerSRS
        lyr.styles.append(name)
        self.mapnik_map.layers.append(lyr)
        
    def reloadMapView(self):
        
        zoom = self.start_zoom + self.zoomFactor
        self.finalVisuals(zoom)
        
        

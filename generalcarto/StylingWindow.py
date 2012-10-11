from gi.repository import Gtk
import mapnik
import time
import os
from generalcarto import xmlFunctions



class StylingWindow(Gtk.Window):
    
    def __init__(self, logfiles, main_window, name = "styling_window", file = "./data/ui/Toolbars.glade"):
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
 
###Initializations 
    def initializeContents(self):
        self.comboboxtext_layer = self.builder.get_object('comboboxtext_layer')
        self.comboboxtext_layer.connect("changed", self.on_comboboxtext_layer_changed)
        self.comboboxtext_style = self.builder.get_object('comboboxtext_style')
        self.comboboxtext_style.connect("changed", self.on_comboboxtext_style_changed)
        self.comboboxtext_rules = self.builder.get_object('comboboxtext_rules')
        self.comboboxtext_rules.connect("changed", self.on_comboboxtext_rules_changed)
        
        
    def initializeTilesWindow(self, mapnik_map, tiles_window):
        self.tiles_window = tiles_window
        self.mapnik_map = mapnik_map
        #initial information request of the used style-file to be able to choose a geometry for generalization
        #loop through all layers
        for layer in self.mapnik_map.layers.__iter__():
            self.comboboxtext_layer.append_text(layer.name) 
        
        
    def showWindow(self):
        if self.closed == True:
            self.main_window.ui.mnu_styling.set_label(self.main_window.menuItemIndicator + self.main_window.ui.mnu_styling.get_label())
            self.window.show_all()
            self.closed = False
            
    def hideWindow(self):
        if self.closed == False:
            self.main_window.ui.mnu_styling.set_label(self.main_window.ui.mnu_styling.get_label().split(self.main_window.menuItemIndicator)[1])
            self.window.hide()
            self.closed = True
            
###Listeners
    def closedThisWindow(self, window, event):
        self.hideWindow()
        return True #this prevents the window from getting destroyed
        
    def on_comboboxtext_layer_changed(self, widget, data=None):
        self.comboboxtext_style.remove_all()
        chosen_layer = self.comboboxtext_layer.get_active_text()  
        self.mapnik_styles = [] 
        #find the chosen layer
        for layer in self.mapnik_map.layers.__iter__():
           if chosen_layer == layer.name:
               source_params = xmlFunctions.getDatasourceFromString(mapnik.save_map_to_string(self.mapnik_map),chosen_layer)
               type = source_params['type']
               #print type
               if type == 'shape' or type == 'postgis':
                   self.datasource = (source_params['type'], layer.datasource, source_params)
                   self.layerSRS = layer.srs
                   for style in layer.styles:
                       self.mapnik_styles.append(style)
                       self.comboboxtext_style.append_text(style)
               else:
                    print 'Please implement the missing type: %s' %type
                    self.comboboxtext_style.append_text('Layer type: %s ... it is not implemented yet!' %type)
    
    def on_comboboxtext_rules_changed(self, widget, data=None):
        print ""
    
    
    def on_comboboxtext_style_changed(self, widget, data=None):
        self.comboboxtext_rules.remove_all()
#        self.textview_symbols.get_buffer().set_text('') 
        if self.comboboxtext_style.get_active() != -1 :
            if self.comboboxtext_style.get_active_text().find('self.comboboxtext_style.get_active()') == -1: #!????????????????????????????????????
                chosen_style_name = self.comboboxtext_style.get_active_text()
               #print chosen_style_name
                self.chosen_style = self.mapnik_map.find_style(chosen_style_name)
                self.mapnik_rules = []
                #loop through all rules of the chosen style
                if self.chosen_style.rules.__len__() == 0:
                    self.comboboxtext_rules.append_text('Style contains no rule!')
                else:  
                    for rule in self.chosen_style.rules.__iter__():
                        rule_content = str(rule.filter) +' '+ str(rule.min_scale) +' '+ str(rule.max_scale) 
                        mapnik_symbols = []
                        for symbol in rule.symbols.__iter__():
                            symbol_type = symbol.type()
                            sym_params = {}
                            #print dir(symbol)
                            if symbol_type == 'polygon':
                                polygon_symbolizer = symbol.polygon()
                                
                                sym_params['Fill'] = str(polygon_symbolizer.fill)
                                sym_params['Fill-opacity'] = str(polygon_symbolizer.fill_opacity)
                                sym_params['Gamma'] = str(polygon_symbolizer.gamma)
                                #print symbol.fill, symbol.fill_opacity, symbol.gamma
                                
                            elif symbol_type == 'line':
                                line_symbolizer = symbol.line()
                                stroke = line_symbolizer.stroke
                                sym_params['Color'] = str(stroke.color) 
                                sym_params['Dash-offset'] = str(stroke.dash_offset) 
                                sym_params['Gamma'] = str(stroke.gamma) 
                                sym_params['Line-cap'] = str(stroke.line_cap) 
                                sym_params['Line-join'] = str(stroke.line_join) 
                                sym_params['Opacity'] = str(stroke.opacity) 
                                sym_params['Width'] = str(stroke.width) 
                                
                                #for test in sym_params.keys():
                                   #print test, sym_params[test]
                                
                                #print stroke.color, stroke.dash_offset, stroke.gamma, stroke.line_cap, stroke.line_join, stroke.opacity, stroke.width
                            elif symbol_type == 'text':
                                text_symbolizer = symbol.text()
                                print dir(text_symbolizer)
                                sym_params['allow overlap'] = str(text_symbolizer.allow_overlap)
                                sym_params['avoid edges'] = str(text_symbolizer.avoid_edges)
                                sym_params['displacement'] = str(text_symbolizer.displacement)
                                sym_params['force_odd_labels'] = str(text_symbolizer.force_odd_labels)
                                sym_params['format'] = str(text_symbolizer.format)
                                sym_params['minimum_distance'] = str(text_symbolizer.minimum_distance)
                                sym_params['minimum_path_length'] = str(text_symbolizer.minimum_path_length)
                                sym_params['orientation'] = str(text_symbolizer.orientation)
                                print text_symbolizer.name
                                """
                                 	allow_overlap
                                    avoid_edges
                                    displacement
                                    force_odd_labels
                                    format
                                    format_treehas to be implemented to preview!!!
                                    horizontal_alignment
                                    justify_alignment
                                    label_placement
                                    label_position_tolerance
                                    label_spacing
                                    largest_bbox_only
                                    maximum_angle_char_delta
                                    minimum_distance
                                    minimum_padding
                                    minimum_path_length
                                    orientation
                                    text_ratio
                                    vertical_alignment
                                    wrap_width"""
                            else:
                                print 'Please implement the missing types!!!!!'
                                
                            
                            self.symbol_type = symbol_type  
                                
                                
                            mapnik_symbols.append((symbol, sym_params))
                           #print symbol
                        self.mapnik_rules.append((rule,rule_content,rule.filter, mapnik_symbols, (rule.min_scale, rule.max_scale)))
                        self.comboboxtext_rules.append_text(rule_content)
                        
                #print 'Number of rules: ', len(self.mapnik_rules)
                #print self.mapnik_rules[0]
                self.comboboxtext_rules.set_active(0)
    
    
###Functions

    def getStatus(self):
        return self.closed
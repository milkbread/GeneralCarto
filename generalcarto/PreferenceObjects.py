import os
import time

class FilesNLogs:
    global working_folder
    global log_files_folder_name
    global log_file_name
    global tiles_folder_name
    global image_name
    global xml_files_folder_name
    
    working_folder = '/GeneralCarto/'
    log_files_folder_name = 'log-files/'
    log_file_name = 'GeneralCarto-log.txt'
    tiles_folder_name = 'tiles/'
    image_name = "user_image.png"
    xml_files_folder_name = 'xmlfiles/'
    
    def __init__(self):
        self.home = os.getenv("HOME")
        self.generalHome = self.home + working_folder
        self.logs = self.generalHome + log_files_folder_name
        self.logfile_name = self.logs+log_file_name
        self.tile_dir = self.generalHome + tiles_folder_name 
        self.previewImage = self.generalHome + image_name
        self.xml_files_folder = self.generalHome + xml_files_folder_name
        
        self.checkFolderExistence(self.generalHome)
        self.checkFolderExistence(self.logs)
        self.checkFolderExistence(self.tile_dir)
        self.checkFolderExistence(self.xml_files_folder)
        
        self.user_path = ''
        self.chosen_mapfile_name = ''
        
        #initialize a logfile
        self.logfile = Logfile(self.logfile_name)
            
    def getHome(self):
        return self.home
    def getGeneralHome(self):
        return self.generalHome
    def getLogfilesHome(self):
        return self.logs
    def getTilesHome(self):
        return self.tile_dir
    def getPreviewImage(self):
        return self.previewImage
    def getXMLFilesHome(self):
        return self.xml_files_folder
        
    def checkFolderExistence(self, folder):
        if not os.path.isdir(folder):
            os.mkdir(folder)
    
    def writeToLog(self, content):
        self.logfile.writeToLog(content)
    
    #user defined inputs
    def setUserPath(self, path):
        self.user_path = path + '/'        
    def setMapfile(self, mapfile):
        self.chosen_mapfile_name = mapfile
        self.mapfileHome = self.user_path + mapfile
        
    #user input dependend outputs
    def getUserPath(self):
        return self.user_path
    def getMapfile(self):
        return self.chosen_mapfile_name
    def getMapfileHome(self):
        return self.mapfileHome
        
class Definitions:
    def __init__(self):
        self.menuItemIndicator = "<  "
        self.textEditor = 'gedit'      
        self.minimal_mapnik_version = 200100
        self.mapnik_version_warning = "You're having a too old version of mapnik...install minimum version 2.1.0!!!"
        self.minZoom = '0'
        self.maxZoom = '18'
        
    def getIndicator(self):
        return self.menuItemIndicator
    def getEditor(self):
        return self.textEditor
    def getMinMapnikVersion(self):
        return self.minimal_mapnik_version, self.mapnik_version_warning
    def getZoomRange(self):
        return self.minZoom, self.maxZoom
        
class Logfile:
    def __init__(self, logs):
        self.logs = logs
        self.file = open(logs,"a")
        self.file.write('\n***********************************************************')
        self.file.write('\n'+str(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())))
        self.file.close()
    def writeToLog(self, content):
        self.file = open(self.logs,"a")
        self.file.write("\n"+content)
        self.file.close()
    def closeLogfile(self):
        self.file.close()
        
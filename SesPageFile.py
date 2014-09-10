from SesPage import SesPage

import os

class SesPageFile(SesPage):
    """
    Read pre-recorded SES data from a file.
    Write is not supported.
    """
    
    """What directory to find the SES page data."""
    default_directory = "pages"
    
    def __init__(self, directory=default_directory):
        super(SesPageFile,self).__init__()
        self.directory = directory
    
    def close(self):
        pass
        
    def readpage(self, pagenum):
        f = open(os.path.join(self.directory, "%.2x"%pagenum), "rb")
        return f.read()
    
    def writepage(self, pagenum, data):
        pass
    
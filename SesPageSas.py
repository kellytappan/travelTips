
from SesPage import SesPage
from ScsiPT  import ScsiPT
from Cmd     import Cmd
from CDB     import CDB

class SesPageSas(SesPage):
    """
    Read and write SES pages through SAS.
    """
    
    def __init__(self, ptdev):
        """
        pt is a SCSI passthrough device file name
        """
        self.pt = ScsiPT(ptdev)
        
    def readpage(self, pagenum):
        """
        Read the SES page specified by integer pagenum, returning a string.
        """
        data = self._getsespage(pagenum, 4)
        if pagenum == 0x80:
            data = self._getsespage(pagenum, 5)
        length = 4 + \
            (ord(data[2]) << 8) + \
            (ord(data[3]) << 0)
        return self._getsespage(pagenum, length)
    
    def writepage(self, pagenum, data):
        """
        Write the SES page specified by integer pagenum with string, data.
        """
        pass
    
    def _getsespage(self, page, length):
        # uses pt
        cmd = Cmd("rdr", {"pcv":1, "page_code":page, "alloc":length})
        #for q in cmd.cdb: print "%.2x" % q,
        #print
        cdb = CDB(cmd.cdb)
        cdb.set_data_in(length)
        self.pt.sendcdb(cdb)
        return cdb.buf


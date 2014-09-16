
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
        super(SesPageSas, self).__init__()
        self.pt = ScsiPT(ptdev)
        #print "__init__: self.pt =", self.pt  # DEBUG

    def close(self):
        del self.pt
        self.pt = None
        #print "close: self.pt =", self.pt  # DEBUG

    def __del__(self):
        self.close()

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

    def writepage(self, expanderid, data):
        """
        Write the SES page specified by integer pagenum with string, data.
        """
        #page = Cmd.clicommandout(Cls, expanderid, command)
        #cmd = Cmd("sd", {"self-test_code":0, "pf":1, "parameter_list_length":len(page)})
        pass

    def _getsespage(self, page, length):
        # uses pt
        cmd = Cmd("rdr", {"pcv":1, "page_code":page, "alloc":length})
        #for q in cmd.cdb: print "%.2x" % q,
        #print
        cdb = CDB(cmd.cdb)
        cdb.set_data_in(length)
        #print "_getsespage: self.pt =", self.pt  # DEBUG
        self.pt.sendcdb(cdb)
        return cdb.buf


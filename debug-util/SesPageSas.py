
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

    def close(self):
        del self.pt
        self.pt = None

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

    def writepage(self, data):
        """
        Write the SES page specified by integer pagenum with string, data.
        """
        cmd = Cmd("sd", {"self-test_code":0, "pf":1, "parameter_list_length":len(data)})
        cdb = CDB(cmd.cdb)
        cdb.set_data_out(data)
        result = self.pt.sendcdb(cdb)
        return result

    def _getsespage(self, page, length):
        # uses pt
        cmd = Cmd("rdr", {"pcv":1, "page_code":page, "alloc":length})
        #for q in cmd.cdb: print "%.2x" % q,
        #print
        cdb = CDB(cmd.cdb)
        cdb.set_data_in(length)
        self.pt.sendcdb(cdb)
        return cdb.buf

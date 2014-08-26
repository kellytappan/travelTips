from CliCmd  import CliCmd
from SesPageSas import SesPageSas
from ScsiPT  import ScsiPT
from Cmd     import Cmd
from CDB     import CDB

class CliCmdSas(CliCmd):
    
    def __init__(self, ptdev):
        """
        pt is a SCSI passthrough device file name
        """
        super(CliCmdSas, self).__init__()
        self.ses = SesPageSas(ptdev)
        self.pt = ScsiPT(ptdev)
    
    def __del__(self):
        #del self.ses
        pass
    
    def execute(self, command):
        """
        Send a CLI command through SES page 0xe8.
        """
        cmd = Cmd.clicommandout(1, command)
        cdb = CDB(cmd.cdb)
        self.pt.sendcdb(cdb)
        
        page = self.ses.readpage(0xe8)
        return page["data"].response.val

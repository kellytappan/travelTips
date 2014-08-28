from CliCmd  import CliCmd
from SesPageSas import SesPageSas
from ScsiPT  import ScsiPT
from Cmd     import Cmd
from CDB     import CDB

class CliCmdSas(CliCmd):
    
    def __init__(self, ptdev, expanderid):
        """
        pt is a SCSI passthrough device file name
        expanderid can have one of the values
          0x01: SBB Canister A
          0x02: SBB Canister B
          0x03: FEM Canister A SAS Expander 1
          0x04: FEM Canister A SAS Expander 2
          0x05: FEM Canister B SAS Expander 1
          0x06: FEM Canister B SAS Expander 2
        """
        super(CliCmdSas, self).__init__()
        self.ses = SesPageSas(ptdev)
        self.pt = ScsiPT(ptdev)
        self.expanderid = expanderid
    
    def __del__(self):
        #del self.ses
        pass
    
    def execute(self, command):
        """
        Send a CLI command through SES page 0xe8.
        """
        cmd = Cmd.clicommandout(self.expanderid, command)
        cdb = CDB(cmd.cdb)
        cdb.set_data_out(cmd.dat)
        self.pt.sendcdb(cdb)
        
        page = self.ses.parse(self.ses.readpage(0xe8))
        return page["data"].response.val

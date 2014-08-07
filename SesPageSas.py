from SesPage import SesPage
from ScsiPT import ScsiPT
from Cmd import Cmd
from CDB import CDB

class SesPageSas(SesPage):
    """
    Read and write SES pages through SAS.
    """
    
    def __init__(self, pt):
        """
        pt is a SCSI passthrough device
        """
        self.pt = pt
        
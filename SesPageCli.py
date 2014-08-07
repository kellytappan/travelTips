from SesPage import SesPage

class SesPageFile(SesPage):
    """
    Read and write SES pages through a CLI.
    """
    
    def __init__(self, cli_interface):
        self.cli_interface= cli_interface
        
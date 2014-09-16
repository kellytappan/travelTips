class Configuration:
    """
    Hold various configuration variables to be accessible to everyone.
    """

    # Are we menu-driven (interactive) or command-line driven (not interactive)?
    interactive = True
    @staticmethod
    def setInteractive(v):        Configuration.interactive = not not v
    @staticmethod
    def getInteractive( ): return Configuration.interactive

    # Should we clear the screen before each menu and data?
    clear = True
    clearcode = "\033[H\033[J"
    @staticmethod
    def setClear(v):        Configuration.clear = not not v
    @staticmethod
    def getClear( ): return Configuration.clear

    # Should we display byte offsets?
    byteoffsets = False
    @staticmethod
    def setByteoffsets(v):        Configuration.byteoffsets = not not v
    @staticmethod
    def getByteoffsets( ): return Configuration.byteoffsets

    # Should the menus display command-line shortcuts?
    shortcuts = False
    @staticmethod
    def setShortcuts(v):        Configuration.shortcuts = not not v
    @staticmethod
    def getShortcuts( ): return Configuration.shortcuts

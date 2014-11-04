from SesPage import SesPage

class SesPageCli(SesPage):
    """
    Read and write SES pages through a CLI.
    """

    def __init__(self, cli_interface):
        super(SesPageCli, self).__init__()
        self.cli_interface = cli_interface

    def close(self):
        if self.cli_interface:
            self.cli_interface.close()
            self.cli_interface = None

    def readpage(self, pagenum):
        """
        Read the SES page specified by integer pagenum, returning a string.
        """
        data = self._getsespage(pagenum, 4)
        if pagenum == 0x80:
            data = self._getsespage(pagenum, 5)
        if len(data) < 4:
            return self._getsespage(pagenum)
        length = 4 + \
            (ord(data[2]) << 8) + \
            (ord(data[3]) << 0)
        return self._getsespage(pagenum, length)

    def _getsespage(self, pagenum, length=None):
        cmd = "ses rcv " + str(pagenum)
        if length:
            cmd += " " + str(length)
        raw = self.cli_interface.execute(cmd)
        expected_index = 0  # The first line of data starts with "0000".
        page = ""  # No data yet.
        state = "before"  # We're not yet looking at a line with data.
        #print "raw = "
        #print raw
        for line in raw.split("\n"):
            # Skip everything before the starting "0000".
            if state == "before":
                words = line.split()
                if len(words) >= 1 and words[0] == "%.4x" % expected_index:
                    state = "in"
                    # Drop through.
            # We're past the header. Grab all the data values.
            if state == "in":
                words = line.split()
                if len(words) == 0:
                    # Blank line; all done with data.
                    state = "after"
                else:
                    if words[0] == "%.4x" % expected_index:
                        # Each word is the ASCII representation of one byte.
                        for word in words[1:]:
                            page += chr(int(word,16))
                            expected_index += 1
                    else:
                        if length and len(page) == length:
                            return page
                        if "@" not in words[0]:
                            return None
        return page

    def writepage(self, data):
        # Not yet implemented.
        pass



import os.path
import subprocess
import tempfile
import shutil

class FirmwareTypes:
    APP     = "app"
    BOOT    = "boot"
    SBBMI   = "cpld sbbmi"
    SASCONN = "cpld sasconn"
    BB      = "cpld baseboard"
    DAP     = "cpld dap"
    cpld_set = set((SBBMI, SASCONN, BB, DAP))
    specials = set((BB, DAP))  # programming requires FEM-B to be down
    affect   = \
    {
     APP    : set(("A","B","A0","A1","B0","B1")),
     BOOT   : set(("A","B","A0","A1","B0","B1")),
     SBBMI  : set(("A","B")),
     SASCONN: set(("A","B")),
     BB     : set(("A0")),
     DAP    : set(("A0")),

     "A" : set((APP,BOOT,SBBMI,SASCONN)),
     "B" : set((APP,BOOT,SBBMI,SASCONN)),
     "A0": set((APP,BOOT,BB,DAP)),
     "A1": set((APP,BOOT)),
     "B0": set((APP,BOOT)),
     "B1": set((APP,BOOT)),
     }
    iom_set = set(("A","B"))
    fem_set = set(("A0","A1","B0","B1"))
    all_set = iom_set | fem_set

class FirmwareFile():
    """
    operations pertaining to firmware files
    """
    
    def __init__(self, name):
        """
        "name" can be either
          a single firmware file,
          a 7z archive of firmware files,
          or a directory of firmware files.
        """
        self.name = name

        self.tmpdir = None
        # fwdict is
        #   dictionary indexed by expander type ("A", "A0", etc.) of
        #     dictionary indexed by firmware type of
        #       dictionary indexed by version string of
        #         file name string
        self.fwdict = {}
#         self.fwlist = []
        
        if os.path.isfile(name):
            self.tmpdir = tempfile.mkdtemp("", "fw-")
            result = subprocess.call(['7za','x','-o'+self.tmpdir,self.name], stdout=open("/dev/null","w"))
            #print "result =", result
            if   result is 0:
                self._populate_from_dir(self.tmpdir)
            elif result is 2:
                self._populate_from_file(self.name)
            else:
                print "7z error", result
        elif os.path.isdir(name):
            self._populate_from_dir(self.name)
        elif name == "":
            pass
        else:
            print "path not found:", self.name
            
    def __del__(self):
        if self.tmpdir:
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _log(self, level, message):
        pass

    def identifyfile(self, filename):
        """ Attempt to determine version and productid of a firmware file. """
        """
        Return a tuple with
          the version string,
          the keymap entry, or None
        """
        
        # key is bytes 8, 9, 10 of file, i.e. product id, hardware rev, destination partition
        # value is tuple of expanders, firmware image id, firmware type
        keymap = {
            "\x02\xa0\x02": (("A" ,     "B"      ), 1, FirmwareTypes.APP    ),
            "\x02\x0b\xff": (("A" ,     "B"      ), 1, FirmwareTypes.BOOT   ),
            "\x02\xa0\x08": (("A" ,     "B"      ), 2, FirmwareTypes.SBBMI  ),
            "\x02\x0b\x09": (("A" ,     "B"      ), 3, FirmwareTypes.SASCONN),
            "\x03\xa0\x02": (("A0","A1","B0","B1"), 1, FirmwareTypes.APP    ),
            "\x03\x0b\xff": (("A0","A1","B0","B1"), 1, FirmwareTypes.BOOT   ),
            "\x03\x0b\x08": (("A0",              ), 2, FirmwareTypes.BB     ),
            "\x03\x0b\x09": (("A0",              ), 3, FirmwareTypes.DAP    ),
            }

        f = open(filename, 'rb')

        f.seek(0x00)
        magic = f.read(8)
        if "JBL" not in magic:
            self._log(2, "file has bad magic number")
            return None
        
        f.seek(0x08)
        key = f.read(3)  # product id, hardware rev, destination partition
        mapped = keymap[key] if key in keymap else None

        f.seek(0x0c)
        version = f.read(2)
        version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
        version = "%04X" % version
        self._log(2, "file version   = "+version)
        if version == "0000":
            f.seek(0x0e)
            version = f.read(2)
            version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
            version = "0x%02x" % version
            self._log(2, "file version   = "+version)

#         f.seek(0x2b)
#         productid = f.read(16)
#         productid = mapped[4] if mapped else None
#         self._log(2, "file productid = "+productid)

        return (version, mapped)
    
    def _populate_from_file(self, filename):
        identity = self.identifyfile(filename)
        if identity:
            version, mapped = identity
            expanders, image, typ = mapped  # @UnusedVariable
            for expander in expanders:
                if expander not in self.fwdict:
                    self.fwdict[expander] = {}
                if typ not in self.fwdict[expander]:
                    self.fwdict[expander][typ] = {}
                self.fwdict[expander][typ][version] = filename
#
#             version, more = identity  # @UnusedVariable
#             if version not in self.fwdict:
#                 self.fwdict[version] = {}
#             self.fwdict[version][productid] = filename
#             self.fwlist.append((filename, version, more))
    
    def _populate_from_dir(self, dirname):
        for basename in os.listdir(dirname):
            fullname = os.path.join(dirname, basename)
            if   os.path.isfile(fullname): self._populate_from_file(fullname)
            elif os.path.isdir (fullname): self._populate_from_dir (fullname)
            else:
                pass  # Ignore non-file, non-directory paths.

#     def get_versions(self):
#         return self.fwdict.keys()
    
    def get_filename(self, prompt=None, typ=None, version=None):
        retval = self.fwdict
        if prompt:
            retval = retval[prompt] if prompt in retval else None
            if typ:
                retval = retval[typ] if typ in retval else None
                if version:
                    retval = retval[version] if version in retval else None
        return retval

#     def get_filename(self, productid, version=None):
#         if   len(self.fwdict) is 0:
#             # We didn't find any firmware files.
#             return None
#         elif len(self.fwdict) is 1:
#             if version and self.fwdict.keys()[0] != version:
#                 # The requested version didn't match the version we found.
#                 return None
#             if not version:
#                 # No specific version requested; use the one we found.
#                 version = self.fwdict.keys()[0]
#         else:
#             # We found more than one version.
#             if not version:
#                 # Version not specified. Still OK if we have exactly one matching productid.
#                 for v in self.fwdict:
#                     if productid in self.fwdict[v]:
#                         if version:
#                             # Found more than one candidate version.
#                             return None
#                         else:
#                             version = v
#         if version not in self.fwdict:
#             # We didn't find any files with that version.
#             return None
#         if productid not in self.fwdict[version]:
#             # We found that version, but not that productid.
#             return None
#         # We have well-enough-specified version and productid, and a matching file exists.
#         return self.fwdict[version][productid]

#     def get_all(self):
#         return self.fwdict
    
#     def get_list(self):
#         return self.fwlist


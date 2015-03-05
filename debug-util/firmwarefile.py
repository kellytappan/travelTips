
import os.path
import subprocess
import tempfile
import shutil
import re
import struct

class FirmwareTypes:
    APP     = "app"
    BOOT    = "boot"
    SBBMI   = "cpld sbbmi"
    SASCONN = "cpld sasconn"
    BB      = "cpld baseboard"
    DAP     = "cpld dap"
    MI      = "cpld mi"   # midplane
    SSM     = "cpld ssm"  # status
    BIOS    = "bios"
    U112    = "U112"  # PLX EEPROM 87xx
    U187    = "U187"  # PLX EEPROM 87xx
    U199    = "U199"  # PLX EEPROM 87xx
    BMC     = "bmc"
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
     MI     : set(("A","B")),
     SSM    : set(("A")),
     BIOS   : set(("A","B")),
     U112   : set(("A","B")),
     U187   : set(("A","B")),
     U199   : set(("A","B")),
     BMC    : set(("A","B")),

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
    
    # key is bytes 8, 9, 10 of file, i.e. product id, hardware rev, destination partition
    # value is tuple of expanders, firmware image id, firmware type
    keymap = {
        "\x02\xa0\x02"    : (("A" ,     "B"      ), 1, FirmwareTypes.APP    ),
        "\x02\x0b\xff"    : (("A" ,     "B"      ), 1, FirmwareTypes.BOOT   ),
        "\x02\xa0\x08"    : (("A" ,     "B"      ), 2, FirmwareTypes.SBBMI  ),
        "\x02\x0b\x09"    : (("A" ,     "B"      ), 3, FirmwareTypes.SASCONN),
        "\x03\xa0\x02"    : (("A0","A1","B0","B1"), 1, FirmwareTypes.APP    ),
        "\x03\x0b\xff"    : (("A0","A1","B0","B1"), 1, FirmwareTypes.BOOT   ),
        "\x03\x0b\x08"    : (("A0",              ), 2, FirmwareTypes.BB     ),
        "\x03\x0b\x09"    : (("A0",              ), 3, FirmwareTypes.DAP    ),
        
        "\x05\x0b\x08"    : (("A0",              ), 0, FirmwareTypes.BB     ),  # wc_baseboard
        "\x05\x0b\x09"    : (("A0",     "B0"     ), 0, FirmwareTypes.MI     ),  # wc_midplane
        "\x05\x0b\x0a"    : (("A0",              ), 0, FirmwareTypes.SSM    ),  # wc_status
        "\x05\xa0\x02"    : (("A0","A1","B0","B1"), 0, FirmwareTypes.APP    ),  # wolfcreek_fem_sas_update
        
        FirmwareTypes.BIOS: (("A" ,     "B"      ), 0, FirmwareTypes.BIOS   ),
        FirmwareTypes.U112: (("A" ,     "B"      ), 0, FirmwareTypes.U112   ),
        FirmwareTypes.U187: (("A" ,     "B"      ), 0, FirmwareTypes.U187   ),
        FirmwareTypes.U199: (("A" ,     "B"      ), 0, FirmwareTypes.U199   ),
        FirmwareTypes.BMC : (("A" ,     "B"      ), 0, FirmwareTypes.BMC    ),
        }

    def __init__(self, name, verbosity=0):
        """
        "name" can be either
          a single firmware file,
          a 7z archive of firmware files,
          or a directory of firmware files.
        """
        self.name = name
        self.verbosity = verbosity

        self.tmpdirs = []
        # fwdict is
        #   dictionary indexed by expander type ("A", "A0", etc.) of
        #     dictionary indexed by firmware type of
        #       dictionary indexed by version string of
        #         file name string
        self.fwdict = {}
#         self.fwlist = []
        
        if os.path.isfile(name):
#             tmpdir = tempfile.mkdtemp("", "fw-")
#             self.tmpdirs.append(tmpdir)
#             result = subprocess.call(['7za','x','-o'+tmpdir,self.name], stdout=open("/dev/null","w"))
#             #print "result =", result
#             if   result is 0:
#                 self._populate_from_dir(tmpdir)
#             elif result is 2:
#                 self._populate_from_file(self.name)
#             else:
#                 print "7z error", result
            self._populate_from_file(self.name)
        elif os.path.isdir(name):
            self._populate_from_dir(self.name)
        elif name == "":
            pass
        else:
            print "path not found:", self.name
            
    def __del__(self):
        for tmpdir in self.tmpdirs:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _log(self, level, message):
        if self.verbosity >= level:
            print message
        pass

    def identifyfile(self, filename):
        """ Attempt to determine version and productid of a firmware file. """
        """
        Return a tuple with
          the version string,
          the keymap entry, or None
        """
        
        with open(filename, 'rb') as f:
    
            f.seek(0x00)
            magic = f.read(8)
            if "JBL" not in magic:
                # Try some other types.
                # Try BIOS: strings has '$BVDT' followed by version number.
                p = subprocess.Popen(["strings", "--all", filename], stdout=subprocess.PIPE)
                state = "looking"
                for line in p.stdout:
                    if state == "looking":
                        if "$BVDT$" in line:
                            state = "grabrev"
                            continue
                    if state == "grabrev":
                        version = line[1:5]
                        p.terminate()
                        return (version, self.keymap[FirmwareTypes.BIOS])
                # Try PLX EEPROMs.
                retval = self.identifyfile_plx(filename)
                if retval:
                    return retval
                # Try BMC.
                m = re.search("JBL_WC_BMC_([0-9a-fA-F]*)\.bin", filename)
                if m:
                    version = m.group(1)
                    return (version, self.keymap[FirmwareTypes.BMC])
    #                 p = subprocess.call(["grep", "-q", "ifconfig", filename])
    #                 if p is 0:
    #                     return ("-", self.keymap[FirmwareTypes.BMC])
                # unknown
                self._log(2, "file is not recognizable firmware: "+filename)
                return None
            
            f.seek(0x08)
            key = f.read(3)  # product id, hardware rev, destination partition
            self._log(3, "key = %.2x,%.2x,%.2x %s" % (ord(key[0]), ord(key[1]), ord(key[2]), filename))
            mapped = self.keymap[key] if key in self.keymap else None
    
            f.seek(0x0c)
            version = f.read(2)
            version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
            version = "%04X" % version
            self._log(2, "file version   = "+version)
            if version == "0000":
                f.seek(0x0e)
                version = f.read(2)
                version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
                version = "0x%04x" % version
                self._log(2, "file version   = "+version)
    
    #         f.seek(0x2b)
    #         productid = f.read(16)
    #         productid = mapped[4] if mapped else None
    #         self._log(2, "file productid = "+productid)

        return (version, mapped)
    
    def identifyfile_plx(self, filename):
        prog = self.parse_plx(filename)
        if prog:
            for entry in prog:
                if entry[0] is 0x29c:
                    return entry[2]  #TODO: data needs to be parsed into version and type
            # It doesn't have the 0x29c register with version and type,
            # so guess type based on filename.  Version is hopeless.
            if "U112" in filename: return ("", self.keymap[FirmwareTypes.U112])
            if "U187" in filename: return ("", self.keymap[FirmwareTypes.U187])
            if "U199" in filename: return ("", self.keymap[FirmwareTypes.U199])
        else:
            return None  # If parse_plx fails, it's not a PLX EEPROM file.

    def _populate_from_file(self, filename):
        if filename.split('.')[-1] in ("xlsx","docx"):
            # Some Microsoft Office files can be unpacked with 7za, but we don't bother.
            self._populate_from_single_file(filename)
        else:
            tmpdir = tempfile.mkdtemp("", "fw-")
            self.tmpdirs.append(tmpdir)
            #TODO errorcheck
            result = subprocess.call(['7za','x','-o'+tmpdir,filename], stdout=open("/dev/null","w"))
            #print "result =", result
            if   result is 0:
                self._populate_from_dir(tmpdir)
            elif result is 2:
                self._populate_from_single_file(filename)
            else:
                print "7z error", result

    def _populate_from_single_file(self, filename):
        identity = self.identifyfile(filename)
        if identity:
            version, mapped = identity
            if not mapped:
                return
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

    def parse_plx(self, filename):
        with open(filename, 'rb') as f:

            # Check magic number.
            magic = f.read(1)
            if magic != "\x5a":
                #print "bad magic"
                return None
            flags = f.read(1)  # @UnusedVariable

            # Retrieve and check data size.            
            filesize = os.fstat(f.fileno()).st_size
            datasize = struct.unpack("<H", f.read(2))[0]
            if filesize != 4+datasize+4:
                #print "bad size:", filesize, datasize
                return None
            
            # Read the entries.
            program = []
            while datasize:
                addr, data = struct.unpack("<HI", f.read(6))
                port = addr >> 10
                regn = (addr << 2) & 0xfff
                program.append((regn, port, data))
                datasize -= 6
            
            # Read checksum.  We don't check it yet.
            chk = struct.unpack("<I", f.read(4))[0]  # @UnusedVariable
            
            return program


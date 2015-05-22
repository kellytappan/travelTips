
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
    WCISTR  = "WC istr"
    WCAPP   = "WC app"
    WCBOOT  = "WC boot"
    WCBB    = "WC cpld baseboard"
    WCMI    = "WC cpld mi"   # midplane
    WCSSM   = "WC cpld ssm"  # status
    WCALL   = "WC all-in-one"  # WC app, bb, mi, ssm
    WCBIOS  = "WC bios"
    U112    = "U112"  # PLX EEPROM 87xx
    U187    = "U187"  # PLX EEPROM 87xx
    U199    = "U199"  # PLX EEPROM 87xx
    U1000   = "U1000" # PLX EEPROM 97xx
    U1001   = "U1001" # PLX EEPROM 97xx
    U1002   = "U1002" # PLX EEPROM 97xx
    U1003   = "U1003" # PLX EEPROM 97xx
    U1004   = "U1004" # PLX EEPROM 97xx
    U1005   = "U1005" # PLX EEPROM 97xx
    U1006   = "U1006" # PLX EEPROM 97xx
    WCBMC   = "WC bmc"
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
     WCISTR : set(("A0","A1","B0","B1")),
     WCAPP  : set(("A0","A1","B0","B1")),
     WCBOOT : set(("A0","A1","B0","B1")),
     WCBB   : set(("A0")),
     WCMI   : set(("A","B")),
     WCSSM  : set(("A")),
     WCALL  : set(("A0","A1","B0","B1")),
     WCBIOS : set(("A","B")),
     U112   : set(("A","B")),
     U187   : set(("A","B")),
     U199   : set(("A","B")),
     U1000  : set(("A","B")),
     U1001  : set(("A","B")),
     U1002  : set(("A","B")),
     U1003  : set(("A","B")),
     U1004  : set(("A","B")),
     U1005  : set(("A","B")),
     U1006  : set(("A","B")),
     WCBMC  : set(("A","B")),

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


class FirmwareUtils:
    @staticmethod
    def normalize_version(version):
        """
        Regularize version string.
        """
        method = 1

        if not version:
            return version

        if method is 1:
            # 4 characters, no dot
            majmin = version.split('.')
            if len(majmin) is 2:
                while len(majmin[1]) < 2:
                    majmin[1] = "0" + majmin[1]
                version = majmin[0] + majmin[1]
            while len(version) < 4:
                version = "0" + version

        if method is 2:
            # 5 characters, space-filled major, dot, 0-filled minor
            majmin = version.split('.')
            if len(majmin) < 2:
                if len(version) is not 4:
                    # Don't know what this is.
                    return 'xx.xx'
                majmin[0] =   version[0:2]
                majmin.append(version[2:4])
            while len(majmin[1]) < 2:
                majmin[1] = "0" + majmin[1]
            while len(majmin[0]) < 2:
                majmin[0] = " " + majmin[0]
            if majmin[0][0] == "0":
                majmin[0] = " "+majmin[0][1:]
            version = majmin[0] + '.' + majmin[1]

        return version


class FirmwareFile():
    """
    operations pertaining to firmware files
    """
    
    # key is bytes 8, 9, 10 of file, i.e. product id, hardware rev, destination partition
    # value is tuple of expanders, firmware image id, firmware type
    keymap = {
        "\x02\xa0\x02"      : (("A" ,     "B"      ), 1, FirmwareTypes.APP    ),
        "\x02\x0b\xff"      : (("A" ,     "B"      ), 1, FirmwareTypes.BOOT   ),
        "\x02\xa0\x08"      : (("A" ,     "B"      ), 2, FirmwareTypes.SBBMI  ),
        "\x02\x0b\x09"      : (("A" ,     "B"      ), 3, FirmwareTypes.SASCONN),
        "\x03\xa0\x02"      : (("A0","A1","B0","B1"), 1, FirmwareTypes.APP    ),
        "\x03\x0b\xff"      : (("A0","A1","B0","B1"), 1, FirmwareTypes.BOOT   ),
        "\x03\x0b\x08"      : (("A0",              ), 2, FirmwareTypes.BB     ),
        "\x03\x0b\x09"      : (("A0",              ), 3, FirmwareTypes.DAP    ),
        
        "\x05\xa0\x02"      : (("A0","A1","B0","B1"), 0, FirmwareTypes.WCISTR ),  # wolfcreek_fem_sas_update istr
        "\x05\xa0\x05"      : (("A0","A1","B0","B1"), 0, FirmwareTypes.WCAPP  ),  # wolfcreek_fem_sas_update app
        "\x05\x0b\xff"      : (("A0","A1","B0","B1"), 0, FirmwareTypes.WCBOOT ),  # wolfcreek_fem_sas_update boot
        "\x05\x0b\x08"      : (("A0",              ), 0, FirmwareTypes.WCBB   ),  # wc_baseboard
        "\x05\x0b\x09"      : (("A0",     "B0"     ), 0, FirmwareTypes.WCMI   ),  # wc_midplane
        "\x05\x0b\x0a"      : (("A0",              ), 0, FirmwareTypes.WCSSM  ),  # wc_status
        
        FirmwareTypes.WCBIOS: (("A" ,     "B"      ), 0, FirmwareTypes.WCBIOS ),
        0x0112              : (("A" ,     "B"      ), 0, FirmwareTypes.U112   ),
        0x0187              : (("A" ,     "B"      ), 0, FirmwareTypes.U187   ),
        0x0199              : (("A" ,     "B"      ), 0, FirmwareTypes.U199   ),
        0x1000              : (("A" ,     "B"      ), 0, FirmwareTypes.U1000  ),
        0x1001              : (("A" ,     "B"      ), 0, FirmwareTypes.U1001  ),
        0x1002              : (("A" ,     "B"      ), 0, FirmwareTypes.U1002  ),
        0x1003              : (("A" ,     "B"      ), 0, FirmwareTypes.U1003  ),
        0x1004              : (("A" ,     "B"      ), 0, FirmwareTypes.U1004  ),
        0x1005              : (("A" ,     "B"      ), 0, FirmwareTypes.U1005  ),
        0x1006              : (("A" ,     "B"      ), 0, FirmwareTypes.U1006  ),
        FirmwareTypes.WCBMC : (("A" ,     "B"      ), 0, FirmwareTypes.WCBMC  ),
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
#             tmpdir = tempfile.mkdtemp("", "wcfw-")
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
        """ Attempt to determine version and type of a firmware file. """
        """
        Return a tuple with
          the version string,
          the keymap entry, or None
        """
        
        with open(filename, 'rb') as f:

            # Try JBL types.
            f.seek(0x00)
            magic = f.read(8)
            if "JBL" in magic:
                f.seek(0x08)
                key = f.read(3)  # product id, hardware rev, destination partition
                self._log(3, "key = %.2x,%.2x,%.2x %s" % (ord(key[0]), ord(key[1]), ord(key[2]), filename))
                mapped = self.keymap[key] if key in self.keymap else None
                if mapped[2] is FirmwareTypes.WCISTR:
                    if "ALL_IN_ONE" in filename:
                        mapped = list(mapped)
                        mapped[2] = FirmwareTypes.WCALL
        
                f.seek(0x0c)
                version = f.read(2)
                version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
                version = "%04X" % version
                self._log(2, "file version   = "+version)
                if version == "0000":
                    f.seek(0x0e)
                    version = f.read(2)
                    version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
                    version = "%04x" % version
                    self._log(2, "file version   = "+version)
                return (FirmwareUtils.normalize_version(version), mapped)

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
                    return (FirmwareUtils.normalize_version(version), self.keymap[FirmwareTypes.WCBIOS])
            
            # Try PLX EEPROMs.
            retval = self.identifyfile_plx(filename)
            if retval:
                return retval
            
            # Try BMC.
            m = re.search(".*WC_BMC_([0-9a-fA-F]*)\.bin", filename)
            if m:
                version = m.group(1)
                return (FirmwareUtils.normalize_version(version), self.keymap[FirmwareTypes.WCBMC])
#                 p = subprocess.call(["grep", "-q", "ifconfig", filename])
#                 if p is 0:
#                     return ("-", self.keymap[FirmwareTypes.WCBMC])
            
            # unknown
            self._log(2, "file is not recognizable firmware: "+filename)
            return None
            
    
    def identifyfile_plx(self, filename):
        prog = self.parse_plx(filename)
        if prog:
            for entry in prog:
                if entry[0] == 0x029c:
                    typ =          ((entry[2] >> 16) & 0xffff)
                    ver = "%.4X" % ((entry[2] >>  0) & 0xffff)
                    mapped = self.keymap[typ] if typ in self.keymap else None
                    return (FirmwareUtils.normalize_version(ver), mapped)
            # It doesn't have the 0x29c register with version and type,
            # so guess type based on filename.  Version is hopeless.
            if "U112" in filename: return ("", self.keymap[0x0112])
            if "U187" in filename: return ("", self.keymap[0x0187])
            if "U199" in filename: return ("", self.keymap[0x0199])
            # All 97xx files should have 0x29c register.
            return None  # Cannot determine PLX EEPROM file type nor version.
        else:
            return None  # If parse_plx fails, it's not a PLX EEPROM file.

    def _populate_from_file(self, filename):
        """
        We have a file. If it's an archive, split it and populate the directory.
        """

        def combine_istr_app(tmpdir, f1, f2):
            """
            We have both ISTR and APP type files. Combine them into a single file.
            """
            if os.path.isfile(tmpdir+'/'+f1) and os.path.isfile(tmpdir+'/'+f2):
                # We have both istr and app sections; combine them.
                with open(tmpdir+'/'+f1+"-"+f2, "wb") as fw:
                    for frname in (f1, f2):
                        with open(tmpdir+'/'+frname) as fr:
                            fw.write(fr.read())
                        os.remove(tmpdir+'/'+frname)

        if filename.split('.')[-1] in ("xlsx","docx"):
            # Some Microsoft Office files can be unpacked with 7za, but we don't bother.
            self._populate_from_single_file(filename)
        else:
            tmpdir = tempfile.mkdtemp("", "wcfw-")
            self.tmpdirs.append(tmpdir)
            #TODO errorcheck
            result = subprocess.call(['7za','x','-o'+tmpdir,filename], stdout=open("/dev/null","w"))
            #print "result =", result
            if   result is 0:
                self._populate_from_dir(tmpdir)
            elif result is 2:
                # not an archive parsable by 7z
                jbl_list = self.parse_jbl(filename)
                if len(jbl_list) <= 1 or \
                    (len(jbl_list) is 2 and (
                        (jbl_list[0][0] == "\x02\xa0\x02" and jbl_list[1][0] == "\x02\xa0\x05") or
                        (jbl_list[0][0] == "\x03\xa0\x02" and jbl_list[1][0] == "\x03\xa0\x05") or
                        (jbl_list[0][0] == "\x05\xa0\x02" and jbl_list[1][0] == "\x05\xa0\x05") or
                        False)):
                    # It's either not a JBL file or it's either a single-element JBL file or an istr/app combo.
                    self._populate_from_single_file(filename)
                else:
                    # It's a JBL file that needs to be split up.
                    for jbl_item in jbl_list:
                        fn = "%.2x%.2x%.2x" % tuple(ord(c) for c in jbl_item[0])
                        with open(tmpdir+'/'+fn, 'wb') as f:
                            f.write(jbl_item[2])
                    combine_istr_app(tmpdir, "02a002","02a005")
                    combine_istr_app(tmpdir, "03a002","03a005")
                    combine_istr_app(tmpdir, "05a002","05a005")
                    self._populate_from_dir(tmpdir)
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
    
    def parse_jbl(self, filename):
        with open(filename, 'rb') as f:
            
            offset = 0  # Start at the beginning
            filesize = os.fstat(f.fileno()).st_size
            retval = []
            while offset+0x1c < filesize:
                # Check magic number.
                f.seek(offset+0x00)
                magic = f.read(3)
                if magic != "JBL":
                    self._log(3, "bad magic at 0x%x in %s" % (offset, filename))
                    return retval
                
                f.seek(offset+0x08)
                key = f.read(3)  # product id, hardware rev, destination partition
                self._log(2, "key = %.2x,%.2x,%.2x %s" % (ord(key[0]), ord(key[1]), ord(key[2]), filename))
    
                f.seek(offset+0x0c)
                version = f.read(2)
                version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
                version = "%04X" % version
                self._log(2, "file version   = "+version)
                if version == "0000":
                    f.seek(offset+0x0e)
                    version = f.read(2)
                    version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
                    version = "%04x" % version
                    self._log(2, "file version   = "+version)
    
                f.seek(offset+0x10)
                length = struct.unpack(">I", f.read(4))[0]  # big-endian 4-byte unsigned int

                f.seek(offset+0x00)
                retval.append((key, version, f.read(0x1c+length)))
            
                offset += 0x1c + length
                
            return retval

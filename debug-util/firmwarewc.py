#!/usr/bin/env python
version = "0.1.3"

# import serial
# from xmodem import XMODEM
#from time import sleep
import pexpect.fdpexpect  # @UnusedImport
import sys
# import os.path
import subprocess
import re

from firmwarecli  import FirmwareCli
from firmwarefile import FirmwareTypes, FirmwareUtils

installdir = "/usr/local/lib/wcdu/"

class FirmwareBios:
    """
    Update and check version of BIOS.
    Must run on the compute node.
    """
    def __init__(self):
        self.verbosity = 1
        pass

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def update(self, filename):
        subprocess.call([installdir+"utilities/flashrom", "-p", "internal", "-l", installdir+"utilities/layout.txt", "-i", "bios", "-f", "-w", filename])
    
    def version(self):
        version = subprocess.check_output(["dmidecode", "-s", "bios-version"])
        version = version.strip()
        return FirmwareUtils.normalize_version(version)
    
class FirmwareBmc:
    """
    Update and check version of the BMC.
    Must run on the compute node.
    """
    def __init__(self):
        self.verbosity = 1
        pass

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def update(self, filename):
        # TODO error checking
        logfile = sys.stdout if self.verbosity >= 1 else None
        self.procssh = pexpect.spawn(installdir+"utilities/Yafuflash64", ["-full", "-cd", "-no-reboot", filename], logfile=logfile)
        match = self.procssh.expect([
            pexpect.TIMEOUT,
            pexpect.EOF,
            "The Module boot major or minor version is different from the one in the image.*Enter your Option : ",
            "Existing Image and Current Image are Same.*Enter your Option : ",
            "The Module boot size is different from the one in the Image.*Enter your Option : ",
            ], timeout=60*12)
        if   match is 0:  # timeout
            #TODO
            pass
        elif match is 1:  # eof
            #TODO
            pass
        elif match is 2:  # The Module boot major or minor
            self.procssh.sendline("y")
        elif match is 3:  # Existing Image and Current Image are Same
            self.procssh.sendline("y")
        elif match is 4:  # The Module boot size is different
            self.procssh.sendline("y")
        self.procssh.expect(pexpect.EOF, timeout=60*12)
        self.procssh.close(); self.procssh = None
    
    def activate_cpld(self):
        # For now we are supposed to follow the BMC update with this command to program power/controller/the CPLD, but it resets.
        subprocess.call(["ipmitool", "raw", "0x3c", "0x00", "0x01", "0x00"])
        subprocess.call(["poweroff"])  # Assuming we're running on the compute node.
        
    def activate_psoc(self):
        # For now we are supposed to follow the BMC update with this command to program PSoC.
        # Behavior is unknown as it only works on DVT hardware.
        subprocess.call(["ipmitool", "raw", "0x3c", "0x00", "0x01", "0x01"])
        
    def version(self):
        # To get revisions of BMC and power/controller/the CPLD:
        #line = subprocess.check_output(["ipmitool", "-H", self._get_ip(), "-U", "admin", "-P", "admin", "raw", "0x3c", "0x00", "0x00", "0x00"])
        # Maybe it's just the running and next CPLD versions.
        # Instead do: ipmitool bmc info
        version = subprocess.check_output("ipmitool bmc info | grep 'Firmware Revision' | cut -d: -f2 | tr -d ' '", shell=True)
        version = version.strip()
        return FirmwareUtils.normalize_version(version)
        
class FirmwarePlx:
    """
    Update and check version of 87xx PLX EEPROMs.
    Must run on the compute node.
    """
    def __init__(self, typ, d=None):
        self.verbosity = 1
        self.typ = typ
        self.d = d    # -d parameter to PlxEep
        if   typ == FirmwareTypes.U199: self.s = "00:01.0"; self.p = "8750,AB"
        elif typ == FirmwareTypes.U187: self.s = "00:02.0"; self.p = "8796,AB"
        elif typ == FirmwareTypes.U112: self.s = "00:03.0"; self.p = "8796,AB"
        else:                           self.s = None     ; self.p = None  #TODO

        # Load kernel modules.
        #TODO check for errors
        #subprocess.call("cd "+installdir+"utilities/PlxSdk; lsmod | grep -q Plx8000_NT || Bin/Plx_load 8000n", shell=True)
        subprocess.call("cd "+installdir+"utilities/PlxSdk; lsmod | grep -q PlxSvc     || Bin/Plx_load Svc  ", shell=True)

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def update(self, filename):
        logfile = sys.stdout if self.verbosity >= 1 else None
        if self.d:
            # We were handed the menu item number, i.e. the parameter to the -d switch.
            if filename[0] == "/":
                # PlxEep treats anything starting with / or - as a switch.
                # Prepend many ../ combinations to eventually get to the top.
                filename = "../" * 40 + ".." + filename
            p = [
                installdir+"utilities/PlxSdk/Samples/PlxEep/App/PlxEep",
                "-l", filename,
                "-d", str(self.d),
                ]
            if self.verbosity >= 1: print p
            subprocess.call(p)
        else:
            # Find the bus number.
            line = subprocess.check_output("lspci -x -s "+self.s+" | grep ^10:", shell=True)
            bus = line.split()[10]
    
            self.procssh = pexpect.spawn(installdir+"utilities/PlxSdk/Samples/PlxEep/App/PlxEep", ["-l", filename, "-p", self.p, "-d", "0"], logfile=logfile)
            itemnumber = None
            while True:
                match = self.procssh.expect([
                    pexpect.TIMEOUT,
                    " +[0-9]+\.",
                    "b:"+bus,
                    "Device selection --> ",
                    ], timeout=5)
                if match is 0:
                    # timeout
                    # indicate a failure
                    return False
                elif match is 1:
                    # menu item number
                    m = re.match(" +([0-9]+)\.", match.after)
                    if not m:
                        return False
                    recentitemnumber = m.group(1)
                elif match is 2:
                    # bus number
                    itemnumber = recentitemnumber
                elif match is 3:
                    # Device selection prompt
                    self.procssh.sendline(itemnumber)
                    break
            self.procssh.expect(pexpect.EOF, timeout=None)  # Wait for the program to terminate.
            self.procssh.close()
            self.procssh = None
    
    def version(self):
        # plxcm to read, mmr 29c
        return None #TODO
    
class FirmwareU199(FirmwarePlx):
    def __init__(self):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U199).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U199).version()

class FirmwareU187(FirmwarePlx):
    def __init__(self):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U187).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U187).version()

class FirmwareU112(FirmwarePlx):
    def __init__(self):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U112).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U112).version()
    
class FirmwareU1000(FirmwarePlx):  # U112
    def __init__(self, d=5):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1000, d=5).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1000, d=5).version()
    
class FirmwareU1001(FirmwarePlx):  # U187
    def __init__(self, d=9):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1001, d=9).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1001, d=9).version()
    
class FirmwareU1002(FirmwarePlx):  # U116
    def __init__(self, d=13):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1002, d=13).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1002, d=13).version()
    
class FirmwareU1003(FirmwarePlx):  # U119
    def __init__(self, d=3):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1003, d=3).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1003, d=3).version()
    
class FirmwareU1004(FirmwarePlx):  # U120
    def __init__(self, d=7):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1004, d=7).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1004, d=7).version()
    
class FirmwareU1005(FirmwarePlx):  # U121
    def __init__(self, d=11):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1005, d=11).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1005, d=11).version()
    
class FirmwareU1006(FirmwarePlx):  # U199
    def __init__(self, d=15):
        pass
    def update(self, filename): FirmwarePlx(FirmwareTypes.U1006, d=15).update(filename)
    def version(self):   return FirmwarePlx(FirmwareTypes.U1006, d=15).version()
    


class FirmwareExpander(FirmwareCli):

    def __init__(self, tty=None, filename=None, expnum=0, verbosity=2):
        """
        tty, filename, verbosity are the same as in FirmwareCli.__init__
        expnum is the FEM number to be affected, 0 or 1
        ip is the desired IP address or None for no change
        """
        self.tty       = tty
        self.filename  = filename
        self.expnum    = expnum
        self.verbosity = verbosity
        if self.tty:
            super(FirmwareExpander, self).__init__(self.tty, self.filename, self.verbosity)
        self.hw_versions = None

    def set_serial(self, tty):
        self.tty = tty
        super(FirmwareExpander, self).__init__(self.tty, self.filename, self.verbosity)
        self.hw_versions = None

    def set_expnum(self, expnum):
        self.expnum = expnum
    
    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def _mux_set(self, port, disable=1):
        dflag = 0x80 if disable else 0
        returncode = subprocess.call(["ipmitool", "raw", "0x3c", "3", "0x%.2x" % (port+dflag)])
        return returncode is 0
    
    def _mux_restore(self):
        return self._mux_set(0,0)
        
    def update(self, filename):
        super(FirmwareExpander, self).set_filename(filename)
        if self._mux_set(2+self.expnum):
            self._log(3, "setup succeeded; updating")
            super(FirmwareExpander, self).update()
            self._log(3, "update finished; resetting port")
            self._mux_restore()
            self._log(3, "resetting port finished")
            self.hw_versions = None
    
    def version(self, typ):
        self._log(3, "FirmwareExpander:expnum = "+str(self.expnum))
        if self._mux_set(2+self.expnum):
            if not self.hw_versions:
                self._log(3, "setup succeeded; fetching version")
                self.hw_versions = super(FirmwareExpander, self).identifydevice()
                self._log(3, "version finished; resetting port")
                self._mux_restore()
                self._log(3, "resetting port finished")
            try:
                return FirmwareUtils.normalize_version(self.hw_versions[0][typ])
            except:
                pass
        return None

class FirmwareSas0 (FirmwareExpander):
    def __init__(self, tty=None, filename=None, verbosity=2):
        super(FirmwareSas0, self).__init__(tty=tty, filename=filename, expnum=0, verbosity=verbosity)
    def version(self): return super(FirmwareSas0 , self).version(FirmwareTypes.APP  )

class FirmwareSas1 (FirmwareExpander):
    def __init__(self, tty=None, filename=None, verbosity=2):
        super(FirmwareSas1, self).__init__(tty=tty, filename=filename, expnum=1, verbosity=verbosity)
    def version(self): return super(FirmwareSas1 , self).version(FirmwareTypes.APP  )

class FirmwareBoot0(FirmwareExpander):
    def __init__(self, tty=None, filename=None, verbosity=2):
        super(FirmwareBoot0, self).__init__(tty=tty, filename=filename, expnum=0, verbosity=verbosity)
    def version(self): return super(FirmwareBoot0, self).version(FirmwareTypes.BOOT )

class FirmwareBoot1(FirmwareExpander):
    def __init__(self, tty=None, filename=None, verbosity=2):
        super(FirmwareBoot1, self).__init__(tty=tty, filename=filename, expnum=1, verbosity=verbosity)
    def version(self): return super(FirmwareBoot1, self).version(FirmwareTypes.BOOT )

class FirmwareWcbb (FirmwareExpander):
    def version(self): return super(FirmwareWcbb , self).version(FirmwareTypes.WCBB )

class FirmwareWcmi (FirmwareExpander):
    def version(self): return super(FirmwareWcmi , self).version(FirmwareTypes.WCMI )

class FirmwareWcssm(FirmwareExpander):
    def version(self): return super(FirmwareWcssm, self).version(FirmwareTypes.WCSSM)


# if __name__ == "__main__":
#     filename = "firmware/WC/wolfcreek_fem_sas_update_01_01.bin"
#     fw = FirmwareSas(tty="/dev/ttyUSB0", filename=filename, ip=None, verbosity=2)
#     fw.update()

if __name__ == "__main__":
    # TODO Do we need the user to supply IP address?
    if len(sys.argv) != 4:
        print "usage:", sys.argv[0].split('/')[-1], "<tty device file> <firmware file> <expander number>"
        sys.exit(-1)
    tty      =     sys.argv[1]
    filename =     sys.argv[2]
    expnum   = int(sys.argv[3])
    
    print "program version =", version
    
    fw = FirmwareSas1(tty, filename, expnum, ip=None, verbosity=2)
    fw.update_bmc(filename)
    sys.exit(0)
    
    #fw.port_setup()
#     fid = fw.identifyfile()
#     did = fw.identifydevice()
#     if not fid:
#         print "Aborting; cannot get version string from file, '" + filename +"'."
#         sys.exit(-1)
#     if not did:
#         print "Aborting; cannot get version string from device at " + tty + "'."
#         sys.exit(-1)
#     fver, mapped      = fid
#     expanders, imageid, typ = mapped
#     dvers, expanderid = did
#     if expanderid not in expanders:
#         print "Aborting; mismatch between expander type and firmware type."
#         print expanderid, "not in", expanders
#         sys.exit(-1)
    fw.update()
#     fw.identifydevice()
    
#     if fw.procssh:
#         fw.port_reset()
    fw._mux_restore()

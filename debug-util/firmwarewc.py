#!/usr/bin/env python

version = "0.1.0"

# import serial
# from xmodem import XMODEM
#from time import sleep
import pexpect.fdpexpect  # @UnusedImport
import sys
# import os.path
import subprocess
import re

from firmwarecli import FirmwareCli
from firmwarefile import FirmwareTypes

installdir = "/usr/local/lib/wcdu/"

class FirmwareBios:
    """
    Update and check version of BIOS.
    Must run on the compute node.
    """
    def __init__(self):
        pass

    def update(self, filename):
        subprocess.call([installdir+"utilities/flashrom", "-p", "internal", "-l", installdir+"utilities/layout.txt", "-i", "bios", "-f", "-w", filename])
    
    def version(self):
        version = subprocess.check_output(["dmidecode", "-s", "bios-version"])
        version = version.strip()
        return version
    
class FirmwareBmc:
    """
    Update and check version of the BMC.
    Must run on the compute node.
    """
    def __init__(self):
        pass

    def update(self, filename):
        # TODO error checking
        self.procssh = pexpect.spawn(installdir+"utilities/Yafuflash64", ["-full", "-cd", "-no-reboot", filename], logfile=sys.stdout)
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
        # For now we are supposed to follow the BMC update with this command to program power/controller/the CPLD, but it resets.
        #subprocess.call(["ipmitool", "-H", self._get_ip(), "-U", "admin", "-P", "admin", "raw", "0x3c", "0x00", "0x01", "0x00"])
        #subprocess.call(["poweroff"])  # Assuming we're running on the compute node.
        
    def version(self):
        # To get revisions of BMC and power/controller/the CPLD:
        #line = subprocess.check_output(["ipmitool", "-H", self._get_ip(), "-U", "admin", "-P", "admin", "raw", "0x3c", "0x00", "0x00", "0x00"])
        # Maybe it's just the running and next CPLD versions.
        # Instead do: ipmitool bmc info
        version = subprocess.check_output("ipmitool bmc info | grep 'Firmware Revision' | cut -d: -f2 | tr -d ' '", shell=True)
        version = version.strip()
        return version
        # TODO test
        
class FirmwarePlx:
    """
    Update and check version of 87xx PLX EEPROMs.
    Must run on the compute node.
    """
    def __init__(self, typ):
        self.typ = typ
        if   typ == FirmwareTypes.U199: self.s = "00:01.0"; self.p = "8750,AB"
        elif typ == FirmwareTypes.U187: self.s = "00:02.0"; self.p = "8796,AB"
        elif typ == FirmwareTypes.U112: self.s = "00:03.0"; self.p = "8796,AB"
        else:                           self.s = None     ; self.p = None  #TODO

        # Load kernel modules.
        #TODO check for errors
        subprocess.call("cd "+installdir+"utilities/PlxSdk; lsmod | grep -q Plx8000_NT || Bin/Plx_load 8000n", shell=True)
        subprocess.call("cd "+installdir+"utilities/PlxSdk; lsmod | grep -q PlxSvc     || Bin/Plx_load Svc  ", shell=True)

    def update(self, filename):
        # TODO test after fixing EEPROMs
        # Find the bus number.
        line = subprocess.check_output("lspci -x -s "+self.s+" | grep ^10:", shell=True)
        bus = line.split()[10]
        self.procssh = pexpect.spawn(installdir+"utilities/PlxSdk/Samples/PlxEep/App/PlxEep", ["-l", filename, "-p", self.p, "-d", "0"], logfile=sys.stdout)
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
    


class FirmwareFem(FirmwareCli):

    def __init__(self, tty, filename=None, expnum=0, ip=None, verbosity=0):
        """
        tty, filename, verbosity are the same as in FirmwareCli.__init__
        expnum is the FEM number to be affected, 0 or 1
        ip is the desired IP address or None for no change
        """
        super(FirmwareFem, self).__init__(tty, filename, verbosity)
        self.expnum = expnum
#         self.ip = ip
#         
#         self.procssh = None
#         self.curr_ip = None
    def set_expnum(self, expnum):
        self.expnum = expnum
    
#     def _get_ip(self, new_ip=None):
#         # Make sure we're logged in.
#         if self.curr_ip:
#             return self.curr_ip
#         
#         triesleft = 5
#         while True:
#             self.proc.sendline("")
#             match = self.proc.expect([
#                 pexpect.TIMEOUT,
#                 "login:",
#                 "# ",
#                 "@",
#                 ])
#             if   match is 0:  # TIMEOUT
#                 return None
#             elif match is 1:  # login:
#                 self.proc.sendline("sysadmin")
#                 self.proc.expect("assword:", timeout=5)
#                 self.proc.sendline("sysadmin")
#                 self.proc.expect("# ", timeout=5)
#             elif match is 2:
#                 break  # Already logged in.
#             elif match is 3:  # UART MUX is switched to the wrong port.
#                 self.proc.sendcontrol("^")
#                 self.proc.send("a")
#             triesleft -= 1
#             if triesleft is 0:
#                 return None
#         # Now logged in.
#         
#         # Optionally set IP, and get it.
#         if new_ip:
#             self.proc.sendline("ifconfig eth0 "+new_ip)
#             self.proc.expect("# ")
#         self.proc.sendline("ifconfig eth0")
#         match = self.proc.expect(["inet addr:", "# "])
#         if   match is 0:
#             self.proc.expect(" ")
#             curr_ip = self.proc.before
#         elif match is 1:
#             curr_ip = None
#         
#         # Log out.
#         self.proc.sendline("exit")
#         
#         self.curr_ip = curr_ip
#         return curr_ip
#     
#     def _ssh_start(self, ip):
#         """
#         Ensure the ssh process is logged in.
#         """
#         if self.procssh:
#             # We think it's already ready. Test it.
#             self.procssh.sendline("")
#             match = self.procssh.expect([pexpect.TIMEOUT, "# "])
#             if   match is 0:  # TIMEOUT, close and reopen
#                 self._ssh_stop()
#             elif match is 1:  # Got prompt.
#                 return True
#         while not self.procssh:
#             self.procssh = pexpect.spawn("ssh", ["-lsysadmin", "-oStrictHostKeyChecking=no", ip], logfile=sys.stdout)
#             while True:
#                 match = self.procssh.expect([
#                     pexpect.TIMEOUT,
#                     "# ",
#                     "assword:",
#                     "continue connecting (yes/no)? ",
#                     'remove with: ssh-keygen -f "',
#                     ], timeout=5)
#                 if   match is 0:  # TIMEOUT
#                     self._ssh_stop()
#                     return False
#                 elif match is 1:  # We got a prompt.
#                     break
#                 elif match is 2:  # assword:
#                     self.procssh.sendline("sysadmin")
#                 elif match is 3:  # continue connecting
#                     self.procssh.sendline("yes")
#                 elif match is 4:  # remove with:
#                     self.procssh.expect('"')
#                     subprocess.call(["ssh-keygen", "-f", self.procssh.before, "-R", ip])  # Remove old key.
# #                     self.procssh.expect("Permission denied (publickey,password).")
#                     self._ssh_stop()  # Causes restart of the ssh spawn above.
#                     break
#         return True
#     
#     def _ssh_stop(self):
#         self.procssh.close()
#         self.procssh = None
#         
#     def _ssh_cmd(self, cmd):
#         self.procssh.sendline(cmd)
#         self.procssh.expect("# ")
    
    def _mux_set(self, port, disable=1):
        dflag = 0x80 if disable else 0
        returncode = subprocess.call(["ipmitool", "raw", "0x3c", "3", "0x%.2x" % (port+dflag)])
        return returncode is 0
#         self._ssh_cmd("i2c-test -b 7 -s 64 -w -d a6 "+str(disable))  # Disable hotkey support.
#         self._ssh_cmd("i2c-test -b 7 -s 64 -w -d a5 "+str(port))     # Set the UART MUX to the desired port
    
    def _mux_restore(self):
        return self._mux_set(0,0)
#         self._mux_set(4, disable=0)
    
#     def port_setup(self):
#         ip = self._get_ip()
#         print "ip =", ip
#         if not ip:
#             raise("cannot get IP address")
#             return False
#         if ip:
#             if not self._ssh_start(ip):
#                 raise("cannot start ssh")
#                 return False
#             self._mux_set(2+self.expnum)  # Switch the UART MUX to requested SAS expander.
#             return True
#         
#     def port_reset(self):
#         self._mux_restore()
#         self._ssh_stop()
        
    def update(self, filename):
        super(FirmwareFem, self).set_filename(filename)
        if self._mux_set(2+self.expnum):
            print "setup succeeded; updating"  #DEBUG
            super(FirmwareFem, self).update()
            print "update finished; resetting port"  #DEBUG
            self._mux_restore()
            print "resetting port finished"  #DEBUG
    
    def version(self):
        if self._mux_set(2+self.expnum):
            print "setup succeeded; fetching version"  #DEBUG
            retval = super(FirmwareFem, self).identifydevice()
            print "version finished; resetting port"  #DEBUG
            self._mux_restore()
            print "resetting port finished"  #DEBUG
            try:
                return retval[0]["app"]  #TODO handle more than just app version in wcfw
            except:
                pass
        return None


# if __name__ == "__main__":
#     filename = "firmware/WC/wolfcreek_fem_sas_update_01_01.bin"
#     bbfw = FirmwareFem(tty="/dev/ttyUSB0", filename=filename, ip=None, verbosity=2)
#     bbfw.update()

if __name__ == "__main__":
    # TODO Do we need the user to supply IP address?
    if len(sys.argv) != 4:
        print "usage:", sys.argv[0].split('/')[-1], "<tty device file> <firmware file> <expander number>"
        sys.exit(-1)
    tty      =     sys.argv[1]
    filename =     sys.argv[2]
    expnum   = int(sys.argv[3])
    
    print "program version =", version
    
    fw = FirmwareFem(tty, filename, expnum, ip=None, verbosity=2)
    fw.update_bmc(filename)
    sys.exit(0)
    
    #bbfw.port_setup()
#     fid = bbfw.identifyfile()
#     did = bbfw.identifydevice()
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
#     bbfw.identifydevice()
    
#     if bbfw.procssh:
#         bbfw.port_reset()
    fw._mux_restore()

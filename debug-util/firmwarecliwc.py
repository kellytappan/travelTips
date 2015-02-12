#!/usr/bin/env python

version = "0.0.1+"

# import serial
# from xmodem import XMODEM
#from time import sleep
import pexpect.fdpexpect  # @UnusedImport
import sys
# import os.path
import subprocess
from firmwarecli import FirmwareCli

class FirmwareCliWC(FirmwareCli):

    def __init__(self, tty, filename, expnum, ip=None, verbosity=0):
        """
        tty, filename, verbosity are the same as in FirmwareCli.__init__
        expnum is the FEM number to be affected, 0 or 1
        ip is the desired IP address or None for no change
        """
        super(FirmwareCliWC, self).__init__(tty, filename, verbosity)
        self.expnum = expnum
        self.ip = ip
        
        self.procssh = None
        self.curr_ip = None
    
    def _get_ip(self, new_ip=None):
        # Make sure we're logged in.
        if self.curr_ip:
            return self.curr_ip
        
        triesleft = 5
        while True:
            self.proc.sendline("")
            match = self.proc.expect([
                pexpect.TIMEOUT,
                "login:",
                "# ",
                "@",
                ])
            if   match is 0:  # TIMEOUT
                return None
            elif match is 1:  # login:
                self.proc.sendline("sysadmin")
                self.proc.expect("assword:", timeout=5)
                self.proc.sendline("sysadmin")
                self.proc.expect("# ", timeout=5)
            elif match is 2:
                break  # Already logged in.
            elif match is 3:  # UART MUX is switched to the wrong port.
                self.proc.sendcontrol("^")
                self.proc.send("a")
            triesleft -= 1
            if triesleft is 0:
                return None
        # Now logged in.
        
        # Optionally set IP, and get it.
        if new_ip:
            self.proc.sendline("ifconfig eth0 "+new_ip)
            self.proc.expect("# ")
        self.proc.sendline("ifconfig eth0")
        match = self.proc.expect(["inet addr:", "# "])
        if   match is 0:
            self.proc.expect(" ")
            curr_ip = self.proc.before
        elif match is 1:
            curr_ip = None
        
        # Log out.
        self.proc.sendline("exit")
        
        self.curr_ip = curr_ip
        return curr_ip
    
    def _ssh_start(self, ip):
        """
        Ensure the ssh process is logged in.
        """
        if self.procssh:
            # We think it's already ready. Test it.
            self.procssh.sendline("")
            match = self.procssh.expect([pexpect.TIMEOUT, "# "])
            if   match is 0:  # TIMEOUT, close and reopen
                self._ssh_stop()
            elif match is 1:  # Got prompt.
                return True
        while not self.procssh:
            self.procssh = pexpect.spawn("ssh", ["-lsysadmin", "-oStrictHostKeyChecking=no", ip], logfile=sys.stdout)
            while True:
                match = self.procssh.expect([
                    pexpect.TIMEOUT,
                    "# ",
                    "assword:",
                    "continue connecting (yes/no)? ",
                    'remove with: ssh-keygen -f "',
                    ], timeout=5)
                if   match is 0:  # TIMEOUT
                    self._ssh_stop()
                    return False
                elif match is 1:  # We got a prompt.
                    break
                elif match is 2:  # assword:
                    self.procssh.sendline("sysadmin")
                elif match is 3:  # continue connecting
                    self.procssh.sendline("yes")
                elif match is 4:  # remove with:
                    self.procssh.expect('"')
                    subprocess.call(["ssh-keygen", "-f", self.procssh.before, "-R", ip])  # Remove old key.
#                     self.procssh.expect("Permission denied (publickey,password).")
                    self._ssh_stop()  # Causes restart of the ssh spawn above.
                    break
        return True
    
    def _ssh_stop(self):
        self.procssh.close()
        self.procssh = None
        
    def _ssh_cmd(self, cmd):
        self.procssh.sendline(cmd)
        self.procssh.expect("# ")
    
    def _mux_set(self, port, disable=1):
        self._ssh_cmd("i2c-test -b 7 -s 64 -w -d a6 "+str(disable))  # Disable hotkey support.
        self._ssh_cmd("i2c-test -b 7 -s 64 -w -d a5 "+str(port))     # Set the UART MUX to the desired port
    
    def _mux_restore(self):
        self._mux_set(4, disable=0)
    
    def port_setup(self):
        ip = self._get_ip()
        print "ip =", ip
        if not ip:
            raise("cannot get IP address")
            return False
        if ip:
            if not self._ssh_start(ip):
                raise("cannot start ssh")
                return False
            self._mux_set(2+self.expnum)  # Switch the UART MUX to requested SAS expander.
            return True
        
    def port_reset(self):
        self._mux_restore()
        self._ssh_stop()
        
    def update(self):
        if self.port_setup():
            super(FirmwareCliWC, self).update()
            self.port_reset()
            
    def update_bios(self):
        # TODO
        # run on compute node
        # flashrom -p internal -l layout.txt -i bios -f -w 0101.FD
        pass
    
    def update_bmc(self):
        # TODO
        # run on compute node
        # yafuflash
        pass

    def update_plx(self):
        # TODO
        # run on compute node
        # plxeep
        subprocess.call("cd utilities/PlxSdk; lsmod | grep -q Plx8000_NT || Bin/Plx_load 8000n", shell=True)
        subprocess.call("cd utilities/PlxSdk; lsmod | grep -q PlxSvc     || Bin/Plx_load Svc  ", shell=True)
        p = subprocess.Popen("lspci -x -s 00:01.0 | grep ^10:", shell=True, stdout=subprocess.PIPE)
        for line in p.stdout:
            bus112 = line.split()[10]
        p = subprocess.Popen("lspci -x -s 00:02.0 | grep ^10:", shell=True, stdout=subprocess.PIPE)
        for line in p.stdout:
            bus187 = line.split()[10]
        p = subprocess.Popen("lspci -x -s 00:03.0 | grep ^10:", shell=True, stdout=subprocess.PIPE)
        for line in p.stdout:
            bus199 = line.split()[10]
        print "bus112 =", bus112, ", bus187 =", bus187, ", bus199 =", bus199
        pass


# if __name__ == "__main__":
#     filename = "firmware/WC/wolfcreek_fem_sas_update_01_01.bin"
#     fw = FirmwareCliWC(tty="/dev/ttyUSB0", filename=filename, ip=None, verbosity=2)
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
    
    fw = FirmwareCliWC(tty, filename, expnum, ip=None, verbosity=2)
    fw.update_plx()
    sys.exit(0)
    
    fw.port_setup()
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
    
    if fw.procssh:
        fw.port_reset()

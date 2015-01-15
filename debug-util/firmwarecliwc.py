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

    def __init__(self, tty, filename, ip, verbosity=0):
        """
        tty, filename, verbosity are the same as in FirmwareCli.__init__
        ip is the desired IP address or None for no change
        """
        super(FirmwareCliWC, self).__init__(tty, filename, verbosity)
        self.ip = ip
        self.procssh = None
    
    def _get_ip(self, new_ip=None):
        # Make sure we're logged in.
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
            pass  # Already logged in.
        elif match is 3:  # UART MUX is switched to the wrong port.
            # TODO put this set of ifs in a loop
            self.proc.sendcontrol("^")
            self.proc.send("a")
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
        self._ssh_cmd("i2c-test -b 7 -s 64 -w -d a5 "+str(port))  # Set the UART MUX to the desired port
    
    def _mux_restore(self):
        self._mux_set(4, disable=0)


if __name__ == "__main__":
    filename = "firmware/WC/wolfcreek_fem_sas_update_01_01.bin"
    fw = FirmwareCliWC(tty="/dev/ttyUSB0", filename=filename, ip=None, verbosity=2)
    ip = fw._get_ip()
    print "ip =", ip
    if not ip:
        print "cannot get IP address"
        sys.exit(1)
    if ip:
        if not fw._ssh_start(ip):
            print "cannot start ssh"
            sys.exit(2)
        fw._mux_set(2)  # Switch the UART MUX to primary SAS expander.
        
        fw.update()
        
        fw._mux_restore()
        fw._ssh_stop()


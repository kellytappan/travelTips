from CLIcmd import *

import pexpect

class clicmd_serial(clicmd):
    
    timeout= .4   # seconds  # .3 works for 424 bytes
    
    def __init__(self, tty, baud=115200):
        self.tty  = tty
        self.baud = baud
        self.logfile = open("/tmp/serial-log", "w")
        self.proc = pexpect.spawn("python -m serial.tools/miniterm -b" + str(baud) + " " + self.tty, timeout=clicmd_serial.timeout, logfile=self.logfile)
        # Turn off echo, if it's on.
        self.flush()
        self.proc.sendline("garbage")   # should print "unknown_cmd"
        match = self.proc.expect(["garbage", "unknown_cmd"])
        if match == 0:
            # It printed "garbage" first, echo is on, turn it off.
            self.proc.sendline("echo")
            self.echo_toggled = True
        else:
            self.echo_toggled = False
        # Turn off prompt, if it's on.
        self.flush()
        self.proc.sendline("")   # Print a prompt, if prompt is on.
        self.proc.expect([">", pexpect.TIMEOUT])
        if match == 0:
            # It printed a prompt, turn it off.
            self.proc.sendline("prompt")
            self.prompt_toggled = True
        else:
            self.prompt_toggled = False
        
        self.flush()
        
    def __del__(self):
        # Restore "echo" and "prompt" to previous values.
        if self.echo_toggled  : self.proc.sendline("echo")
        if self.prompt_toggled: self.proc.sendline("prompt")
        self.flush()
        self.proc.close()
        
    def sendcmd(self, cmd):
        self.proc.sendline(cmd)
        self.proc.expect(pexpect.TIMEOUT)
        retval = self.proc.before
        self.flush()
        return retval
    
    def flush(self):
        try:
            while True:
                self.proc.read_nonblocking()
        except:
            None
        # Kludge to clear out self.proc.before.
        self.proc.sendline("garbage")
        self.proc.expect("unknown_cmd")
    
    
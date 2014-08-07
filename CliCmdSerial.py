from CliCmd import CliCmd

import pexpect

class CliCmdSerial(CliCmd):
    
    timeout= .4   # seconds  # .3 works for 424 bytes
    
    def __init__(self, tty, baud=115200):
        self.tty  = tty
        self.baud = baud
        self.logfile = open("/tmp/serial-log", "w")
        self.proc = pexpect.spawn("python -m serial.tools/miniterm -b" + str(baud) + " " + self.tty, timeout=CliCmdSerial.timeout, logfile=self.logfile)
        # Turn off echo, if it's on.
        self._flush()
        self.proc.sendline("garbage")   # should print "unknown_cmd"
        match = self.proc.expect(["garbage", "unknown_cmd"])
        if match == 0:
            # It printed "garbage" first, echo is on, turn it off.
            self.proc.sendline("echo")
            self.echo_toggled = True
        else:
            self.echo_toggled = False
        # Turn off prompt, if it's on.
        self._flush()
        self.proc.sendline("")   # Print a prompt, if prompt is on.
        self.proc.expect([">", pexpect.TIMEOUT])
        if match == 0:
            # It printed a prompt, turn it off.
            self.proc.sendline("prompt")
            self.prompt_toggled = True
        else:
            self.prompt_toggled = False
        
        self._flush()
        
    def __del__(self):
        # Restore "echo" and "prompt" to previous values.
        if self.echo_toggled  : self.proc.sendline("echo")
        if self.prompt_toggled: self.proc.sendline("prompt")
        self._flush()
        self.proc.close()
        
    def execute(self, cmd):
        self.proc.sendline(cmd)
        self.proc.expect(pexpect.TIMEOUT)
        retval = self.proc.before
        self._flush()
        return retval
    
    def _flush(self):
        try:
            while True:
                self.proc.read_nonblocking()
        except:
            None
        # Kludge to clear out self.proc.before.
        self.proc.sendline("garbage")
        self.proc.expect("unknown_cmd")
    
    
from CliCmd import CliCmd

import pexpect

class CliCmdSerial(CliCmd):

    timeout= .4   # seconds  # .3 works for 424 bytes

    def __init__(self, tty, baud=115200):
        self.tty  = tty
        self.baud = baud
        self.echo_toggled = False
        self.prompt_toggled = False
        self.logfile = open("/tmp/serial-log-"+tty[-1], "w")
        self.proc = pexpect.spawn("python -m serial.tools/miniterm -b" + str(baud) + " " + self.tty, timeout=CliCmdSerial.timeout, logfile=self.logfile)
        # Turn off echo, if it's on.
        self._flush()
        self.proc.sendline("garbage")   # should print "unknown_cmd"
        match = self.proc.expect(["garbage", "unknown_cmd", pexpect.TIMEOUT])
        if match == 0:
            # It printed "garbage" first, echo is on, turn it off.
            self.proc.sendline("echo")
            self.echo_toggled = True
        elif match == 1:
            self.echo_toggled = False
        elif match == 2:
            self.close()
            raise Exception("not connected " + tty)
            return
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

    def close(self):
        # Restore "echo" and "prompt" to previous values.
        try:
            if self.echo_toggled  : self.proc.sendline("echo")
            if self.prompt_toggled: self.proc.sendline("prompt")
            self._flush()
        except:
            pass
        try:
            self.proc.close()
        except:
            pass

    def __del__(self):
        self.close()

    def execute(self, cmd):
        """
        Send the command, cmd, to the device and return the output.
        """
        """
        TODO: Expect one line at a time with a shorter timeout.
        """
        self.proc.sendline(cmd)
        self.proc.expect(pexpect.TIMEOUT)
        # Strip carriage-returns from the output text.
        retval = self.proc.before.replace("\r", "")
        # Something is adding two newlines before and one after the data, compared to the SES page 0xe8 interface.
        if retval[0] == "\n": retval = retval[1:]
        if retval[0] == "\n": retval = retval[1:]
        if retval[-1] == "\n": retval = retval[:-1]
        self._flush()
        return retval

    def _flush(self):
        # Kludge to clear out self.proc.before.
        self.proc.expect("$")
        self.proc.expect("$")
        assert(self.proc.before == "")
        #print "len before =", len(self.proc.before)
        #if len(self.proc.before) > 4: print "before =", self.proc.before



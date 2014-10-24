#!/usr/bin/env python

version = "0.0.1+"

import serial
from xmodem import XMODEM
from time import sleep
import pexpect.fdpexpect
import sys
import os.path

from firmwarefile import FirmwareFile

class FirmwareCli:
    """
    Update firmware on one device.
    """
    
    baudrate = 115200
    
    def __init__(self, tty, filename, verbosity=0):
        self.tty       = tty
        self.filename  = filename
        self.verbosity = verbosity

        # Initialize serial port and pexpect.
        self.sport = serial.Serial(port=self.tty, baudrate=self.baudrate, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        self.logfile = open("/tmp/serial-log-"+tty[-1], "w")
        self.proc = pexpect.fdpexpect.fdspawn(self.sport, logfile=self.logfile, timeout=.4)
        
        self.ruthere = None   # unknown
        
        #self._interrupt_xmodem()
    
    def set_filename(self, filename):
        self.filename = filename
    
    def get_prompt(self):
        self.ruthere = None
        if self._ruthere():
            return self._appmode()
        else:
            return None

    def update(self, callback=None):
        if not self._ruthere():
            self._log(0, 'Device does not respond: '+self.tty)
            return
        self._bootmode()
        self._sendfile(self.filename, callback)
        self._appmode()
        
        # Done. Shut things down.
        #sport.close()
        #self.proc.close()
    
    def _log(self, level, message):
        if self.verbosity >= level:
            print message
    
    def _flush(self):
        """ Kludge to clear out self.proc.before. """
        self.proc.expect(["$", pexpect.TIMEOUT])
        self.proc.expect(["$", pexpect.TIMEOUT])

    def _interrupt_xmodem(self):
        """ Interrupt possible running xmodem. """
        self._log(2, "sending CAN CAN")
        self.proc.sendcontrol('x')
        self.proc.sendcontrol('x')
        self.proc.sendline('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.proc.expect(['unknown_cmd', pexpect.TIMEOUT], timeout=1)
    
    def _ruthere(self):
        """ Test to see if the device is responsive, turning on prompts if needed. """
        if self.ruthere is not None:
            return self.ruthere
        self._interrupt_xmodem()
        self.proc.sendline('')
        match = self.proc.expect(['>\r\n', pexpect.TIMEOUT], timeout=1)
        if match is 0:
            self.ruthere = True
        elif match is 1:
            self._log(2, "turning on prompt")
            self.proc.sendline('prompt')
            match2 = self.proc.expect(['>', pexpect.TIMEOUT], timeout=1)
            if match2 is 0:
                self.ruthere = True
            else:
                self.ruthere = False
        return self.ruthere
    
    def _bootmode(self):
        """ Get into boot mode. """
        self.proc.sendline('')
        match = self.proc.expect(['=>', '>'], timeout=1)
        if match == 0:
            # We're already in boot mode.
            return
        self._log(2, "sending reset")
        self.proc.sendline('reset')
        self._log(2, "waiting for message")
        self.proc.expect('Hit \^d to stop autoboot:', timeout=10)
        self._log(2, "sending ^d")
        self.proc.sendcontrol('d')
        self.proc.expect('=>')
        
    def _appmode(self):
        """ Get into app mode. """
        self.proc.sendline('')
        match = self.proc.expect(['=>', '>', pexpect.TIMEOUT], timeout=1)
        if match == 1:
            # We're already in app mode.
            self.proc.sendline('')
        else:
            self._log(2, "boot")
            self.proc.sendline('boot')

        self.proc.expect('>')
        self.proc.sendline('')
        self.proc.expect('@')
        prompt = self.proc.before.rsplit('\r\n')[-1]
        self._log(2, "prompt = "+prompt+", length = "+str(len(prompt)))
        self.proc.expect('>')
        return prompt
    
    def _sendfile(self, filename, callback=None):
        """ Send a file to the device using xmodem. """
        def getc(size, timeout=1):
            self.sport.timeout = timeout
            return self.sport.read(size)
        def putc(data, timeout=1):
            self.sport.writeTimeout = timeout
            return self.sport.write(data)

        self.previous_line = ''
        def statuscallback(total_packets, success_count, error_count):
            #global previous_line
            this_line = " %d%%  %d err\r" % (total_packets*100/file_packets, error_count)
            if this_line != self.previous_line:
                self.previous_line = this_line
                sys.stdout.write(this_line)
                sys.stdout.flush()

        self.proc.sendline('')
        self.proc.expect('=>')
        self._log(2, "xmdm")
        self.proc.sendline('xmdm')
        sleep(1.0)

        self.sport.close()
        self.sport = serial.Serial(port=self.tty, baudrate=self.baudrate, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
        modem = XMODEM(getc, putc)

        if callback:
            cb = callback
        else:
            if self.verbosity >= 1:
                cb = statuscallback
            else:
                cb = None        
        file_packets = (os.path.getsize(self.filename)-1)/128+1
        result = modem.send(open(filename, 'rb'), callback=cb)
        self._log(2, "xmodem result = " + str(result))
        self.proc = pexpect.fdpexpect.fdspawn(self.sport, logfile=self.logfile)
        
    def identifyfile(self):
        """ Attempt to determine version and productid of a firmware file. """
        return FirmwareFile(self.filename).identifyfile()
    
    def identifydevice(self):
        """ Attempt to determine version and productid of a device. """
        if not self._ruthere():
            self._log(0, 'Device does not respond: '+self.tty)
            return
        self._appmode()
        self.proc.sendline('info')
        self.proc.expect('Product ID: ')
        self.proc.expect('\r\n')
        productid = self.proc.before
        self._log(2, "device productid = "+productid)

        self.proc.expect('\tActive Expander FW Revision: ')
        self.proc.expect(' ')
        version = self.proc.before
        self._log(2, "device version   = "+version)

        return (version, productid)
    
    def find_matches_directory(self, directory):
        pass



if __name__ == "__main__":
    #tty  = '/dev/ttyUSB1'
    #filename = 'firmware/2.04/pinot_grigio_fem_sas_update_02_04.bin'
    #filename = 'firmware/Skytree_SAS_Release_02_87/skytree_fem_sas_update_02_87.bin'
    
    #tty = '/dev/ttyUSB2'
    #filename = 'firmware/Skytree_SAS_Release_02_87/bluemoon_sas_update_02.87.bin'
    
    #tty = '/dev/ttyUSB0'
    #fw = FirmwareCli(tty, filename, verbosity=2)
    #fw.update()
    
    #fw = FirmwareCli(tty, sys.argv[1], verbosity=2)
    #fw.identifyfile()
    
    #fw = FirmwareCli(sys.argv[1], None, verbosity=2)
    #fw.identifydevice()
    
    if len(sys.argv) != 3:
        print "usage:", sys.argv[0].split('/')[-1], "<tty device file> <firmware file>"
        sys.exit(-1)
    tty      = sys.argv[1]
    filename = sys.argv[2]
    
    print "program version =", version
    
    fw = FirmwareCli(tty, filename, verbosity=2)
    fid = fw.identifyfile()
    did = fw.identifydevice()
    if not did:
        sys.exit(-1)
    if fid[1] != did[1]:
        print "product IDs don't match; aborting"
        print fid[1], "!=", did[1]
        sys.exit(-1)
    fw.update()
    fw.identifydevice()

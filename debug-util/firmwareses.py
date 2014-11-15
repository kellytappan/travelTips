#!/usr/bin/env python

version = "0.0.0+"

import sys
import os

from SesPageSas import SesPageSas
from firmwarefile import FirmwareFile

class FirmwareSes:
    """
    Update firmware on one device.
    """
    
    chunksize = 4096  # Maximum number of bytes to send to device at one time.
    
    def __init__(self, devicename, expanderid, filename, verbosity=0):
        self.devicename = devicename
        self.expanderid = expanderid
        self.filename   = filename
        self.verbosity  = verbosity
        
        if os.geteuid() != 0:
            raise Exception("You must be running as root.")
        self.sp = SesPageSas(devicename)

    def set_filename(self, filename):
        self.filename = filename
    
    def update(self, callback=None):
        def mycallback(total_packets, success_count, error_count):
            if cb:
                cb(total_packets, success_count, error_count, file_packets)

        self.previous_line = ''
        def statuscallback(total_packets, success_count, error_count, file_packets):
            #global previous_line
            this_line = " %d%%  %d err\r" % (total_packets*100/file_packets, error_count)
            if this_line != self.previous_line:
                self.previous_line = this_line
                sys.stdout.write(this_line)
                sys.stdout.flush()

        if callback:
            cb = callback
        else:
            if self.verbosity >= 1:
                cb = statuscallback
            else:
                cb = None        
        file_packets = (os.path.getsize(self.filename)-1)/FirmwareSes.chunksize+1

        fwfile = open(self.filename, 'rb')
        offset = 0  # We're at the beginning of the file.
        
        microcode = fwfile.read()
        for offset in range(0, len(microcode), FirmwareSes.chunksize):
            mycallback(offset/FirmwareSes.chunksize, 0, 0)
            sesdat = self.sp.page_0e_fill({
                "mode":0x07,
                "buf_offset":offset,
                "data_len":min(FirmwareSes.chunksize, len(microcode[offset:])),
                "firmware_image_id":1,
                "sas_expander_id":self.expanderid,
                }, microcode)
            result = self.sp.writepage(sesdat)
            if result != 0:
                print "aborting; result =", result
                break
            page0e_desc = self.sp.parse(self.sp.readpage(0x0e))["data"].descriptors.val[0]
            if page0e_desc.status.val not in (0x01, 0x10):
                print "aborting; status =", page0e_desc.status.val
                break
            if page0e_desc.status.val == 0x10:
                print "done? status =", 0x10
        page0e = self.sp.parse(self.sp.readpage(0x0e))["data"]
        for descriptor in page0e.descriptors.val:
            print "Enclosure #" + str(descriptor.subid.val)
            print "    status                : %.2X - %s" % (descriptor.status.val, descriptor.status_text.val)
            print "    additional status     : %.2X" % descriptor.additional_status.val
            print "    maximum size          : %s" % format(descriptor.maxsize.val, ",d")
            print "    expected buffer id    : %.2X" % descriptor.expected_id.val
            print "    expected buffer offset: %.8X" % descriptor.expected_offset.val


    def identifyfile(self):
        """ Attempt to determine version and productid of a firmware file. """
        return FirmwareFile("").identifyfile(self.filename)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "usage:", sys.argv[0].split('/')[-1], "<sg device file> <SAS expander ID> <firmware file>"
        sys.exit(-1)
    devicename = sys.argv[1]
    expanderid = sys.argv[2]
    filename   = sys.argv[3]
    
    print "program version =", version
    
    fw = FirmwareSes(devicename, int(expanderid), filename, verbosity=2)
#     fid = fw.identifyfile()
#     did = fw.identifydevice()
#     if not did:
#         sys.exit(-1)
#     if fid[1] != did[1]:
#         print "product IDs don't match; aborting"
#         print fid[1], "!=", did[1]
#         sys.exit(-1)
    fw.update()
#     fw.identifydevice()

import os

class Discovery(object):
    """
    Discover interfaces for us to use.
    """
    
    @staticmethod
    def discover_sas():
        """
        Look through sysfs for the sg device names of enclosures.
        Only works on Linux.
        """
        devices = []
        devdir = "/dev"
        prefix = "/sys/class/enclosure"
        postfix = "device/scsi_generic"
        for enclosure in os.listdir(prefix):
            for sg in os.listdir(prefix + "/" + enclosure + "/" + postfix):
                devices.append(devdir + "/" + sg)
        return devices

    @staticmethod
    def discover_serial():
        """
        Look for serial devices we can use.
        Only works on Linux.
        """
        dev = "/dev"
        return [dev + "/" + s for s in os.listdir(dev) if "ttyUSB" in s]

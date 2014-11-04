import os
import collections

from SesPageSas import SesPageSas
from SesPageCli import SesPageCli
from CliCmdSas    import CliCmdSas
from CliCmdSerial import CliCmdSerial

class Discovery(object):
    """
    Discover interfaces for us to use.
    """

    # capabilities
    CAP_CLI         = -999
    CAP_SES         = -998  # can return full SES pages
    CAP_FAN_CONTROL = -997  # includes CAP_CLI
    CAP_SES_SHORT   = -996  # can return short SES pages (maybe long, too)

    description = \
    {
     CAP_CLI        : "cli",
     CAP_SES        : "ses, full results",
     CAP_FAN_CONTROL: "fan control",
     CAP_SES_SHORT  : "ses, short results",
     }

    capabilities = {}

    created = {}

    @staticmethod
    def discover_sas():
        """
        Look through sysfs for the sg device names of enclosures.
        Only works on Linux.

        Returns a list of device file names.
        """
        devfiles = []
        devdir = "/dev"
        prefix = "/sys/class/enclosure"
        postfix = "device/scsi_generic"
        try:
            enclosures = os.listdir(prefix)
        except:
            enclosures = []
        for enclosure in enclosures:
            for sg in os.listdir(prefix + "/" + enclosure + "/" + postfix):
                devfiles.append(devdir + "/" + sg)
        return devfiles

    @staticmethod
    def discover_serial():
        """
        Look for serial devices we can use.
        Only works on Linux.

        Returns a list of device file names.
        """
        dev = "/dev"
        return [dev + "/" + s for s in os.listdir(dev) if "ttyUSB" in s]

    @staticmethod
    def probe_cli(cli):
        """
        Probe the given CliCmd object for its capabilities.

        Returns a list of capabilities.
        """
        try:
            fanspeed = cli.execute("fan speed")
        except:
            return []
        else:
            #print "fan speed length =", len(fanspeed)
            if len(fanspeed) <= 400:
                return [Discovery.CAP_CLI]
            else:
                return [Discovery.CAP_CLI, Discovery.CAP_FAN_CONTROL]

    @staticmethod
    def probe_ses(sp):
        """
        Probe the given SesPage object for its capabilities.

        Returns a list of capabilities.
        """
#         try:
#             page_02 = sp.readpage(0x02)
#         except:
#             return []
#         else:
#             if page_02:
#                 #print "page 02 length =", len(page_02)
#                 if len(page_02) <= 424:
#                     return [Discovery.CAP_SES_SHORT]
#                 else:
#                     return [Discovery.CAP_SES_SHORT, Discovery.CAP_SES]
#             else:
#                 return []
        page_02 = sp.readpage(0x02)
        if page_02:
            return [Discovery.CAP_SES_SHORT, Discovery.CAP_SES]
        else:
            return []

    @staticmethod
    def probe():
        """
        Create Discovery.capabilities.  It is a dictionary indexed by capability.
        Value is a set of tuples:
          [0] is an arbitrary quality value, the lower the better.
          [1] is either a class or a sequence of classes used to create the access object.  If it's a sequence, the parameters are supplied to the last element, then the result is passed to the previous element, etc.
          [2] is a parameter to send to the class to construct the access object.
        """
        Discovery.capabilities = collections.defaultdict(set)
        for devfile in Discovery.discover_sas():
            for expanderid in (1,2,3,5):
                cli = CliCmdSas(devfile, expanderid)
                for capability in Discovery.probe_cli(cli):
                    #print "cli capability of", devfile, expanderid, "=", Discovery.description[capability]
                    definition = ( 1, CliCmdSas, (devfile,expanderid) )
                    Discovery.capabilities[capability].add(definition)
                cli.close()
            sp = SesPageSas(devfile)
            for capability in Discovery.probe_ses(sp):
                #print "ses capability of", devfile, "=", Discovery.description[capability]
                definition = (1, SesPageSas, devfile)
                Discovery.capabilities[capability].add(definition)
            sp.close()
        for devfile in Discovery.discover_serial():
            cli = None
            try:
                cli = CliCmdSerial(devfile)
            except:
                if cli:
                    cli.close()
                continue
            for capability in Discovery.probe_cli(cli):
                #print "cli capability of", devfile, "=", Discovery.description[capability]
                definition = (3, CliCmdSerial, devfile)
                Discovery.capabilities[capability].add(definition)
            sp = SesPageCli(cli)
            for capability in Discovery.probe_ses(sp):
                #print "ses capability of", devfile, "=", Discovery.description[capability]
                definition = ( 3, (SesPageCli,CliCmdSerial), devfile )
                Discovery.capabilities[capability].add(definition)
            sp.close()

    @staticmethod
    def create_accessor(definition):
        """
        Create an accessor object based on definition.

        definition is a sequence where the first element is a function or sequence of functions
        and the second parameter is a parameter.
        Call the function or call the list of functions starting from the end, initially passing the parameter,
        subsequently passing the result of the previous function call.

        For example, if definition is ( (SesPageCli,CliCmdSerial), "/dev/ttyUSB0" ), then return
            SesPageCli(CliCmdSerial("/dev/ttyUSB0"))
        """
        if definition in Discovery.created:
            retval = Discovery.created[definition]
            if retval:
                #print "create_accessor: returning existing accessor for", definition, ":", retval  # DEBUG
                return retval

        quality, funcs, param = definition
        try:
            funcs[0]
        except:
            funcs = (funcs,)
        for func in funcs[::-1]:
            param = func(param)
        Discovery.created[definition] = param
        #print "create_accessor: new accessor for", definition, ":", param  # DEBUG
        return param

    @staticmethod
    def close_all():
        for ad,accessor in Discovery.created.items():
            accessor.close()
            del ad
        #print "Discovery.created =", Discovery.created  # DEBUG

    @staticmethod
    def find_candidates(cap_set):
        """
        Return a set of accessor definitions that have all the specified capabilities.
        """
        retval = None
        if isinstance(cap_set, int):
            cap_set = (cap_set,)
        for cap in cap_set:
            ads = Discovery.capabilities[cap]
            if retval == None:
                retval = ads
            else:
                retval &= ads
        return retval

    @staticmethod
    def find_best(cap_set):
        """
        Return the best accessor definition that has all the specified capabilities.
        """
        ads = sorted(Discovery.find_candidates(cap_set), key=lambda ad: ad[0])
        if ads:
            return ads[0]
        else:
            return None

    @staticmethod
    def create_best(cap_set):
        """
        Return the best accessor that has all the specified capabilities.
        """
        ad = Discovery.find_best(cap_set)
        #print cap_set, ad
        if ad:
            return Discovery.create_accessor(ad)
        else:
            return None


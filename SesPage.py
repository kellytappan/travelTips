import sys
sys.path.append('../../ih/python-scsi-pt')

import abc

from Cmd import Cmd

class SesPage(object):
    """
    Read and write SES pages through various means.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        pass
    
    @abc.abstractmethod
    def readpage(self, pagenum):
        """
        Read the SES page specified by integer pagenum, returning a string.
        """
        pass
    
    @abc.abstractmethod
    def writepage(self, pagenum, data):
        """
        Write the SES page specified by integer pagenum with string, data.
        """
        pass
    
    #@staticmethod
    def parse_00(self, data):
        return tuple(ord(pc) for pc in data[4:])
    
    #@staticmethod
    def parse_01(self, data):
        configuration = \
        (
         (  0   , 1*8, "int", "pc",          "page code"),
         (  1   , 1*8, "int", "secondaries", "number of secondary subenclosures"),
         (  2   , 2*8, "int", "length",      "pagelength"),
         (  4   , 4*8, "int", "gen",         "generation code"),
         )
        enclosure_descriptor = \
        (
         (( 0,6), 3  , "int", None,      "relative enclosure services process identifier"),
         (( 0,2), 3  , "int", None,      "number of enclosure services processes"),
         (  1   , 1*8, "int", "subid",   "subenclosure identifier"),
         (  2   , 1*8, "int", "number",  "number of type descriptor headers"),
         (  3   , 1*8, "int", "length",  "enclosure descriptor length"),
         (  4   , 8*8, "int", "logid",   "enclosure logical identifier"),
         ( 12   , 8*8, "str", "vendor",  "enclosure vendor identification"),
         ( 20   ,16*8, "str", "product", "product identification"),
         ( 36   , 4*8, "str", "revision","product revision level"),
         ( 40   , 0  , "str", None,      "vendor specific enclosure information"),
         )
        type_descriptor_header = \
        (
         (  0   , 1*8, "int", "type",     "element type"),
         (  1   , 1*8, "int", "possible", "number of possible elements"),
         (  2   , 1*8, "int", "subid",    "subenclosure identifier"),
         (  3   , 1*8, "int", "desclen",  "type descriptor text length"),
         )
        # This must be lists instead of tuples so we can modify the length.
        type_descriptor_text = \
        [
         [  0   , 0*8, "str", "text", "type descriptor text"],
         ]
        bo = 0   # byte offset
        head = Cmd.extract(data[bo:], configuration, bo)
        bo += 8
        enclosures = []
        encnumtypes = []
        numenclosures = 1+Cmd.extracttodict(head)["secondaries"][0]
        for encnum in range(numenclosures):
            #print "encnum =", encnum
            enclist = Cmd.extract(data[bo:], enclosure_descriptor, bo)
            encdict = Cmd.extracttodict(enclist)
            enclosures.append(enclist)
            encnumtypes.append(encdict["number"][0])
            bo += 4+encdict["length"][0]
        for encnum in range(numenclosures):
            typeheaders = []
            for typenum in range(encnumtypes[encnum]):
                typeheaders.append(Cmd.extract(data[bo:], type_descriptor_header, bo))
                bo += 4
            enclosures[encnum].append(typeheaders)
        for encnum in range(numenclosures):
            for typenum in range(encnumtypes[encnum]):
                thislen = enclosures[encnum][-1][typenum][3][0]
                type_descriptor_text[0][1] = thislen*8  # ugly
                enclosures[encnum][-1][typenum][3] = Cmd.extract(data[bo:], type_descriptor_text, bo)[0]
                bo += thislen
        self.page01 = enclosures
        return enclosures
    
    #@staticmethod
    def parse_02(self, data):
        enclosure_status = \
        (
         (  0   , 1*8, "int", "pc"      , "page code"),
         (( 1,4), 1  , "int", "invop"   , "invop"),
         (( 1,3), 1  , "int", "info"    , "info"),
         (( 1,2), 1  , "int", "non_crit", "non-crit"),
         (( 1,1), 1  , "int", "crit"    , "crit"),
         (( 1,0), 1  , "int", "unrecov" , "unrecov"),
         (  2   , 2*8, "int", "length"  , "pagelength"),
         (  4   , 4*8, "int", "gen"     , "generation code"),
         )
        status_element = \
        (
         (( 0,6), 1  , "int", "prdfail" , "prdfail"),
         (( 0,5), 1  , "int", "disabled", "disabled"),
         (( 0,4), 1  , "int", "swap"    , "swap"),
         (( 0,3), 4  , "int", "elstat"  , "element status code"),
         (  1   , 3*8, "int", "status"  , "element type specific status information"),
         )
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], enclosure_status)
        bo += 8
        
        
        pass

    #@staticmethod
    def parse_04(self, data):
        pass
    #@staticmethod
    def parse_05(self, data):
        pass
    #@staticmethod
    def parse_07(self, data):
        pass
    #@staticmethod
    def parse_0a(self, data):
        pass
    #@staticmethod
    def parse_0e(self, data):
        pass
    
    pagedict = {
         0x00: (parse_00, "Supported Diagnostic Pages"),
         0x01: (parse_01, "Configuration"),
         0x02: (parse_02, "Enclosure"),
         0x04: (parse_04, "String"),
         0x05: (parse_05, "Threshold"),
         0x07: (parse_07, "Element Descriptor"),
         0x0a: (parse_0a, "Additional Element"),
         0x0e: (parse_0e, "Download Microcode"),
         }
    
    #@staticmethod
    def parse(self, data):
        """
        Parse the string, data, and return a structure with all the information.
        """
        pagecode = ord(data[0])
        if pagecode in SesPage.pagedict:
            return {
                    "pagecode": pagecode,
                    "pagedesc": SesPage.pagedict[pagecode][1],
                    "data"    : SesPage.pagedict[pagecode][0](self, data),
                    }
        else:
            return {
                    "pagecode": pagecode,
                    "pagedesc": "unknown",
                    "data"    : data,
                    }
    

#import sys
#sys.path.append('/home/larry/git/ih/python-scsi-pt')

import abc

from Cmd import Cmd

class SesPage(object):
    """
    Read and write SES pages through various means.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        self.page01 = None
    
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
        """
        return a ListDict of Fields, including "enclosures": list of enclosures
        an enclosure is a ListDict of Fields, including "typedesc": list of type descriptors
        a type descriptor is a ListDict of Fields, including "text": type descriptor text
        """
        configuration = \
        (
         (  0   , 1*8, "int", "pc",          "page code"),
         (  1   , 1*8, "int", "secondaries", "number of secondary subenclosures"),
         (  2   , 2*8, "int", "length",      "pagelength"),
         (  4   , 4*8, "int", "gen",         "generation code"),
         (  8   , 0  , "str", "enclosures" , "enclosure descriptor list"),
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
         (  0   , 0  , "str", "typedesc", "list of type descriptor"),  # placeholder
         )
        type_descriptor_header = \
        (
         (  0   , 1*8, "int", "type",     "element type"),
         (  1   , 1*8, "int", "possible", "number of possible elements"),
         (  2   , 1*8, "int", "subid",    "subenclosure identifier"),
         (  3   , 1*8, "int", "desclen",  "type descriptor text length"),
         (  0   , 0  , "str", "text"    , "type descriptor text"),  # placeholder
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
        enctypecounts = []   # number of types for each enclosure
        numenclosures = 1+head.secondaries.val  # total number of enclosures
        # Loop through the enclosures, retrieving headers.
        for encidx in range(numenclosures):
            # An enclosure is a ListDict of Fields.
            enclosure = Cmd.extract(data[bo:], enclosure_descriptor, bo)
            enclosures.append(enclosure)
            enctypecounts.append(enclosure.number.val)
            bo += 4+enclosure.length.val
        # Loop again through enclosures, retrieving lists of type descriptors.
        for encidx in range(numenclosures):
            typeheaders = []
            typedescbo  = bo
            for typenum in range(enctypecounts[encidx]):
                # A typeheader is a ListDict of Fields.
                # typeheaders is a list of them.
                typeheaders.append(Cmd.extract(data[bo:], type_descriptor_header, bo))
                bo += 4
            # Replace the placeholder for the list of type descriptors.
            enclosures[encidx].typedesc.val = typeheaders
            enclosures[encidx].typedesc.bo  = typedescbo
        # Loop yet again through enclosures, retrieving type descriptor texts.
        for encidx in range(numenclosures):
            for typenum in range(enctypecounts[encidx]):
                thislen = enclosures[encidx].typedesc.val[typenum].desclen.val
                type_descriptor_text[0][1] = thislen*8  # ugly, set the number of bits to extract
                # Replace the placeholder for the type descriptor text.
                enclosures[encidx].typedesc.val[typenum].text = Cmd.extract(data[bo:], type_descriptor_text, bo).text
                bo += thislen
        head.enclosures.val = enclosures
        self.page01 = head
        return head
    
    #@staticmethod
    def parse_02(self, data):
        """
        return a ListDict of Fields, including "enclosures": list of enclosures
        an enclosure is a dictionary with "subid": enclosure number and "types": list of types
        a type is a dictionary with "type": element type and "elements": list of status elements, starting with the overall status element
        a status element is a list of Fields
        """
        enclosure_status = \
        (
         (  0   , 1*8, "int", "pc"        , "page code"),
         (( 1,4), 1  , "int", "invop"     , "invop"),
         (( 1,3), 1  , "int", "info"      , "info"),
         (( 1,2), 1  , "int", "non_crit"  , "non-crit"),
         (( 1,1), 1  , "int", "crit"      , "crit"),
         (( 1,0), 1  , "int", "unrecov"   , "unrecov"),
         (  2   , 2*8, "int", "length"    , "pagelength"),
         (  4   , 4*8, "int", "gen"       , "generation code"),
         (  8   , 0  , "str", "enclosures", "enclosure descriptor list"),
         )
        status_element = \
        (
         (( 0,6), 1  , "int", "prdfail" , "prdfail"),
         (( 0,5), 1  , "int", "disabled", "disabled"),
         (( 0,4), 1  , "int", "swap"    , "swap"),
         (( 0,3), 4  , "int", "elstat"  , "element status code"),
         (  1   , 3*8, "int", "status"  , "element type specific status information"),
         )
        
        if not self.page01:
            # We need the information from SES page 0x01 before we can
            # parse page 0x02.
            return None
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], enclosure_status, bo)
        bo += 8
        
        enclosures02 = []
        for enclosure01 in self.page01.enclosures.val:
            typelist02 = []
            for typedef01 in enclosure01.typedesc.val:
                ellist02 = []
                for elnum in range(1+typedef01.possible.val):
                    ellist02.append(Cmd.extract(data[bo:], status_element, bo))
                    bo += 4
                typelist02.append({
                                   "type":typedef01.type.val,
                                   "text":typedef01.text.val,
                                   "elements":ellist02,
                                   })
            enclosures02.append(typelist02)
        head.enclosures = Cmd.Field(enclosures02, 8, "enclosures", "list of enclosures")
        #head.append(Cmd.Field(enclosures02, 8, "enclosures", "list of enclosures"), "enclosures")
        return head

    #@staticmethod
    def parse_04(self, data):
        pass

    #@staticmethod
    def parse_05(self, data):
        """
        return a ListDict of Fields, including "enclosures": list of enclosures
        an enclosure is a dictionary with "subid": enclosure number and "types": list of types
        a type is a dictionary with "type": element type and "elements": list of status elements, starting with the overall status element
        a status element is a list of Fields
        """
        threshold_in = \
        (
         (  0   , 1*8, "int", "pc"        , "page code"),
         (( 1,4), 1  , "int", "invop"     , "invalid operation requested"),
         (  2   , 2*8, "int", "length"    , "pagelength"),
         (  4   , 4*8, "int", "gen"       , "generation code"),
         (  8   , 0  , "str", "enclosures", "enclosure descriptor list"),
         )
        threshold_descriptor = \
        (
         (  0   , 1*8, "int", "hicrit", "high critical threshold"),
         (  1   , 1*8, "int", "hiwarn", "high warning threshold"),
         (  2   , 1*8, "int", "lowarn", "low warning threshold"),
         (  3   , 1*8, "int", "locrit", "low critical threshold"),
         )
        
        if not self.page01:
            # We need the information from SES page 0x01 before we can
            # parse page 0x04.
            return None
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], threshold_in, bo)
        bo += 8
        
        enclosures05 = []
        for enclosure01 in self.page01.enclosures.val:
            typelist05 = []
            for typedef01 in enclosure01.typedesc.val:
                ellist05 = []
                for elnum in range(1+typedef01.possible.val):
                    ellist05.append(Cmd.extract(data[bo:], threshold_descriptor, bo))
                    bo += 4
                typelist05.append({
                                   "type":typedef01.type.val,
                                   "text":typedef01.text.val,
                                   "elements":ellist05,
                                   })
            enclosures05.append(typelist05)
        head.enclosures = Cmd.Field(enclosures05, 8, "enclosures", "list of enclosures")
        return head

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
    

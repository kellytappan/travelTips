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
        return tuple((
                      ord(pc),
                      self.pagedict.get(ord(pc),(-1,""))[1]  # description, defaults to ""
                      ) for pc in data[4:])
    
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
        # Table 60 in ses3r06.pdf
        element_type_codes = \
        {
         0x00: "Unspecified",
         0x01: "Device Slot",
         0x02: "Power Supply",
         0x03: "Cooling",
         0x04: "Temperature Sensor",
         0x05: "Door",
         0x06: "Audible Alarm",
         0x07: "Enclosure Services Controller Electronics",
         0x08: "SCC Controller Electronics",
         0x09: "Nonvolatile Cache",
         0x0a: "Invalid Operation Reason",
         0x0b: "Uninterruptible Power Supply",
         0x0c: "Display",
         0x0d: "Key Pad Entry",
         0x0e: "Enclosure",
         0x0f: "SCSI Port/Transceiver",
         0x10: "Language",
         0x11: "Communication Port",
         0x12: "Voltage Sensor",
         0x13: "Current Sensor",
         0x14: "SCSI Target Port",
         0x15: "SCSI Initiator Port",
         0x16: "Simple Subenclosure",
         0x17: "Array Device Slot",
         0x18: "SAS Expander",
         0x19: "SAS Connector",
         }
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
                typeheader = Cmd.extract(data[bo:], type_descriptor_header, bo)
                bo += 4
                # Does the text have a default value?
                if typeheader.type.val in element_type_codes:
                    typeheader.text.val = element_type_codes[typeheader.type.val]
                # Add it to the list.
                typeheaders.append(typeheader)
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
            # parse this page.
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
            # parse this page.
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
        element_descriptor_head = \
        (
         (  0   , 1*8, "int", "pc"        , "page code"),
         (  2   , 2*8, "int", "length"    , "pagelength"),
         (  4   , 4*8, "int", "gen"       , "generation code"),
         (  8   , 0  , "str", "enclosures", "enclosure descriptor list"),
         )
        descriptor_head = \
        (
         (  0   , 2*8, "str", None    , "reserved"),
         (  2   , 2*8, "int", "length", "descriptor length"),
         )
        # This must be lists instead of tuples so we can modify the length.
        descriptor_text = \
        [
         [  0   , 0*8, "str", "text", "type descriptor text"],
         ]

        if not self.page01:
            # We need the information from SES page 0x01 before we can
            # parse this page.
            return None
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], element_descriptor_head, bo)
        bo += 8
        
        enclosures07 = []
        for enclosure01 in self.page01.enclosures.val:
            typelist07 = []
            for typedef01 in enclosure01.typedesc.val:
                ellist07 = []
                for elnum in range(1+typedef01.possible.val):
                    length = Cmd.extract(data[bo:], descriptor_head, bo).length.val
                    bo += 4
                    descriptor_text[0][1] = length*8
                    ellist07.append(Cmd.extract(data[bo:], descriptor_text, bo))
                    bo += length
                typelist07.append({
                                   "type":typedef01.type.val,
                                   "text":typedef01.text.val,
                                   "elements":ellist07,
                                   })
            enclosures07.append(typelist07)
        head.enclosures = Cmd.Field(enclosures07, 8, "enclosures", "list of enclosures")
        return head
        pass
    
    #@staticmethod
    def parse_0a(self, data):
        additional_element_head = \
        (
         (  0   , 1*8, "int", "pc"         , "page code"),
         (  2   , 2*8, "int", "length"     , "pagelength"),
         (  4   , 4*8, "int", "gen"        , "generation code"),
         (  8   , 0  , "str", "descriptors", "additional element descriptor list"),
         )
        
        descriptor_head = \
        (
         (( 0,7), 1  , "int", "invalid" , "invalid"),
         (( 0,4), 1  , "int", "eip"     , "element index present"),
         (( 0,3), 4  , "int", "protocol", "protocol identifier"),
         (  1   , 1*8, "int", "length"  , "additional element status descriptor length"),
         )
        descriptor_eip1 = \
        (
         (( 0,0), 1  , "int", "eiioe", "element index includes overall elements"),
         (  1   , 1*8, "int", "index", "element index"),
         )
        
        sas_specific_head = \
        (
         (  0   , 1*8, "int", "numphys", "number of phy descriptors"),
         (( 1,7), 2  , "int", "type"   , "descriptor type (00b)"),
         (( 1,0), 1  , "int", "notall" , "not all phys"),
        #(  2   , 0  , "str", "phydescriptors", "phy descriptor list"),
         )
        sas_specific_eip1 = \
        (
         (  1   , 1*8, "int", "slotnum", "device slot number"),
        #(  4   , 0  , "str", "phydescriptors", "phy descriptor list"),
         )
        
        phy_descriptor = \
        (
         (( 0,6), 3  , "int", "type"    , "device type"),
         (( 2,3), 1  , "int", "ssp_init", "ssp initiator port"),
         (( 2,2), 1  , "int", "stp_init", "stp initiator port"),
         (( 2,1), 1  , "int", "smp_init", "smp initiator port"),
         (( 3,7), 1  , "int", "selector", "sata port selector"),
         (( 3,3), 1  , "int", "ssp_targ", "ssp target port"),
         (( 3,2), 1  , "int", "stp_targ", "stp target port"),
         (( 3,1), 1  , "int", "smp_targ", "smp target port"),
         (( 3,0), 1  , "int", "device"  , "sata device"),
         (  4   , 8*8, "int", "attached_sas_addr", "attached sas_specific address"),
         ( 12   , 8*8, "int", "sas_addr", "sas_specific address"),
         ( 20   , 1*8, "int", "phy_id"  , "phy identifier"),
         )
        
        if not self.page01:
            # We need the information from SES page 0x01 before we can
            # parse this page.
            return None
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], additional_element_head, bo)
        bo += 8
        
        endbo = bo-4 + head.length.val
        descriptors = []
        while bo < endbo:
            # Retrieve a descriptor header.
            dhead = Cmd.extract(data[bo:], descriptor_head, bo)
            bo += 2
            if dhead.eip.val:
                dhead += Cmd.extract(data[bo:], descriptor_eip1, bo)
                bo += 2
                index_remaining = dhead.index.val
                foundit = False
                for enclosure in self.page01.enclosures.val:
                    for typedef in enclosure.typedesc.val:
                        if index_remaining > typedef.possible.val + dhead.eiioe.val:
                            index_remaining -= typedef.possible.val + dhead.eiioe.val
                        else:
                            foundit = True
                            break
                    if foundit:
                        break
                dhead.index.val = (enclosure.subid.val, typedef.type.val, index_remaining-dhead.eiioe.val)
            
            if dhead.protocol.val != 0x06:
                return None  # Only SAS protocol is supported.
            
            sas_specific = Cmd.extract(data[bo:], sas_specific_head, bo)
            bo += 2
            if dhead.eip.val:
                sas_specific += Cmd.extract(data[bo:], sas_specific_eip1, bo)
                bo += 2
    
            phylist = []
            phybo = bo
            for phynum in range(sas_specific.numphys.val):
                phylist.append(Cmd.extract(data[bo:], phy_descriptor, bo))
                bo += 28
            sas_specific.append(Cmd.Field(phylist, phybo, "phydescriptors", "phy descriptor list"), "phydescriptors")
            descriptor = dhead + sas_specific
            descriptors.append(descriptor)

        head.descriptors.val = descriptors
        return head

    
    #@staticmethod
    def parse_0e(self, data):
        download_microcode_head = \
        (
         (  0   , 1*8, "int", "pc"         , "page code"),
         (  1   , 1*8, "int", "secondaries", "number of secondary subenclosures"),
         (  2   , 2*8, "int", "length"     , "pagelength"),
         (  4   , 4*8, "int", "gen"        , "generation code"),
         (  8   , 0  , "str", "descriptors", "additional element descriptor list"),
         )
        descriptor_format = \
        (
         (  1   , 1*8, "int", "subid"            , "subenclosure identifier"),
         (  2   , 1*8, "int", "status"           , "subenclosure download microcode status"),
         (  3   , 1*8, "int", "additional_status", "subenclosure download microcode additional status"),
         (  4   , 4*8, "int", "maxsize"          , "subenclosure download microcode maximum size"),
         ( 11   , 1*8, "int", "expected_id"      , "subenclosure download microcode exected buffer id"),
         ( 12   , 4*8, "int", "expected_offset"  , "subenclosure download microcode expected buffer offset"),
         )
        status_text = \
        { # ses3r06.pdf table 52
         # Codes indicating interim status
         0x00: "No download microcode operation in progress.",
         0x01: "Download microcode operation in progress. The enclosure services process has received one or more Download Microcode Control diagnostic pages and is awaiting additional microcode data.",
         0x02: "Download microcode operation data transfer complete, currently updating non-volatile storage",
         0x03: "The enclosure services process is currently updating non-volatile storage with deferred microcode",
         # Codes indicating completion with no errors
         0x10: "Download microcode operation complete with no error. The enclosure services process begins using the new microcode after returning this status.",
         0x11: "Download microcode operation complete with no error. The enclosure services process (e.g., a standalone enclosure services process) begins using the new microcode after the next hard reset or power on.",
         0x12: "Download microcode operation complete with no error. The enclosure services process (e.g., an attached enclosure services process) begins using the new microcode after the next power on.",
         0x13: "Download microcode operation complete with no error. The enclosure services process (e.g., an attached enclosure services process) begins using the new microcode after: a) processing a Download Microcode Control diagnostic page specifying the active deferred microcode mode; b) hard reset; or c) power on.",
         # Codes indicating completion with errors
         0x80: "Error in one or more of the Download Microcode Control diagnostic page fields, new microcode discarded. The SUBENCLOSURE DOWNLOAD MICROCODE ADDITIONAL STATUS field shall be set to the offset of the lowest byte of the field in the Download Microcode Control diagnostic page that is in error.",
         0x81: "Microcode image error (e.g., a problem detected from a vendor specific check of the microcode image such as a checksum), new microcode discarded",
         0x82: "Download microcode timeout, new microcode discarded. The enclosure services process may discard microcode data after a vendor specific amount of time if it does not receive the entire microcode image.",
         0x83: "Internal error in the download microcode operation; new microcode image is needed before a hard reset or power on (e.g., a flash ROM write failed and no backup ROM image is available).",
         0x84: "Internal error in the download microcode operation; hard reset and power on safe (e.g., the enclosure services process will use a backup ROM image on hard reset or power on).",
         0x85: "Processed a Download Microcode Control diagnostic page with the DOWNLOAD MICROCODE MODE field set to 0Fh (i.e., activate deferred microcode) when there is no deferred microcode.",
         }

        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], download_microcode_head, bo)
        bo += 8
        
        descriptors = []
        for encidx in range(1+head.secondaries.val):
            descriptor = Cmd.extract(data[bo:], descriptor_format, bo)
            bo += 16
            descriptor.append(Cmd.Field(status_text[descriptor.status.val], -1, "status_text", "status meaning"), "status_text")
            descriptors.append(descriptor)
            
        head.descriptors.val = descriptors
        return head
    
    
    def parse_80(self, data):
        eventlogin_head = \
        (
         (  0   , 1*8, "int", "pc"         , "page code"),
         (  2   , 2*8, "int", "length"     , "pagelength"),
         (( 5,1), 1  , "int", "notavail"   , "buffer not available"),
         (( 5,0), 1  , "int", "stop"       , "stop"),
         (  6   , 0  , "str", "log"        , "log data"),
         )
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], eventlogin_head, bo)
        bo += 6
        
        head.log.val = data[bo:]
        return head
    
    def parse_ex(self, data, exandernum):
        report_phy_status_head = \
        (
         (  0   , 1*8, "int", "pc"         , "page code"),
         (  2   , 2*8, "int", "length"     , "pagelength"),
         )
        
        pass
    
    def parse_e0(self, data): self.parse_ex(data, 0)
    def parse_e1(self, data): self.parse_ex(data, 1)
    def parse_e2(self, data): self.parse_ex(data, 2)
    def parse_e3(self, data): self.parse_ex(data, 3)
    def parse_e4(self, data): self.parse_ex(data, 4)
    def parse_e5(self, data): self.parse_ex(data, 5)
    
    def parse_e8(self, data):
        clicommandin_head = \
        (
         (  0   , 1*8, "int", "pc"         , "page code"),
         (  2   , 2*8, "int", "length"     , "pagelength"),
         (  4   , 1*8, "int", "expanderid" , "expander id"),
         (  5   , 0  , "str", "response"   , "cli response"),
         )
        
        bo = 0  # byte offset
        head = Cmd.extract(data[bo:], clicommandin_head, bo)
        bo += 5
        
        head.response.val = data[bo:]
        return head
    
    pagedict = {
         0x00: (parse_00, "Supported Diagnostic Pages"   ),
         0x01: (parse_01, "Configuration"                ),
         0x02: (parse_02, "Enclosure"                    ),
         0x04: (parse_04, "String"                       ),
         0x05: (parse_05, "Threshold"                    ),
         0x07: (parse_07, "Element Descriptor"           ),
         0x0a: (parse_0a, "Additional Element"           ),
         0x0e: (parse_0e, "Download Microcode"           ),
         0x80: (parse_80, "Event Log"                    ), # SK and PG
         0x82: (None    , "SXP Firmware Status"          ), # PG only
         0x91: (None    , "SXP Boot Configuration Status"), # BM only
         0x92: (None    , "Low Power Condition Status"   ), # BM only
         0xe0: (parse_e0, "Report PHY Status"            ), # ST only
         0xe1: (parse_e1, "Report PHY Status"            ), # ST only
         0xe2: (parse_e2, "Report PHY Status"            ), # ST only
         0xe3: (parse_e3, "Report PHY Status"            ), # ST only
         0xe4: (parse_e4, "Report PHY Status"            ), # ST only
         0xe5: (parse_e5, "Report PHY Status"            ), # ST only
         0xe8: (parse_e8, "CLI Command"                  ), # ST only
         0xe9: (None    , "Product Type Flag Status"     ),
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
    

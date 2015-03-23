#!/usr/bin/env python

import sys
import argparse

from firmwarewc   import FirmwareFem, FirmwareBmc, FirmwareBios, FirmwareU199, FirmwareU187, FirmwareU112
from firmwarefile import FirmwareTypes, FirmwareFile

type_bmc  = "bmc"
type_bios = "bios"
type_u112 = "u112"
type_u187 = "u187"
type_u199 = "u199"
type_fem  = "fem"
type_boot = "boot"
type_bb   = "bb"
type_mi   = "mi"
type_ssm  = "ssm"
type_list = (
    type_bmc,
    type_bios,
    type_u112,
    type_u187,
    type_u199,
    type_fem,
    type_boot,
    type_bb,
    type_mi,
    type_ssm,
    )
fw_type = {
    type_bmc : FirmwareTypes.BMC ,
    type_bios: FirmwareTypes.BIOS,
    type_u112: FirmwareTypes.U112,
    type_u187: FirmwareTypes.U187,
    type_u199: FirmwareTypes.U199,
    type_fem : FirmwareTypes.APP ,
    type_boot: FirmwareTypes.BOOT,
    type_bb  : FirmwareTypes.BB  ,
    type_mi  : FirmwareTypes.MI  ,
    type_ssm : FirmwareTypes.SSM ,
    }

def print_expander_version(label, vers):
    if FirmwareTypes.APP  in vers: print label, "app :", vers[FirmwareTypes.APP ]
    if FirmwareTypes.BOOT in vers: print label, "boot:", vers[FirmwareTypes.BOOT]
    if FirmwareTypes.BB   in vers: print label, "bb  :", vers[FirmwareTypes.BB  ]
    if FirmwareTypes.MI   in vers: print label, "mi  :", vers[FirmwareTypes.MI  ]
    if FirmwareTypes.SSM  in vers: print label, "ssm :", vers[FirmwareTypes.SSM ]

##### main
parser = argparse.ArgumentParser(description="Jabil Firmware Update, Wolf Creek")
#parser.add_argument("--version" , nargs=1, type=str,   help="desired version number")
#parser.add_argument("--force"   , action="store_true", help="program even if up to date")
parser.add_argument("--type"    , nargs=1, type=str,   required=True , help='type of thing to update, or "help", "all", or "avail"')
parser.add_argument("--firmware", nargs=1, type=str,   required=True , help="firmware file, directory, or 7z")
parser.add_argument("--instance", nargs=1, type=int,   required=False, help="instance 0 or 1 for FEM or CPLD")
parser.add_argument("--serial"  , nargs=1, type=str,   required=False, help="serial port device file for FEM or CPLD")
# Need to know
#   type of thing to program: all, bmc, bios, plx (u112, u187, u199), fem, cpld (baseboard, midplane, status)
#   firmware file
#   operation?  update, info, dryrun
#   if SAS expander or SAS CPLD, then need serial port and can't run from compute node
#   version number, if more than one firmware file for type
params, commands = parser.parse_known_args()
params = vars(params)

#force = params["force"]
fw_file = FirmwareFile(params["firmware"][0])
typ = params["type"][0]

if typ == "help" or typ not in type_list:
    print 'Please choose a parameter to the "--type" switch from the following:'
    for t in ["help", "all", "avail"] + list(type_list):
        print "  "+t
    sys.exit(2)

type_all = [
    type_bmc,
    type_bios,
    type_u112,
    type_u187,
    type_u199,
    (type_fem ,0), (type_fem ,1),
    (type_boot,0), (type_boot,1),
    type_bb,
    (type_mi  ,0), (type_mi  ,1),
    type_ssm,
    ]
type_do  = [typ]
type_try = []

if typ == "all":
    type_do  = type_all
    type_try = []

if typ == "avail":
    type_do  = []
    type_try = type_all

#TODO check file type

if   typ == type_bmc : fw = FirmwareBmc ()
elif typ == type_bios: fw = FirmwareBios()
elif typ == type_u112: fw = FirmwareU112()
elif typ == type_u187: fw = FirmwareU187()
elif typ == type_u199: fw = FirmwareU199()
elif typ in (type_fem, type_boot, type_bb, type_mi, type_ssm):
    if not params["serial"]:
        print 'error: argument --serial is required when --type='+typ
        sys.exit(2)
    if not params["instance"]:
        print 'error: argument --instance is required when --type='+typ
        sys.exit(2)
    fw = FirmwareFem(params["serial"][0], params["firmware"][0], params["instance"][0], verbosity=2)
    #print_expander_version("Current", fw.identifydevice())
    #fw.update()
    #print_expander_version("New    ", fw.identifydevice())
    #sys.exit(0)
else:
    pass  #TODO

print "Current version:", fw.version()
#fw.update(params["firmware"][0])
print "New version:    ", fw.version()

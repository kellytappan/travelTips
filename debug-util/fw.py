#!/usr/bin/env python

version = "0.1.0"

import sys
import curses.wrapper
import Queue
import threading
from time import sleep
import argparse

from firmwarecli  import FirmwareCli
from firmwarefile import FirmwareFile
from discovery    import Discovery

verbosity = 0

display_que = Queue.Queue()
main_que    = Queue.Queue()

POLL_DELAY = 2  # seconds

CMD_SET          = 'set'
CMD_MESSAGE      = 'message'
CMD_STOP         = 'stop'

CMD_DISCONNECTED = 'disconnected'
CMD_CONNECTED    = 'connected'
CMD_PROGRESS     = 'in progress'
CMD_PASS         = 'pass'
CMD_FAIL         = 'fail'
CMD_NOFW         = 'no firmware'

PLUG_BAD      = 1
PLUG_PROGRESS = 2
PLUG_GOOD     = 3
PLUG_GED_OFFSET = 3

STATUS_GOOD     = 'good'         # We know this canister has the right stuff.
STATUS_FAIL     = 'fail'         # We tried and failed to update this canister.
STATUS_PROGRESS = 'in progress'  # Currently programming
STATUS_UNKNOWN  = 'unknown'      # We don't know the status of this canister.
STATUS_NOFW     = 'no fw'        # We don't have firmware for this productid.

def display(scr):
    curses.curs_set(0)
    curses.cbreak()
    
    cans = {}

    modw = 36  # module width
    modh =  6  # module height
    iomw = modw+2  # IOM width
    psh  = 3   # power supply module height
    middle = 39  # center of the picture

    top    =  0
    cans['A'  ] = {'win':curses.newwin(modh, iomw, top, middle-iomw)}
    cans['B'  ] = {'win':curses.newwin(modh, iomw, top, middle+1   )}
    top += modh
    cans['PS0'] = {'win':curses.newwin(psh , modw, top, middle-modw)}
    cans['PS1'] = {'win':curses.newwin(psh , modw, top, middle+1   )}
    top += psh
    cans['PS2'] = {'win':curses.newwin(psh , modw, top, middle-modw)}
    cans['PS3'] = {'win':curses.newwin(psh , modw, top, middle+1   )}
    top += psh
#     cans['Ax' ] = {'win':curses.newwin(modh, modw, top, middle-modw)}
#     cans['Bx' ] = {'win':curses.newwin(modh, modw, top, middle+1   )}
    cans['A0' ] = {'win':curses.newwin(modh, modw/2, top, middle-modw)}
    cans['A1' ] = {'win':curses.newwin(modh, modw/2, top, middle-modw/2)}
    cans['B0' ] = {'win':curses.newwin(modh, modw/2, top, middle+1   )}
    cans['B1' ] = {'win':curses.newwin(modh, modw/2, top, middle+1+modw/2)}
    top += modh
    
    cans['A' ]['plugpos'] = cans['B' ]['plugpos'] = (1,23)
    cans['A0']['plugpos'] = cans['B0']['plugpos'] = (4,modw/2-4)
    cans['A1']['plugpos'] = cans['B1']['plugpos'] = (4,1)
    cans['A' ]['verpos'] = (1,1+iomw-modw)
    cans['B' ]['verpos'] = (1,1)
    cans['A0']['verpos'] = cans['B0']['verpos'] = (1,1)
    cans['A1']['verpos'] = cans['B1']['verpos'] = (1,1)

    curses.init_pair(PLUG_BAD                     , curses.COLOR_RED   , curses.COLOR_BLACK )
    curses.init_pair(PLUG_PROGRESS                , curses.COLOR_YELLOW, curses.COLOR_BLACK )
    curses.init_pair(PLUG_GOOD                    , curses.COLOR_GREEN , curses.COLOR_BLACK )
    curses.init_pair(PLUG_BAD     +PLUG_GED_OFFSET, curses.COLOR_BLACK , curses.COLOR_RED   )
    curses.init_pair(PLUG_PROGRESS+PLUG_GED_OFFSET, curses.COLOR_BLACK , curses.COLOR_YELLOW)
    curses.init_pair(PLUG_GOOD    +PLUG_GED_OFFSET, curses.COLOR_BLACK , curses.COLOR_GREEN )
    curses.init_pair(7                            , curses.COLOR_GREEN , curses.COLOR_BLACK )

    for can in cans.values():
        can['version'] = "unknown"
        can['status' ] = "unknown"
        can['tty'    ] = "       "
        can['plug'   ] = PLUG_BAD
    messages = ()
    bottom = top

    while True:
        scr.erase()
        top = bottom
        for msg in messages:
            scr.addstr(top, 0, msg, curses.color_pair(7))
            top += 1
        scr.noutrefresh()
        
        for can in cans.values():
            can['win'].erase()
            can['win'].border()
            for y in range(1,modh-1):
                for name in ('A0','B0'):
                    cans[name]['win'].addstr(y, modw/2-1, " ")
                for name in ('A1','B1'):
                    cans[name]['win'].addstr(y, 0, " ")
            if 'plugpos' in can:
                plug = can['plugpos']
                can['win'].addstr(plug[0], plug[1], " o ", curses.color_pair(can['plug']))
            if 'verpos' in can:
                verpos = can['verpos']
                can['win'].addstr(verpos[0]+0, verpos[1], "version: "+can['version'])
                can['win'].addstr(verpos[0]+1, verpos[1], "status: " +can['status' ])
                can['win'].addstr(verpos[0]+2, verpos[1], "tty: "    +can['tty'    ])
            can['win'].noutrefresh()
        for name in ('A','B','A0','B0'):
            y,x = cans[name]['plugpos']
            cans[name]['win'].addstr(y,x-len(name),name)
            cans[name]['win'].noutrefresh()
        for name in ('A1','B1'):
            y,x = cans[name]['plugpos']
            cans[name]['win'].addstr(y,x+3,name)
            cans[name]['win'].noutrefresh()
        for name in ('PS0','PS1','PS2','PS3'):
            cans[name]['win'].addstr(1,1,"Power Supply")
            cans[name]['win'].noutrefresh()
    
        curses.doupdate()
#         while True:
#             try:
#                 op = display_que.get(True, 1.0)
#             except Queue.Empty:
#                 op = None
#             if scr.getch() == curses.KEY_BREAK:
#                 return
#             if op:
#                 break
        op = display_que.get()
        if   op[0] == CMD_SET:
            opcode, canister_name, element_name, new_value = op
            cans[canister_name][element_name] = new_value
            del opcode, canister_name, element_name, new_value
        elif op[0] == CMD_MESSAGE:
            opcode, new_messages = op
            messages = new_messages
            del opcode, new_messages
        elif op[0] == CMD_STOP:
            # op = (CMD_STOP)
            opcode, = op
            del opcode
            return

def watch_port(port):
    
    def update_callback(total_packets, success_count, error_count, file_packets):
        if "prev_line" not in update_callback.__dict__:
            prev_line = None
        new_line = str(total_packets*100/file_packets)+"%"
        if prev_line != new_line:
            display_que.put((CMD_SET, prompt, 'status', new_line))
            prev_line = new_line
    
    fw_cli = FirmwareCli(port, None, verbosity)
    while cansleft:
        prompt = fw_cli.get_prompt()
        if prompt:
            # We're plugged into something.
            main_que.put((CMD_CONNECTED,port,prompt))
            if status[prompt] == STATUS_UNKNOWN:
                # This canister is not known to have the right firmware.
                dev_vers, dev_prod = fw_cli.identifydevice()
                if prompt not in versions:
                    # We haven't displayed this version yet.
                    versions[prompt] = dev_vers
                    display_que.put((CMD_SET, prompt, 'version', dev_vers))
                if force or dev_vers != requested_version:
                    # Do the update, if we can.
                    f = fw_file.get_filename(dev_prod, requested_version)
                    if f:
                        main_que.put((CMD_PROGRESS, port, prompt))
                        display_que.put((CMD_SET, prompt, 'status', 'starting'))
                        fw_cli.set_filename(f)
                        fw_cli.update(update_callback)
                        dev_vers, dev_prod = fw_cli.identifydevice()
                        versions[prompt] = dev_vers
                        display_que.put((CMD_SET, prompt, 'version', dev_vers))
                    else:
                        main_que.put((CMD_NOFW, port, prompt))
                        status[prompt] = STATUS_NOFW
                if status[prompt] != STATUS_NOFW:
                    if dev_vers == requested_version:
                        display_que.put((CMD_SET, prompt, 'status', 'good'))
                        main_que.put((CMD_PASS, port, prompt))
                    else:
                        display_que.put((CMD_SET, prompt, 'status', 'fail'))
                        main_que.put((CMD_FAIL, port, prompt))
            else:
                sleep(POLL_DELAY)
        else:
            main_que.put((CMD_DISCONNECTED,port))
            sleep(POLL_DELAY)

def get_color(prompt):
    stat = status[prompt] if prompt in status else STATUS_UNKNOWN
    plugged = PLUG_GED_OFFSET if prompt in connections.values() else 0
    if stat is STATUS_GOOD    : return plugged+PLUG_GOOD
    if stat is STATUS_FAIL    : return plugged+PLUG_BAD
    if stat is STATUS_NOFW    : return plugged+PLUG_BAD
    if stat is STATUS_UNKNOWN : return plugged+PLUG_BAD
    if stat is STATUS_PROGRESS: return plugged+PLUG_PROGRESS
    return plugged+PLUG_BAD


##### main
parser = argparse.ArgumentParser(description="Jabil Firmware Update, Serial, TUI")
parser.add_argument("--firmware", nargs=1, type=str,   required=True, help="firmware file, directory, or 7z")
parser.add_argument("--version" , nargs=1, type=str,   help="desired version number")
parser.add_argument("--force"   , action="store_true", help="program even if up to date")
params, commands = parser.parse_known_args()
params = vars(params)

force = params["force"]
fw_file = FirmwareFile(params["firmware"][0])

# Find appropriate version.
possible = fw_file.get_versions()
if params["version"]:
    # A version was requested on the command line.
    if params["version"][0] in possible:
        # The requested version is available. WIN
        requested_version = params["version"][0]
    else:
        # The requested version is not available. Abort.
        print "Requested version,", params["version"][0]+", does not exist in specified firmware path,", params["firmware"][0]
        print "Possibilities are:", " ".join(possible)
        sys.exit(-1)
else:
    # No version was requested on the command line.
    if len(possible) is 0:
        print "No firmware versions found in specified firmware path:", params["firmware"][0]
        sys.exit(-1)
    elif len(possible) is not 1:
        print "You must request a particular version with this firmware path:", params["firmware"][0]
        print "Possibilities are:", " ".join(possible)
        sys.exit(-1)
    else:
        # Exactly one version is available. WIN
        requested_version = possible[0]
        
connections = {}  # port:prompt
versions    = {}  # prompt:version
cansleft = set(('A','B','A0','A1','B0','B1'))
# For each canister type, what firmware files does it need?
firmleft = {}
for prompt in cansleft:
    firmleft[prompt] = {}
    for typ in FirmwareType.affect[prompt]:
        files = fw_file.get_filename(prompt, typ)
        if len(files) > 1:
            # Too many versions of this type of file.
            pass  #TODO
        elif len(files) == 0:
            # No firmware files for this type.
            pass  #TODO
        else:
            firmleft[prompt][typ] = files[0]
status = {prompt:STATUS_UNKNOWN for prompt in cansleft}  # prompt:status

# Status transitions:
# status starts as unknown
# unknown:
#   discover by serial port
#   if version out of date or force
#     if we can find firmware
#       status = progress
#       update, displaying percentage as status
#       if version is now correct
#         status = good
#       else
#         status = fail
#     else
#       status = nofw
#   else
#     status = good
# good:
#   no transitions
# nofw:
#   no transitions
# fail:
#   when serial port disconnects, status = unknown


display_thr = threading.Thread(
    name='display',
    target=curses.wrapper,
    args=(display,),
    )
#display_thr.daemon = True
display_thr.start()

try:
    ports = Discovery.discover_serial()
    if not ports:
        print "Cannot discover any serial ports. Aborting."
        sys.exit(-2)
    port_threads = set()
    for port in ports:
        thr = threading.Thread(
            name=port,
            target=watch_port,
            args=(port,))
        port_threads.add(thr)
        thr.start()
    while cansleft:
        try:
            # Must have a timeout to make it interruptible.
            op = main_que.get(True, 10000)
        except Queue.Empty:
            continue
        if   op[0] == CMD_DISCONNECTED:
            opcode, port = op
            if port in connections:
                prompt_prev = connections[port]
                del connections[port]
                display_que.put((CMD_SET, prompt_prev, 'plug', get_color(prompt_prev)))
                display_que.put((CMD_SET, prompt_prev, 'tty', ''))
                if  status[prompt_prev] == STATUS_FAIL:
                    # Try again at next connection.
                    status[prompt_prev] =  STATUS_UNKNOWN
                del prompt_prev
            del opcode, port
        elif op[0] == CMD_CONNECTED:
            opcode, port, prompt = op
            if port in connections:
                prompt_prev = connections[port]
                del connections[port]
                display_que.put((CMD_SET, prompt_prev, 'plug', get_color(prompt_prev)))
                display_que.put((CMD_SET, prompt_prev, 'tty', ''))
                del prompt_prev
            if port not in connections or connections[port] != prompt:
                connections[port] = prompt
                display_que.put((CMD_SET, prompt, 'plug', get_color(prompt)))
                display_que.put((CMD_SET, prompt, 'tty', port.split('/')[-1]))
            del opcode, port, prompt
        elif op[0] == CMD_PROGRESS:
            opcode, port, prompt = op
            status[prompt] = STATUS_PROGRESS
            display_que.put((CMD_SET, prompt, 'plug', get_color(prompt)))
            del opcode, port, prompt
        elif op[0] == CMD_PASS:
            opcode, port, prompt = op
            status[prompt] = STATUS_GOOD
            display_que.put((CMD_SET, prompt, 'plug', get_color(prompt)))
            cansleft.remove(prompt)
            del opcode, port, prompt
        elif op[0] == CMD_FAIL:
            opcode, port, prompt = op
            status[prompt] = STATUS_FAIL
            display_que.put((CMD_SET, prompt, 'plug', get_color(prompt)))
            del opcode, port, prompt
        elif op[0] == CMD_NOFW:
            opcode, port, prompt = op
            status[prompt] = STATUS_NOFW
            display_que.put((CMD_SET, prompt, 'plug', get_color(prompt)))
            display_que.put((CMD_SET, prompt, 'status', 'no FW'))
            del opcode, port, prompt
        
        messages = []
        unknowns = sorted(list(cansleft-set(connections.values())))
        if unknowns:
            messages.append("Canisters yet to be checked: "+(", ".join(unknowns)))
        good_connected = sorted([x for x in connections.values() if status[x] in (STATUS_GOOD, STATUS_NOFW)])
        if unknowns and good_connected:
            messages.append("Please move cable from "+(", ".join(good_connected))+" to "+(", ".join(unknowns)))
        if not connections:
            messages.append("Please plug serial cables into enclosure.")
        display_que.put((CMD_MESSAGE, messages))

except KeyboardInterrupt:
    pass

display_que.put((CMD_STOP,))
display_thr.join()

print "Waiting for threads to terminate."
if cansleft:
    print "The following canisters have not been updated:"
    print " ".join(sorted(list(cansleft)))
    cansleft = ()
else:
    print "All canisters are at version", requested_version+"."
for thr in port_threads:
    thr.join()

del fw_file


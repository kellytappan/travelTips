#!/usr/bin/env python

version = "0.0.0+"

import sys
import curses.wrapper
import Queue
import threading
from time import sleep

from firmwarecli import FirmwareCli
from discovery   import Discovery

verbosity = 0

display_que = Queue.Queue()
main_que    = Queue.Queue()

POLL_DELAY = 5  # seconds
CMD_SET          = 'set'
CMD_MESSAGE      = 'message'
CMD_STOP         = 'stop'
CMD_DISCONNECTED = 'disconnected'
CMD_CONNECTED    = 'connected'

def display(scr):
    curses.curs_set(0)
    curses.cbreak()
    
    cans = {}

    modw = 36
    modh =  6
    iomw = modw+2
    psh  = 3
    middle = 39
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

    curses.init_pair(1, curses.COLOR_BLACK , curses.COLOR_RED   )
    curses.init_pair(2, curses.COLOR_BLACK , curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_BLACK , curses.COLOR_GREEN )
    curses.init_pair(4, curses.COLOR_RED   , curses.COLOR_BLACK )
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK )
    curses.init_pair(6, curses.COLOR_GREEN , curses.COLOR_BLACK )
    curses.init_pair(7, curses.COLOR_GREEN , curses.COLOR_BLACK )

    for can in cans.values():
        can['version'] = "unknown"
        can['status' ] = "unknown"
        can['tty'    ] = "       "
        can['plug'   ] = 4
    messages = ()
    bottom = top

    while True:
        scr.erase()
        top = bottom
        for msg in messages:
            scr.addstr(top, 0, msg, curses.color_pair(7))
            top += 1
        scr.noutrefresh()
        
        for name in ('PS0','PS1','PS2','PS3'):
            cans[name]['win'].addstr(1,1,"Power Supply")
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
            # (CMD_SET, canister name, element name, new value)
            cans[op[1]][op[2]] = op[3]
        elif op[0] == CMD_MESSAGE:
            # (CMD_MSG, message)
            messages = op[1]
        elif op[0] == CMD_STOP:
            # (CMD_STOP)
            return
        #curses.napms(1000)

def watch_port(port):
    fw = FirmwareCli(port, None, verbosity)
    while cansleft:
        #print port, cansleft, "\r"
        prompt = fw.get_prompt()
        if prompt:
            main_que.put((CMD_CONNECTED,port,prompt))
            if prompt in cansleft:
                dev_vers, dev_prod = fw.identifydevice()
                # TODO
                pass
            else:
                sleep(POLL_DELAY)
        else:
            main_que.put((CMD_DISCONNECTED,port))
            sleep(POLL_DELAY)


connections = {}

display_thr = threading.Thread(
    name='display',
    target=curses.wrapper,
    args=(display,),
    )
#display_thr.daemon = True
display_thr.start()

try:
    if False:
        sleep(1)
        display_que.put((CMD_SET,'A' ,'plug', 2))
        sleep(1)
        display_que.put((CMD_SET,'B1','plug', 3))
        sleep(1)
        display_que.put((CMD_SET,'B0','plug', 1))
        sleep(1)
        display_que.put((CMD_MESSAGE,("Please plug in serial cables.",)))
        sleep(1)
        display_que.put((CMD_SET, 'A0', 'version', '0278'))
        sleep(1)
        display_que.put((CMD_STOP,))
        sleep(1)
    ports = Discovery.discover_serial()
    if not ports:
        print "Cannot discover any serial ports. Aborting."
        sys.exit(-2)
    cansleft = set(('A','B','A0','A1','B0','B1'))
    port_threads = set()
    for port in ports:
        thr = threading.Thread(
            name=port,
            target=watch_port,
            args=(port,))
        port_threads.add(thr)
        thr.start()
    # TODO
    while cansleft:
        #print "waiting for main_que"
        try:
            # Must have a timeout to make it interruptible.
            op = main_que.get(True, 10000)
        except Queue.Empty:
            continue
        if   op[0] == CMD_DISCONNECTED:
            # (CMD_DISCONNECTED, port)
            #print "CMD_DISCONNECTED", op[1], "\r"
            if op[1] in connections:
                display_que.put((CMD_SET, connections[op[1]], 'plug', 4))
                del connections[op[1]]
            pass
        elif op[0] == CMD_CONNECTED:
            # (CMD_CONNECTED, port, prompt)
            #print "CMD_CONNECTED", op[1], op[2], "\r"
            if op[1] in connections:
                display_que.put((CMD_SET, connections[op[1]], 'plug', 4))
                del connections[op[1]]
            display_que.put((CMD_SET, op[2], 'plug', 1))
            #print CMD_SET, op[2], 'plug', 1, "\r"
            connections[op[1]] = op[2]
            pass

except KeyboardInterrupt:
    pass

display_que.put((CMD_STOP,))
display_thr.join()
    
if cansleft:
    print "The following canisters have not been programmed:"
    print " ".join(sorted(list(cansleft)))
    cansleft = ()
for thr in port_threads:
    thr.join()


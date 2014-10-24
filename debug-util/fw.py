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
    cans['Ax' ] = {'win':curses.newwin(modh, modw, top, middle-modw)}
    cans['Bx' ] = {'win':curses.newwin(modh, modw, top, middle+1   )}
    top += modh
    
    cans['A' ]['plugpos'] = cans['B' ]['plugpos'] = ((1,23),)
    cans['Ax']['plugpos'] = cans['Bx']['plugpos'] = ((4,modw/2-4),(4,modw/2))
    cans['A' ]['verpos'] = ((1,1+iomw-modw),)
    cans['B' ]['verpos'] = ((1,1),)
    cans['Ax']['verpos'] = cans['Bx']['verpos'] = ((1,1),(1,modw/2))

    curses.init_pair(1, curses.COLOR_BLACK , curses.COLOR_RED   )
    curses.init_pair(2, curses.COLOR_BLACK , curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_BLACK , curses.COLOR_GREEN )
    curses.init_pair(4, curses.COLOR_RED   , curses.COLOR_BLACK )
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK )
    curses.init_pair(6, curses.COLOR_GREEN , curses.COLOR_BLACK )
    curses.init_pair(7, curses.COLOR_GREEN , curses.COLOR_BLACK )

    for can in cans.values():
        can['version'] = ["unknown"]*2
        can['status' ] = ["unknown"]*2
        can['tty'    ] = ["       "]*2
        can['plug'   ] = [4        ]*2
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
            if 'plugpos' in can:
                for plugnum in range(len(can['plugpos'])):
                    plug = can['plugpos'][plugnum]
                    can['win'].addstr(plug[0], plug[1], " o ", curses.color_pair(can['plug'][plugnum]))
            if 'verpos' in can:
                for vernum in range(len(can['verpos'])):
                    verpos = can['verpos'][vernum]
                    can['win'].addstr(verpos[0]+0, verpos[1], "version: "+can['version'][vernum])
                    can['win'].addstr(verpos[0]+1, verpos[1], "status: " +can['status' ][vernum])
                    can['win'].addstr(verpos[0]+2, verpos[1], "tty: "    +can['tty'    ][vernum])
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
            cans[op[1]][op[2]][op[3]] = op[4]
        elif op[0] == CMD_MESSAGE:
            messages = op[1]
        elif op[0] == CMD_STOP:
            return
        #curses.napms(1000)

def watch_port(port):
    fw = FirmwareCli(port, None, verbosity)
    while cansleft:
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
        display_que.put((CMD_SET,'A' ,'plug',0,2))
        sleep(1)
        display_que.put((CMD_SET,'Bx','plug',1,3))
        sleep(1)
        display_que.put((CMD_MESSAGE,("Please plug in serial cables.",)))
        sleep(1)
        display_que.put((CMD_SET, 'Ax', 'version', 0, '0278'))
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
            pass
        elif op[0] == CMD_CONNECTED:
            pass

except KeyboardInterrupt:
    pass

display_que.put((CMD_STOP,))
display_thr.join()
    
if cansleft:
    print "The following canisters have not been programmed:"
    print " ".join(sorted(list(cansleft)))
    cansleft = None
for thr in port_threads:
    thr.join()


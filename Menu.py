import types
import collections
import sys

from configuration import Configuration

class Menu(object):

    # Magic function element that is translated to self.stopfunc.
    stop = -1

    @staticmethod
    def clear():
        """
        Clear the screen,
        only if the configuration says it's OK.
        """
        if Configuration.getClear() and Configuration.getInteractive():
            sys.stdout.write(Configuration.clearcode)

    @staticmethod
    def wait():
        """
        Prompt and wait for user to press enter,
        only if the configuration says it's OK.
        """
        if Configuration.getClear() and Configuration.getInteractive():
            print
            print "press enter",
            raw_input()


    def __init__(self, title, data):
        self.title = title
        self.data  = data
        # Verify input.  Convert Menu.stop to self.stopfunc.
        for item in self.data:
            assert(hasattr(item, '__getitem__'))
            assert(isinstance(item, collections.Sequence))
            assert(2 <= len(item) <= 3)
            if item[1] == Menu.stop:
                item[1] = self.stopfunc
            assert(type(item[1]) in (types.FunctionType, types.MethodType))

    def run(self, clparms=None):
        if clparms:
            inp = self.match(clparms[0])
            if isinstance(inp, int):
                # special-case the first menu item ("Exit" == "help")
                if inp == 0:
                    self.help()
                else:
                    self.data[inp][1](clparms[1:])
            elif isinstance(inp, collections.Sequence):
                print "Argument '" + clparms[0] + "' is ambiguous; it could mean any of " + str(inp) + "."
            elif not inp:
                print "Argument '" + clparms[0] + "' isn't a valid keyword. Try 'help'."
        else:
            # Find width of menu numbers.
            powerOfTen = 1
            width = 0
            while len(self.data) > powerOfTen:
                powerOfTen *= 10
                width += 1
            index_form = '%' + str(width) + 'd:'
            # menu
            self.running = True
            while self.running:
                self.clear()
                # Find length of longest keyword shortcut.
                longest = 0
                for item in self.data:
                    if len(item) > 2:
                        if  longest < len(item[2]):
                            longest = len(item[2])
                shortcut_form = "%-" + str(longest+3) + "s"
                # Print heading.
                print '-' * 20
                print self.title
                print '-' * 20
                # Print menu.
                for idx in range(len(self.data)):
                    print index_form % idx,
                    if Configuration.shortcuts:
                        if idx == 0:
                            print shortcut_form % "",
                        else:
                            print shortcut_form % ('(' + self.data[idx][2] + ')'),
                    print self.data[idx][0]
                print 'choose:',

                try:
                    rawinp = raw_input()
                except KeyboardInterrupt:
                    print
                    sys.exit()
                except EOFError:
                    print
                    self.stopfunc(None)
                    continue

                try:
                    inp = int(rawinp)
                except:
                    inp = -1

                if not 0 <= inp < len(self.data):
                    print "bad item number"
                    continue

                try:
                    self.data[inp][1](None)
                except KeyboardInterrupt:
                    print
                    sys.exit()

    def stopfunc(self, p):
        self.running = False

    def match(self, word):
        """
        Attempt to match word to all of self.data[x][2].
        If there are 0 matches, return None.
        If there is 1 match, return its index.
        If there are 2 or more matches, return a list of the keywords.
        The input word matches a keyword if it is an initial substring.
        """
        word = word.lower()
        matches = tuple(x for x in range(len(self.data)) if len(self.data[x]) > 2 and self.data[x][2] and self.data[x][2].startswith(word))
        if len(matches) == 0: return None
        if len(matches) == 1: return matches[0]
        return tuple(self.data[x][2] for x in matches)

    def help(self):
        width = 0
        for item in self.data[1:]:
            if item[2]:
                if  width < len(item[2]):
                    width = len(item[2])
        print "Valid values are"
        for item in self.data[1:]:
            if item[2]:
                print ("%-"+str(width)+"s: %s") % (item[2], item[0])
        pass


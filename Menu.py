import types
import collections
import sys

class Menu(object):
    
    stop = -1
    
    def __init__(self, title, data):
        self.title = title
        self.data  = data
        # Verify input.
        for item in self.data:
            try:
                if not hasattr(item, '__getitem__'):
                    raise Exception("not a list")
                if not isinstance(item, collections.Sequence):
                    raise Exception("not a list")
                if len(item) != 2:
                    raise Exception("data[x] must have length 2")
                if item[1] == Menu.stop:
                    item[1] = self.stopfunc
                if type(item[1]) not in (types.FunctionType, types.MethodType):
                    raise Exception("data[x][1] must be a function or Menu.stop")
            except:
                raise #Exception("data must be a list")
        
    def run(self):
        # Find width of menu numbers.
        pot = 1
        width = 0
        while len(self.data) > pot:
            pot *= 10
            width += 1
        form = '%' + str(width) + 'd:'
        # menu
        self.running = True
        while self.running:
            print '-' * 20
            print self.title
            print '-' * 20
            for idx in range(len(self.data)):
                print form % idx, self.data[idx][0]
            print 'choose:',
            try:
                rawinp = raw_input()
            except KeyboardInterrupt:
                print
                sys.exit()
            except EOFError:
                print
                self.stopfunc()
                continue
            try:
                inp = int(rawinp)
            except:
                inp = -1
            if not 0 <= inp < len(self.data):
                print "bad item number"
                continue
            try:
                self.data[inp][1]()
            except KeyboardInterrupt:
                print
                sys.exit()

    def stopfunc(self):
        self.running = False

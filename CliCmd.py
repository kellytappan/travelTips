import abc

class CliCmd(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def close(self):
        pass
    
    @abc.abstractmethod
    def execute(self, cmd):
        pass
    
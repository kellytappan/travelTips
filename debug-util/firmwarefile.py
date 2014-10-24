
import os.path
import subprocess
import tempfile
import shutil

class FirmwareFile():
    """
    operations pertaining to firmware files
    """
    
    def __init__(self, name):
        """
        "name" can be either
          a single firmware file,
          a 7z archive of firmware files,
          or a directory of firmware files.
        """
        self.name = name

        self.tmpdir = None
        self.fwdict = {}
        
        if os.path.isfile(name):
            self.tmpdir = tempfile.mkdtemp("", "fw-")
            result = subprocess.call(['7za','x','-o'+self.tmpdir,self.name], stdout=open("/dev/null","w"))
            print "result =", result
            if   result is 0:
                self._populate_from_dir(self.tmpdir)
            elif result is 2:
                self._populate_from_file(self.name)
            else:
                print "7z error", result
        elif os.path.isdir(name):
            self._populate_from_dir(self.name)
        else:
            print "path not found:", self.name
            
    def __del__(self):
        if self.tmpdir:
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _log(self, level, message):
        pass

    def identifyfile(self, filename):
        """ Attempt to determine version and productid of a firmware file. """
        f = open(filename, 'rb')

        f.seek(0x00)
        magic = f.read(8)
        if magic != "JBL_ISTR":
            self._log(2, "file has bad magic number")
            return None

        f.seek(0x0c)
        version = f.read(2)
        version = (ord(version[0]) << 8) + (ord(version[1]) << 0)
        version = "%04X" % version
        self._log(2, "file version   = "+version)

        f.seek(0x2b)
        productid = f.read(16)
        self._log(2, "file productid = "+productid)

        return (version, productid)
    
    def _populate_from_file(self, filename):
        identity = self.identifyfile(filename)
        if identity:
            version, productid = identity
            if version not in self.fwdict:
                self.fwdict[version] = {}
            self.fwdict[version][productid] = filename
    
    def _populate_from_dir(self, dirname):
        for basename in os.listdir(dirname):
            fullname = os.path.join(dirname, basename)
            if os.path.isfile(fullname):
                self._populate_from_file(fullname)
            elif os.path.isdir(fullname):
                self._populate_from_dir(fullname)
            else:
                pass  # Ignore non-file, non-directory paths.

    def get_versions(self):
        return self.fwdict.keys()
    
    def get_filename(self, productid, version=None):
        if   len(self.fwdict) is 0:
            # We didn't find any firmware files.
            return None
        elif len(self.fwdict) is 1:
            if version and self.fwdict.keys()[0] != version:
                # The requested version didn't match the version we found.
                return None
            if not version:
                # No specific version requested; use the one we found.
                version = self.fwdict.keys()[0]
        else:
            # We found more than one version.
            if not version:
                # Version not specified. Still OK if we have exactly one matching productid.
                for v in self.fwdict:
                    if productid in self.fwdict[v]:
                        if version:
                            # Found more than one candidate version.
                            return None
                        else:
                            version = v
        if version not in self.fwdict:
            # We didn't find any files with that version.
            return None
        if productid not in self.fwdict[version]:
            # We found that version, but not that productid.
            return None
        # We have well-enough-specified version and productid, and a matching file exists.
        return self.fwdict[version][productid]

    def get_all(self):
        return self.fwdict


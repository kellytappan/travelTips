from distutils.core import setup
setup(
    name='wcdu',
    version='0.2.2',
    py_modules=[
        'configuration', 'discovery', 'Menu',
        'CliCmd', 'CliCmdSerial', 'CliCmdTelnet', 'CliCmdSas',
        'SesPage', 'SesPageFile', 'SesPageCli', 'SesPageSas',
	'firmwarefile', 
    ],
    scripts=['wcdu', 'wcdu-cli', 'slowfan3', 'discovery-test', 'firmwarecli.py', 'fw.py', ],
    data_files=[('/usr/local/share/wcdu', ['wcdu-guide.pdf']), ],
    install_requires=['scsi_pt', 'argparse', 'pexpect', 'pyserial', ],
    author='Larry Fenske',
    author_email='jabil@towanda.com',
    url='http://jabil.com',
)

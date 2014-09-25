from distutils.core import setup
setup(
    name='wcdu',
    version='0.1.0a2',
    py_modules=[
        'configuration', 'discovery', 'Menu',
        'CliCmd', 'CliCmdSerial', 'CliCmdTelnet', 'CliCmdSas',
        'SesPage', 'SesPageFile', 'SesPageCli', 'SesPageSas',
    ],
    scripts=['wcdu', 'wcdu-cli', 'slowfan', 'slowfan2', 'slowfan3', ],
    install_requires=['scsi_pt', 'argparse', 'pexpect', 'pyserial', ],
)

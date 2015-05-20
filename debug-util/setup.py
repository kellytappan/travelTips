from distutils.core import setup
d = '/usr/local/lib/wcdu'
setup(
    name='wcdu',
    version='0.4.0',
    py_modules=[
        'configuration', 'discovery', 'Menu',
        'CliCmd', 'CliCmdSerial', 'CliCmdTelnet', 'CliCmdSas',
        'SesPage', 'SesPageFile', 'SesPageCli', 'SesPageSas',
        'firmwarefile', 'firmwarewc',
    ],
    scripts=[
        'wcdu',
        'wcdu-cli',
        'slowfan3',
        'discovery-test',
        'firmwarecli.py',
        'bbfw',
        'wcfw',
    ],
    data_files=[
        (d+'/documents', ['wcdu-guide.pdf']),
        (d+'/utilities', [
            'utilities/flashrom',
            'utilities/layout.txt',
            'utilities/Yafuflash64'
            ]),
        (d+'/utilities/PlxSdk/Samples/PlxCm/App', [
            'utilities/PlxSdk/Samples/PlxCm/App/PlxCm',
            ]),
        (d+'/utilities/PlxSdk/Samples/PlxEep/App', [
            'utilities/PlxSdk/Samples/PlxEep/App/PlxEep',
            ]),
        (d+'/utilities/PlxSdk/Driver/PlxSvc', [
            'utilities/PlxSdk/Driver/PlxSvc/PlxSvc.ko',
            ]),
        (d+'/utilities/PlxSdk/Driver/Plx8000_NT', [
            'utilities/PlxSdk/Driver/Plx8000_NT/Plx8000_NT.ko',
            ]),
        (d+'/utilities/PlxSdk/Bin', [
            'utilities/PlxSdk/Bin/Plx_load',
            'utilities/PlxSdk/Bin/Plx_unload',
            'utilities/PlxSdk/Bin/startlog',
            ]),
    ],
    install_requires=[
        'scsi_pt>=0.1.3',
        'listdict',
        'argparse',
        'pexpect',
        'pyserial',
        'xmodem',
    ],
    author='Larry Fenske',
    author_email='jabil@towanda.com',
    url='http://jabil.com',
)

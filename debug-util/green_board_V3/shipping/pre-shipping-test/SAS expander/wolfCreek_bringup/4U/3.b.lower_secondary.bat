rem call generate_serialport_cfg.bat
pw5.exe %~dp0..\jPro.wax -c Wolfcreek_upper_lower_sec
reg delete "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\COM Name Arbiter" /v ComDB /f


@echo off

call serialport.bat

rem for secondary SXP:
start ttpmacro %~dp0..\upgradeFEM.ttl       /C=%A0_PORT_NUM%  


echo on

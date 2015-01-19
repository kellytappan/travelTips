@echo off
call serialport.bat
rem for Primary SXP:
start ttpmacro %~dp0..\autoFEM_SASCPLD.ttl  /C=%A0_PORT_NUM% 
echo on

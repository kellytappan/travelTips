@ECHO OFF
set instanceid0=%1
set instanceid1=%2
if "%instanceid0%"=="" then goto ERROR
if "%instanceid1%"=="" then goto ERROR
set MAC0=0001ff0B%instanceid0%%instanceid1%
set MAC1=0001ff4B%instanceid0%%instanceid1%
set WWN0=50001FF0B%instanceid0%%instanceid1%000
set WWN1=50001FF0B%instanceid0%%instanceid1%100
set WWN2=50001FF0B%instanceid0%%instanceid1%200
set WWN3=50001FF0B%instanceid0%%instanceid1%300
set WWN4=50001FF0B%instanceid0%%instanceid1%400
set WWN5=50001FF0B%instanceid0%%instanceid1%500
set WWN6=50001FF0B%instanceid0%%instanceid1%600
set WWN7=50001FF0B%instanceid0%%instanceid1%700
set WWN8=50001FF0B%instanceid0%%instanceid1%800
set WWN9=50001FF0B%instanceid0%%instanceid1%900
set WWNA=50001FF0B%instanceid0%%instanceid1%A00
echo "eeupdate /nic=1 /mac=%MAC0%"
eeupdate /nic=1 /mac=%MAC0%
echo "eeupdate /nic=2 /mac=%MAC1%"
eeupdate /nic=2 /mac=%MAC1%
echo "ipmitool 20 f0 60 1 00 01 FF 5B %instanceid0% %instanceid1%"
ipmitool 20 f0 60 1 00 01 FF 5B %instanceid0% %instanceid1%
echo "sas3flsh -c 0 -o -sasadd %WWN0%"
sas3flsh -c 0 -o -sasadd %WWN0%
sas3flsh -c 1 -o -sasadd %WWN1%
sas3flsh -c 2 -o -sasadd %WWN2%
sas3flsh -c 3 -o -sasadd %WWN3%
sas3flsh -c 4 -o -sasadd %WWN4%
sas3flsh -c 5 -o -sasadd %WWN5%
sas3flsh -c 6 -o -sasadd %WWN6%
sas3flsh -c 7 -o -sasadd %WWN7%
sas3flsh -c 8 -o -sasadd %WWN8%
sas3flsh -c 9 -o -sasadd %WWN9%
echo "sas3flsh -c a -o -sasadd %WWNA%"
sas3flsh -c a -o -sasadd %WWNA%
goto END
:ERROR
echo "Input Error"

:END
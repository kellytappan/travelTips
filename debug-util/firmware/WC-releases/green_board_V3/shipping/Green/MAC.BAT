@ECHO OFF
set instanceid=%1
if "%instanceid%"=="" then goto ERROR
set MAC0=0001ff0B%instanceid%
set MAC1=0001ff4B%instanceid%
set WWN0=50001FF0B%instanceid%000
set WWN1=50001FF0B%instanceid%100
set WWN2=50001FF0B%instanceid%200
set WWN3=50001FF0B%instanceid%300
set WWN4=50001FF0B%instanceid%400
set WWN5=50001FF0B%instanceid%500
set WWN6=50001FF0B%instanceid%600
set WWN7=50001FF0B%instanceid%700
set WWN8=50001FF0B%instanceid%800
set WWN9=50001FF0B%instanceid%900
set WWNA=50001FF0B%instanceid%A00
eeupdate /nic=2 /mac=%MAC0%
eeupdate /nic=2 /mac=%MAC1%
sas3flsh -c 0 -o -sasadd %WWN0%
sas3flsh -c 0 -o -sasadd %WWN1%
sas3flsh -c 0 -o -sasadd %WWN2%
sas3flsh -c 0 -o -sasadd %WWN3%
sas3flsh -c 0 -o -sasadd %WWN4%
sas3flsh -c 0 -o -sasadd %WWN5%
sas3flsh -c 0 -o -sasadd %WWN6%
sas3flsh -c 0 -o -sasadd %WWN7%
sas3flsh -c 0 -o -sasadd %WWN8%
sas3flsh -c 0 -o -sasadd %WWN9%
sas3flsh -c 0 -o -sasadd %WWNA%
goto END
:ERROR
echo "Input Error"

:END
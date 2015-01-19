#######################################################################
#####################           usage          ########################
#######################################################################

1.append the loacation of Procomm (pw5.exe) and TeraTerm executables to 
  PATH system environment variable.
2.Change the parameters /C=x in the 4U/fwUpdate.bat. Use 6 serial cables
  if you want to reduce the update time.
3.Update SAS FW & CPLD by double clicking 4U/fwUpdate.bat.
4.Change the serialport.cfg file according to the real execution 
  environment, like serial connection port etc.
5.Double click the SideA.bat or SideB.bat to run the diag tool for each 
  side spearatly.



#######################################################################
#####################           Change log          ###################
#######################################################################

###### ver 0.1 features  ######
###############################

1.bm.bat         - blue moon SAS FW and CPLDs upgrade
2.fem.bat        - fem SAS FW upgrade and FRU data flash
3.sideA.bat      - executing side A test case  against the Trinidad preship test plan
4.sideB.bat      - executing side B test cases against the Trinidad preship test plan
5.powercycle.bat - execute system powercycle test


#####  ver 0.2 fiexed bugs and adjustment  #####
################################################

1.fixed BM sas FW version check issue
2.change blue moon reset mothod after SAS FW and CPLD upgrading (from automatic to manually operation) 
3.change the prompting message to "please turn the power off and then on" when doing powercycle test.
4.add this file.

known issues:
1.can not reset correctly after FW and CPLD upgrading 
2.ipmifru str commands can not run as well as expected. 
3.can not control local BM cannister ID LED 


#####  ver 0.3 fiexed bugs and adjustment  #####
################################################

1.fixed bugs (D-0002880,D-0002869)
2.removed the FEM/BM SAS FW update feature from BM/FEM test ( BMwithoutSASupgrade.bat | FEMwithoutSASupgrade.bat )
3.removed the BB/DAP CPLD update feature from sideA test ( sideAwithoutU.bat )


unsupported feature:
BM/FEM SAS FW and BB/DAP CPLD update

note:
1.BM SAS FW update by hands befor running BMwithoutSASupgrade.bat
	a.upgrade BM SAS FW to 0004 offical release version
	b.update to rom version for ipmifru issue

2.FEM SAS FW update by hands befor running FEMwithoutSASupgrade.bat 
	a.upgrade FEM SAS FW to 0004 offical release verion
	b.update to rom version for ipmifru issue
	c.upgrade fem bootloader to 0005 version

3.DAP/BB CPLD update by hands befor running sideAwithoutU.bat
	a.mount DAP
	b.upgrade DAP CPLD to 07 version
	c.unmount DAP after success
	d.upgrade BB CPLD to 12 version
	e.mount DAP



#####  ver 0.4 fiexed bugs and adjustment  #####
################################################

Note:Full removed FEM/BM SAS FW update functional

1.fixed bugs
2.BM CPLD update and FRU data     		     (BM.bat)
3.FEM FRU data			  		     (FEM.bat)
4.side A test without DAP and baseboard CPLD update  (sideA_withoutDapBbCPLDupdate.bat)
5.side B test					     (sideB.bat)	
6.add sas port test
7.power cycle test 				     (powerCycle.bat)


#####support Skytree 2U diag since this version#####

  a.SAS fw update function        (2U_SasFWupdate.bat)
  b.CPLD update and BM FRU data   (2U_BM.bat)
  c.Side A test                   (2U_sideA.bat)
  d.Side B test			  (2u_sideB.bat)
  e.powercycle test		  (powerCycle.bat)         

note:
  1.Have changed to use Tera Term Pro to update the SAS FW.
    Make sure the Tera Term Pro have been installed and set the installation location to the "PATH" system environment variable before running the FW update execution.

  2.Change the serail port configuration before running 2U_SasFWupdate.bat file
    a.open the 2u_SasFWupdate.bat then edit the below content:

      ttermpro /c=3 /BAUD=115200 /M=c:/trinidad/upgradeBM.ttl

    b. /C=3 means using serial port COM3 to connecton remote host, please change it depends on real running environment.
       /C=1   #COM1
       /C=2   #COM2
       ...
       /C=255 #COM255


#####  ver 0.5 fiexed bugs and adjustment  #####
################################################

1.fixed issues and bugs
2.add MP/BB SAS address write/read test
3.add HDD ID LEDs test
4.fixed Part Number (FEM PN: FUPBA001287A  |  BM PN:FUPBA001308A  |  MP PN:FUPBA001286A  |  Chassis PN:FUASF005420A   |  BB PN:FUPBA001285A) that don't need to be scan.

known issues:
1.DAP/Baseborad CPLD update unsupported
2.ODP board test unsupported


##### ver 0.5.1 fiexed bugs and adjustment #####
################################################

1.fixed issues (D-0004222,D-0003602,D-0003603,D-0003064,D-0002908,D-0003063,D-0002869,D-0003856,D-0002880,D-0003601,D-0003868,D-0003871,D-0003600,D-0003870	,D-0003869,D-0003599,D-0003598)
2.add DAP/Base board CPLD hard update for DVT test

known issues:
1.ODP board test unsupported

#####  ver 1.0 fiexed bugs and adjustment ######
################################################
1.base on SAS FW 0100 version
2.for Trinidad Rev B system

known issues
1.ODP board test unsupported

#####  ver 1.1 fiexed bugs and adjustment ######
################################################
1.update Bluemoon CPLD update function (SAS CONN 05,SBBMI 02)
2.add ODP board test supported
3.add dongle card test for Skytree R12 

#####  ver 1.2 fiexed bugs and adjustment ######
################################################
1.fixed issues
2.supported BM sas fw 0120 version
3.supported SASCONN and SBBMI CPLD 0.6 version


#####  ver 1.3 fiexed bugs and adjustment ######
################################################
1.fixed issues
2.supported BM sas fw 0131 version


#####  ver 1.3.1 fiexed bugs and adjustment ######
################################################
1.fixed issues

#####  ver 1.3.2 fiexed bugs and adjustment ######
################################################
1.support BM SAS FW 0133
2.support SBBMI CPLD 07
3.support SASCONN CPLD 06
4.mfg data time change to 20130416 for wuxi build

#####  ver 1.3.3 fiexed bugs and adjustment ######
################################################
1.support BM SAS FW 0134
2.combind 2u r12 and r14 into one project

#####  ver 1.3.4 fiexed bugs and adjustment ######
################################################
1.support BM SAS FW 0151
2.update VPD programming according to new FW spec.
3.combind 2u,4u into one project

#####  ver 1.3.5 fiexed bugs and adjustment ######
################################################
1.support 4U diag
2.fixed bugs

#####  ver 1.3.6 fiexed bugs and adjustment ######
################################################
1.fixed known issues
2.add FEM sxp1 FW upgrade
3.add FEM sxp1 PHY test
4.support BM/FEM SAS FW 0151 version
5.support SBBMI CPLD 07 version
6.support SASCONN CPLD 06 version
7.support DAP CPLD 0x0b version 
8.support Baseboard CPLD 0x11 version 

#####  ver 1.3.7 fiexed bugs and adjustment ######
################################################
1.fixed known issues

#####  ver 1.3.8 fiexed bugs and adjustment ######
################################################
1.fixed known issues

#####  ver 1.3.9 fiexed bugs and adjustment ######
################################################
1.fixed known issues
2.miniside A|B test

#####  ver 1.4.0 fiexed bugs and adjustment ######
################################################
1.chage hdd hotswap check method
2.miniSide test for 2U R12 & R24

#####  ver 1.4.1- 1.4.7  fiexed bugs and adjustment ######
################################################
1. Update the flash item for VPD. 
2. Update the flash method for MFG. D/T to system time.
3. Upgrate the FW/CPLD version

The FW version as below:
BM BOOTLOADER            V01.70
FEM BOOTLOADER			 V01.40
BM/FEM SAS               V0197
SASCONN CPLD             0x08
SBBMI CPLD               0x09
BB CPLD					 0x18
DAP CPLD                 0x0e

#####  ver 1.4.8 - 1.5.3  fiexed bugs and adjustment ######
################################################
1. Update the MP/BB VPD method for Skytree4U PVT2 test


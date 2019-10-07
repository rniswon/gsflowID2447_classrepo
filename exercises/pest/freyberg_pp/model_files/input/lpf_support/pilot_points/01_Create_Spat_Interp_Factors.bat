@echo off

REM   %1    Model name 
REM   %2    Structure name and final array label in file name
REM   %3    Layer number

Call  02_Create_Vario_For_Spat_Interp_K.bat  .\freyberg.spec    HydKh_L_1   1
echo .
echo **************************************************************************************
echo Finished Interpolating Pilot Points and Writing New "Factor" File For Layer 1 Horz. K
echo **************************************************************************************
echo .

REM If creating factors for more than one layer, one can add them here...

REM Call  02_Sub.Create_Factors_For_Spat_Interp_K.bat  .\freyberg.spec    HydKh_L_2   2
REM echo .
REM echo **************************************************************************************
REM echo Finished Interpolating Pilot Points and Writing New "Factor" File For Layer 2 Horz. K
REM echo **************************************************************************************
REM echo .


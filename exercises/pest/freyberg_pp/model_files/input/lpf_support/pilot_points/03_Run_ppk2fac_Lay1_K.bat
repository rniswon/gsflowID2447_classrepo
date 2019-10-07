@echo off
REM     VARTYPE
REM     “1”   spherical variogram
REM     “2”   exponential variogram
REM     “3”   Gaussian variogram
REM     “4”   power variogram

REM  Translate PilotPoints to interpolation factors for filling an array ------------------------------

REM   %1    Enter name of grid specification file:
REM   %2    Enter name of pilot points file [points.dat]:  ---  File altered by PEST 
REM   %3    Enter name of zonal integer array file:
REM   %4    Enter name of structure file:
REM   %6    Enter structure name (blank if no interpolation for this zone):
REM   %7    Enter search radius:
REM   %5    Enter name for interpolation factor file:


REM _________________________________  CREATE PP factors for layer 1 _________________________
REM
REM  Enter name of grid specification file:
echo %1      > Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter name of pilot points file:
echo %2     >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter minimum allowable points separation:
echo 0.0    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter name of zonal integer array file:
echo %3     >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Is this a formatted or unformatted file? [f/u]:
echo f      >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter name of structure file:
echo %4     >> Auto_Set_Parameter_Values_For_ppk2fac.txt

REM     For zone characterised by integer value of 0:-
REM     Enter structure name (blank if no interpolation for this zone):
echo                                                                                  . >> Auto_Set_Parameter_Values_For_ppk2fac.txt

REM     For zone characterised by integer value of 1:-
REM     Enter structure name (blank if no interpolation for this zone):
echo %6     >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM     Perform simple or ordinary kriging [s/o]:
echo o    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM     Enter search radius:
echo %7   >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM     Enter minimum number of pilot points to use for interpolation:
echo 1    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM     Enter maximum number of pilot points to use for interpolation:
echo 8    >> Auto_Set_Parameter_Values_For_ppk2fac.txt

REM  Enter name for interpolation factor file:
echo %5    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Is this a formatted or unformatted file? [f/u]:
echo f    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter name for output standard deviation array file:
echo sd.ref.txt    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Is this a formatted or unformatted file? [f/u]:
echo f    >> Auto_Set_Parameter_Values_For_ppk2fac.txt
REM  Enter name for regularisation information file:
echo reg.ref.txt   >> Auto_Set_Parameter_Values_For_ppk2fac.txt

ppk2fac.exe  < Auto_Set_Parameter_Values_For_ppk2fac.txt  >>  s.report.txt


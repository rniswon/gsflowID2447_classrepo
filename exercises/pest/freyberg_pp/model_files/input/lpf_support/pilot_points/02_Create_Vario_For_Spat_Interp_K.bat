@echo off
echo colrow=no           > settings.fig
echo date=mm/dd/yyyy    >> settings.fig

REM     VARTYPE
REM     “1”   spherical variogram
REM     “2”   exponential variogram
REM     “3”   Gaussian variogram
REM     “4”   power variogram
REM 

echo STRUCTURE %2              > Struct_File.%2.Variogram.txt
echo     NUGGET 0.03          >> Struct_File.%2.Variogram.txt
echo     NUMVARIOGRAM 1       >> Struct_File.%2.Variogram.txt
echo     VARIOGRAM var1 0.19  >> Struct_File.%2.Variogram.txt
echo     TRANSFORM log        >> Struct_File.%2.Variogram.txt
echo END STRUCTURE            >> Struct_File.%2.Variogram.txt
echo VARIOGRAM var1           >> Struct_File.%2.Variogram.txt
echo     VARTYPE 1            >> Struct_File.%2.Variogram.txt
echo     A 2500               >> Struct_File.%2.Variogram.txt
echo     ANISOTROPY 1.0       >> Struct_File.%2.Variogram.txt
echo     BEARING 0.0          >> Struct_File.%2.Variogram.txt
echo END VARIOGRAM            >> Struct_File.%2.Variogram.txt


REM  Translate PilotPoints to interpolation factors for filling an array ------------------------------

REM   %1    Enter name of grid specification file:                                             INPUT
REM   %2    Enter name of pilot points file [points.dat]:  ---  File altered by PEST           INPUT
REM   %3    Enter name of zonal integer array file:                                            INPUT
REM   %4    Enter name of structure file:                                                      INPUT -- Created in this batch file
REM   %5    Enter name for interpolation factor file:                                          OUTPUT
REM   %6    Enter structure name (blank if no interpolation for this zone):                    Variable being passed and used in  01_Sub.FACfileCreate?.bat files
REM   %7    Enter search radius:                                                               Variable being passed and used in  01_Sub.FACfileCreate?.bat files

REM                              %1              %2                         %3                        %4                                 %5                  %6         %7
REM                             ----    ---------------------   ----------------------    ------------------------------   ------------------------------    --       ------

call 03_Run_ppk2fac_Lay1_K.bat   %1    ..\Lay_%3_K_PP_List.txt    .\Lay%3_Zone_Arr.txt    .\Struct_File.%2.Variogram.txt   ..\freyberg_interp_factors.txt    %2       1500.0

REM pause

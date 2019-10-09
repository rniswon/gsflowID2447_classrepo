@echo off
REM
REM  ____________________ Interpolate from PP to a 2D arrays___________________________________
REM                     PP were translated to factors by node   
REM
REM  Program FAC2REAL carries out spatial interpolation based on interpolation
REM  factors calculated by PPK2FAC and pilot point values contained in a pilot
REM  points file.

REM  The following is a key for the parameters that were passed to this file.
REM  %1 :: Alameda-Interpolated_%2_By_Pest.txt  where %2 = HydK  or SY
REM  %2 :: ..\Alameda_%3.txt         
REM  %3 :: MF_Array.Lay01-%2.txt
REM  %4 :: HydK or surfK

REM  Enter name of interpolation factor file:
echo %1                                                                               > Temp_Control_File_PP_to_2D_arrays.txt
REM  Is this a formatted or unformatted file? [f/u]:
echo f                                                                               >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Enter name of pilot points file [points.dat]:
echo %2                                                                              >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Supply lower interpolation limit as an array or single value? [a/s]:
echo s                                                                               >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Enter lower interpolation limit:
echo 1e-8                                                                            >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Supply upper interpolation limit as an array or single value? [a/s]:
echo s                                                                               >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Enter upper interpolation limit:
echo 1e8                                                                             >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Enter name for output real array file:
echo %3                                                                              >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Is this a formatted or unformatted file? [f/u]:
echo f                                                                               >> Temp_Control_File_PP_to_2D_arrays.txt
REM  Enter value for elements to which no interpolation takes place:
echo 0.000                                                                           >> Temp_Control_File_PP_to_2D_arrays.txt


Fac2REAL.exe  < Temp_Control_File_PP_to_2D_arrays.txt  

REM call 02_Sub.ReformARRAY.bat %3   %4

REM del %3
REM rename %3.new %3

      
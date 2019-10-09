@echo off

REM __________________________________________________________________________________________________

REM  The following is a key for what parameters were passed to this file.
REM  %1  :: HydKh
REM  %2  :: L_1
REM  %3  :: Lay_1


REM  Next, specify the parameters required by the called upon batch file.
REM   %1    Enter name of interpolation factor file:                                 
REM   %2    Enter name of pilot points file [list of ppts]:  ---  File altered by PEST 
REM   %3    Enter name for output real array file for use by process model:                                   

REM For Hydraulic conductivity of layer 1
REM ------------------------------------------

call 03_PP2Layer.bat    .\freyberg_interp_factors.txt    .\%3_K_PP_List.txt      .\%1_%2.txt 

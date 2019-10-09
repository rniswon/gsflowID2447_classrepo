@echo off
echo colrow=no           > settings.fig
echo date=mm/dd/yyyy    >> settings.fig


REM __________________________________________________________________________________________________
REM
REM  

REM                                  %1    %2    %3  
REM                                  --    --    --  
call 02_Build_arr_hk.bat            HydKh  L_1  Lay_1   

echo .
echo *********************************************
echo Finished Interpolating Pilot Points to Arrays
echo *********************************************
echo .

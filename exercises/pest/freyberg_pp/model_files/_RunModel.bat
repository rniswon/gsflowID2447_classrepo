REM Update K array with latest pilot point values
cd   .\input\lpf_support\
call 01_Interp_ppts.bat
call ReformARRAY.exe < reformArray.in
cd   .\..\..\

REM Run process model
.\..\..\..\..\bin\mf_nwt_1.1.4.exe .\freyberg.nam
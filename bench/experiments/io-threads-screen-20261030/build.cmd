@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
if errorlevel 1 exit /b %errorlevel%
set SRC=C:\Users\User\native-pipe-generic-20261029
set BEST=C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build
cl /nologo /TP /std:c++20 /EHsc /O2 /Ob2 /DNDEBUG /MD /I"%SRC%\include" bench.cpp /Feio_threads_bench.exe /link /nologo "%BEST%\strata_engine.lib" "%BEST%\strata_core.lib" "%BEST%\strata_kernels_cpu.lib" kernel32.lib user32.lib advapi32.lib
exit /b %errorlevel%

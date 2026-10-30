@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
if errorlevel 1 exit /b %errorlevel%
set SRC=C:\Users\User\native-pipe-generic-20261029
set BEST=C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build
set GG=C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\_deps\strata_llamacpp-src\ggml\include
cl /nologo /c /std:c++20 /EHsc /O2 /Ob2 /DNDEBUG /MD /arch:AVX2 /DSTRATA_AVXVNNI=1 /I"%SRC%\include" /I"%SRC%\third_party\ggml" /I"%GG%" kernel.cpp /Fokernel.obj /FAs /Fakernel.asm
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c++20 /EHsc /O2 /Ob2 /DNDEBUG /MD /I"%SRC%\include" /I"%SRC%\third_party\ggml" /I"%GG%" /I"%GG%\..\src" /Tpbench.cpp /Fep2bench.exe /link /nologo kernel.obj "%BEST%\strata_kernels_cpu.lib" "%BEST%\ggml\src\ggml-cpu.lib" "%BEST%\ggml\src\ggml-base.lib" kernel32.lib user32.lib advapi32.lib
exit /b %errorlevel%

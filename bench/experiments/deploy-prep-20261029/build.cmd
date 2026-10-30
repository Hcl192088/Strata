@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64
if errorlevel 1 exit /b %errorlevel%
cl 2> "C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\compiler-version.log"
nvcc --version > "C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\cuda-version.log"
cmake --version > "C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\cmake-version.log"
cmake -S "C:\Users\User\native-pipe-generic-20261029" -B "C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build" -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89 -DSTRATA_ENABLE_CUDA=ON -DFETCHCONTENT_SOURCE_DIR_STRATA_LLAMACPP="C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\_deps\strata_llamacpp-src"
if errorlevel 1 exit /b %errorlevel%
cmake --build "C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build" --target strata -j 2
exit /b %errorlevel%

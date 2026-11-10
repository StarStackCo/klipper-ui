@echo off
rem Repo -> this PC's OrcaSlicer: get the latest StarStack S1 profile and install it. Close Orca first.
cd /d "%~dp0"
git pull --ff-only || goto fail
python tools\orca_profile.py install || goto fail
pause
exit /b 0
:fail
echo FAILED, nothing more was changed.
pause
exit /b 1

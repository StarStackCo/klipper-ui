@echo off
rem This PC's OrcaSlicer -> repo: export the StarStack S1 presets, review, then commit and push.
rem Add a new preset by name: orca-export.bat "My New PLA"
cd /d "%~dp0"
git pull --ff-only || goto fail
python tools\orca_profile.py export %* || goto fail
set CHANGED=
for /f %%i in ('git status --porcelain -- config/s1/orca') do set CHANGED=1
if not defined CHANGED (echo No changes. & pause & exit /b 0)
git status --short -- config/s1/orca
set /p OK=Commit and push these changes? [y/N]
if /i not "%OK%"=="y" (echo Not committed. Undo with: git checkout -- config/s1/orca & pause & exit /b 0)
git add config/s1/orca || goto fail
git commit -m "Orca profile exported from %COMPUTERNAME%" || goto fail
git push || goto fail
echo Pushed. On the other computer: close Orca, run orca-install.bat.
pause
exit /b 0
:fail
echo FAILED.
pause
exit /b 1

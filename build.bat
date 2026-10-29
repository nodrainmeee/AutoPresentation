@echo off
REM Compilation locale FACULTATIVE (nécessite Python sur l'ordinateur).
REM GitHub Actions compile le logiciel pour vous : ce fichier est inutile dans ce cas.
chcp 65001 >nul
python -m pip install -r requirements.txt
python -m unittest discover -s tests -t . -v
if errorlevel 1 (
  echo Les tests ont échoué. Compilation annulée.
  exit /b 1
)
python -m PyInstaller --noconfirm AutoPresentation.spec
if exist dist\AutoPresentation.exe (
  echo Compilation réussie : dist\AutoPresentation.exe
) else (
  echo La compilation a échoué.
  exit /b 1
)

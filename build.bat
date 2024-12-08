@echo off
echo Installing requirements...
python -m pip install -r requirements.txt
echo Building executable...
python build.py
echo Build complete! Check the dist folder.
pause 
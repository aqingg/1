@echo off
title PUMA Client

echo Starting Python script in Conda environment 'puma'...

call conda activate puma 
python client.py

echo.
echo Script has finished. Press any key to exit.
pause
@echo off
echo Installing required packages...
pip install -r requirements.txt

echo Running CPWD tender scraper...
python cpwd_scraper_robust.py

echo Done!
pause
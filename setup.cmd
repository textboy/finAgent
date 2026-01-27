@echo off
echo Extracting repository...
git clone https://github.com/textboy/finAgent
cd finAgent
echo Creating conda environment for FinAgent...
conda create -n finagent python=3.12 -y
echo Activating environment and installing dependencies...
call conda activate finagent
pip install -r requirements.txt
echo.
echo Setup complete!
echo To run: conda activate finagent
echo Then: python finagent.py --symbol GOOG --period medium
echo Copy config/.env.example to config/.env and fill in your API keys.
pause
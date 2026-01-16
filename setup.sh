#!/bin/bash

echo "Extracting repository..."
git clone https://github.com/textboy/finAgent
cd finAgent

echo "Creating virtual environment for FinAgent..."
pip install virtualenv
virtualenv -p python3.12 finagent

echo "Activating environment and installing dependencies..."
source finagent/bin/activate  # Use `source` to activate the environment in bash
pip install -r requirements.txt

echo
echo "Setup complete!"
echo "To run: source finagent/bin/activate"
echo "Then: python finagent.py --symbol GOOG --period medium"
echo "Copy config/.env.example to config/.env and fill in your API keys."
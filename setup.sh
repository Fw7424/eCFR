#!/bin/bash

# Create virtual environment
python3 -m venv env

# Activate the virtual environment
source env/bin/activate

# Upgrade pip
pip3 install --upgrade pip

# Install dependencies
pip3 install flask flask-sqlalchemy

echo "✅ Environment setup complete. To activate, run: source env/bin/activate"

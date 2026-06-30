#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# Deactivate virtual environment when the app is closed
deactivate

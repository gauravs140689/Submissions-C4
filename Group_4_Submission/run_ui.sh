#!/bin/bash
echo "Starting Agentic Research Engine UI..."
echo "To access, open the URL shown below in your browser."

# Try to use the local environment python if it exists
if [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
elif [ -f ".venv/bin/python3" ]; then
    PYTHON=".venv/bin/python3"
else
    PYTHON="python3"
fi

# Run Streamlit with bytecode writing disabled to avoid permission errors
PYTHONDONTWRITEBYTECODE=1 $PYTHON -m streamlit run app.py

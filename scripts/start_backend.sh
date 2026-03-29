#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Suppress Spark warnings
export SPARK_LOCAL_IP=127.0.0.1
export PYSPARK_SUBMIT_ARGS="--conf spark.ui.showConsoleProgress=false pyspark-shell"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
export ENVIRONMENT=development
export DEBUG=true
export SPARK_CONF_DIR=/backend


# Create required directories
mkdir -p data/{raw,processed,uploads}
mkdir -p models/cache
mkdir -p logs

# Start the server
cd backend

# # Run main.py directly
# python app/main.py

# Or using uvicorn directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info

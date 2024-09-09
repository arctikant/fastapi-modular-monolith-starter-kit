#! /usr/bin/env bash

# Try to run prestart.sh script
PRE_START_PATH=${PRE_START_PATH:-prestart.sh}
echo "Checking for script in $PRE_START_PATH"
if [ -f $PRE_START_PATH ] ; then
    echo "Running script $PRE_START_PATH"
    . "$PRE_START_PATH"
else
    echo "There is no script $PRE_START_PATH"
fi

# Run server
echo "Starting development server..."
exec uvicorn "app.main:app" --reload --host $HOST --port $PORT
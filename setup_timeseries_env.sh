#!/usr/bin/env bash

set -e

pip install --upgrade pip
pip install pymongo

export MONGODB_URI='mongodb+srv://admin:passwordone@m10vdj.rjcj1k.mongodb.net/?appName=m10vdj'

echo "Virtual environment activated."
echo "pymongo installed."
echo "MONGODB_URI configured."
 
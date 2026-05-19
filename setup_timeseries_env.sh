#!/usr/bin/env bash

set -e

python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install pymongo

export MONGODB_URI='mongodb+srv://admin:<db_password>@<atlas_cluster_url>/?appName=<cluster_name>'

echo "Virtual environment activated."
echo "pymongo installed."
echo "MONGODB_URI configured."

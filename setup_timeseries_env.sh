#!/usr/bin/env bash

set -e

pip install --upgrade pip
pip install pymongo

export MONGODB_URI='mongodb+srv://admin:<db_password>@<atlas_cluster_url>/?appName=<cluster_name>'

echo "Virtual environment activated."
echo "pymongo installed."
echo "MONGODB_URI configured."
 
#!/bin/bash

set -e

echo "Starting SSH ..."
service ssh start

 gunicorn --bind 0.0.0.0:8000 pubmed_project.wsgi
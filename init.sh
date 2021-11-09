#!/bin/bash
-e 

gunicorn --bind 0.0.0.0:8000 pubmed_project.wsgi
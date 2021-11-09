#!/bin/bash
-e 
/usr/sbin/sshd
gunicorn --bind 0.0.0.0:8000 pubmed_project.wsgi
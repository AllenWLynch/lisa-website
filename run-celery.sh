#!/bin/bash 
celery worker -A lisa_web.celery --loglevel=info -E -c 8
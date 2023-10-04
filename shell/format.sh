#!/bin/bash
isort --sl demo/src/ demo/app.py
black --line-length 80 demo/src/ demo/app.py
flake8 demo/src/ demo/app.py

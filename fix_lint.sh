#!/bin/bash
# Auto-fix linting issues locally
echo "Fixing import order..."
source .venv/bin/activate
isort src/ui/ --recursive

echo "Fixing PEP8 issues..."
autopep8 --in-place --aggressive --aggressive --recursive src/ui/

echo "Running pylint to check remaining issues..."
pylint src/ui/ --recursive=y --score=yes

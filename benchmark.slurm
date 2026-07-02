#!/bin/bash

#SBATCH --job-name=sktime-benchmarking
#SBATCH --output=logs/output.log
#SBATCH --error=logs/error.log

#SBATCH --partition=main
#SBATCH --mem=4G

set -e

if [ ! -d ".venv" ]; then
    uv venv --python 3.11
fi

source .venv/bin/activate

uv lock --upgrade-package sktime
uv sync

python run_benchmark.py
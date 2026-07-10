# Benchmarking with `sktime` on a Slurm Cluster

This repository demonstrates how to run time series benchmarking experiments using sktime on a Slurm-managed compute cluster. sktime provides a benchmarking framework that lets you define an experiment declaratively and execute it on anything from a laptop to an HPC cluster.

## Repository structure

Two files drive the whole experiment:

| File | Role |
| --- | --- |
| `benchmark.slurm` | Slurm batch script. This is what you submit. It sets up the Python environment on the compute node and then runs the benchmark. |
| `run_benchmark.py` | The benchmark itself. A short Python vignette that builds and runs a `ForecastingBenchmark`. |

When you submit the job with `sbatch benchmark.slurm`, Slurm schedules the batch script on a compute node. That script creates/activates a virtual environment, installs dependencies, and finally executes:

```bash
python run_benchmark.py
```

So: Slurm runs the `.slurm` file; the `.slurm` file runs the `.py` file.

The Python script does not know about Slurm, the same `run_benchmark.py` can be run locally with `python run_benchmark.py`.

Supporting files:

* `pyproject.toml`: project dependencies (resolved with `uv`)
* `logs/`: Slurm stdout/stderr (`output.log`, `error.log`)
* `M4_competition_yearly_results.csv`: results written by the benchmark

## What this repository demonstrates

* Running a forecasting benchmark on a Slurm cluster
* Using `ForecastingBenchmark`
* Using a reusable catalogue (`M4CompetitionCatalogueYearly`)
* Producing a results CSV
* Automatically setting up the Python environment on the compute node

## Requirements and setup

### What you need

1. **Access to a Slurm cluster**: a machine (or set of machines) where `sbatch`, `squeue`, and related Slurm commands are available. Ask your HPC/admin team for an account if you do not already have one. Please refer to Slurm documentation for further information: https://slurm.schedmd.com/quickstart_admin.html

2. **A compute environment with:**
   * Python 3.11+ available (or installable)
   * [`uv`](https://docs.astral.sh/uv/) available on the PATH (used by `benchmark.slurm` to create the venv and install dependencies)
   * Network access from the compute node to install packages (PyPI and, for this demo, GitHub, see `pyproject.toml`)
3. This repository checked out on a filesystem visible to both the login node and the compute nodes of the cluster.

### Cluster / partition notes

Before submitting, edit the `#SBATCH` directives in `benchmark.slurm` to match your site:

* `--partition=main`: change to a partition you are allowed to use
* `--mem=8G`: adjust memory for your estimators/datasets
* Optionally add `--time=...`, `--cpus-per-task=...`, `--account=...`, etc.

### One-time local check (optional)

On a machine with the same Python/`uv` setup, you can validate the vignette without Slurm, though if the experiment is too large, it is not feasible:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv sync
python run_benchmark.py 
```

### Submitting on Slurm

From the repository root on the login node:

```bash
sbatch benchmark.slurm
```

The batch script will automatically:

1. Create a `.venv` if one does not already exist (`uv venv --python 3.11`)
2. Activate it
3. Refresh/install dependencies (`uv lock`, `uv sync`)
4. Run `python run_benchmark.py`
5. Write stdout/stderr to `logs/output.log` and `logs/error.log`

### Monitoring the job

```bash
squeue -u $USER
tail -f logs/output.log
# or
tail -f logs/error.log
```

---

## The benchmark vignette (`run_benchmark.py`)

The full experiment fits in a single short script. Follwing is the complete code alongwith explaination:

```python
"""M4 competition yearly catalogue run on the slurm cluster."""

from sktime.benchmarking.forecasting import ForecastingBenchmark
from sktime.catalogues import M4CompetitionCatalogueYearly
from sktime.split import ExpandingWindowSplitter

catalogue = M4CompetitionCatalogueYearly()
benchmark = ForecastingBenchmark(backend="loky")

benchmark.add(catalogue)
benchmark.add(ExpandingWindowSplitter(initial_window=12, step_length=2, fh=6))

print(benchmark.estimators.entities)
print(benchmark.tasks.entities)

results = benchmark.run("./M4_competition_yearly_results.csv")
```

The sections below walk through this vignette line by line: what a benchmark is, how catalogues work, how the CV strategy is added, and how results are written.

### Defining a benchmark

A benchmark in sktime consists of:

* estimators
* datasets
* evaluation strategy
* metrics

A dataset together with an evaluation strategy and a metric forms a **task**. These components are assembled into a `ForecastingBenchmark`:

```python
from sktime.benchmarking.forecasting import ForecastingBenchmark

benchmark = ForecastingBenchmark(backend="loky")
```

Estimators and tasks are then added to that benchmark instance.

### Building a benchmark manually

Components can be registered one by one:

* `add_estimator`: add estimators
* `add_task`: add tasks
* `add`: convenience wrapper over `add_estimator` and `add_task` that infers the scitype and registers the component

See the sktime example notebook: https://www.sktime.net/en/latest/examples/04_benchmarking_forecasters.html

### Using catalogues

Simply put, a catalogue is a collection of objects. It can also be used as reusable specification of a benchmarking experiment. Rather than manually registering every estimator, dataset, metric, and configuration, a catalogue bundles these into a single object that can be added directly to the benchmark. Catalogues may be partial, as in this example, where the CV splitter is left for the user to choose.

This demo uses `M4CompetitionCatalogueYearly`:

```python
from sktime.catalogues import M4CompetitionCatalogueYearly

catalogue = M4CompetitionCatalogueYearly()
benchmark.add(catalogue)
```

That registers the catalogue's components on the benchmark. `M4CompetitionCatalogueYearly` ships with sktime and currently includes the statistical baselines from the M4 competition, the M4 yearly dataset, and the competition metrics. You can define your own catalogues by inheriting from sktime's `BaseCatalogue`.

Docs: https://www.sktime.net/en/latest/api_reference/catalogues.html

### Configuring the evaluation strategy

The original M4 competition used fixed train/test files. In sktime, a task needs a CV strategy, so the vignette adds an expanding-window splitter. This could live in the catalogue, but because the original competition did not specify a splitter, it is left to the user:

```python
from sktime.split import ExpandingWindowSplitter

benchmark.add(
    ExpandingWindowSplitter(
        initial_window=12,
        step_length=2,
        fh=6,
    )
)
```

### Running the benchmark

```python
results = benchmark.run("./M4_competition_yearly_results.csv")
```

This evaluates every estimator on every task with the configured splitter and writes results to `M4_competition_yearly_results.csv`. JSON and Parquet are also supported. Result writing is crash-safe, i.e., if a run fails partway through in case of a system failure etc., re-running the experiment loads existing results and continues with the remaining experiments.

### Execution backend

`ForecastingBenchmark(backend="loky")` controls how jobs are parallelized. sktime currently parallelizes across CV folds; different backends provide different parallelization strategies. For different backends we support and the general API, please checkout out docs.

API docs: https://www.sktime.net/en/latest/api_reference/auto_generated/sktime.benchmarking.forecasting.ForecastingBenchmark.html

---

## Running your own benchmark on a Slurm cluster

1. Adapt `run_benchmark.py` (estimators, catalogues, splitters, output path) using the patterns above, you can either create a catalogue and then add it to the benchmark, or build your benchmark manually.
2. Update `pyproject.toml` with any extra dependencies your estimators or dataset loaders need, you can find the dependencies from the tags.
3. Adjust the `#SBATCH` resource requests in `benchmark.slurm` (memory, time, CPUs, partition).
4. Submit with `sbatch benchmark.slurm`.

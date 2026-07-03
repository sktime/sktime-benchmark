# Benchmarking with `sktime` on a Slurm Cluster

This repository demonstrates how to run time series benchmarking experiments using sktime on a Slurm-managed compute cluster. sktime provides a benchmarking framework that lets you define an experiment declaratively and execute it on anything from a laptop to an HPC cluster.

## What this repository demonstrates

* Running a forecasting benchmark on a Slurm cluster
* Using `ForecastingBenchmark`
* Using a reusable catalogue (M4CompetitionCatalogueYearly)
* Producing a results CSV
* Automatically setting up the Python environment on the compute node

The first few section talks about the benchmarking module itself and the later sections talk about the Slurm configurations.

## Repository structure

```
.
├── benchmark.slurm          # Slurm job script
├── run_benchmark.py         # Benchmark definition
├── logs/
│   ├── output.log
│   └── error.log
└── README.md
```

## Defining a benchmark

A benchmark in sktime consists of the following components:

* estimators
* datasets
* evaluation strategy
* metrics

Dataset, with an evaluation strategy and a metric forms a task. These components are assembled into a `ForecastingBenchmark`.

```python
from sktime.benchmarking.forecasting import ForecastingBenchmark

benchmark = ForecastingBenchmark(backend="loky")
```

The estimators and tasks are added to the instance of `ForecastingBenchmark`.

## Building a benchmark manually

Components of the benchmark can be added manually by the following methods:

* `add_estimtor` - For adding estimators
* `add_task` - For adding tasks
* `add` - Genral convenient wrapper over `add_estimator` and `add_task` which infers the scitype of the component and adds it to the benchmark

Please check this example notebook to see how to build a benchmark manually: https://www.sktime.net/en/latest/examples/04_benchmarking_forecasters.html

## Using catalogues

One of the features of the benchmarking framework in sktime is the concept of catalogues.

A catalogue is a reusable specification of an experiment. Rather than manually registering every estimator, dataset, metric, and configuration, a catalogue bundles these together into a single object which can be added directly to the benchmark. It is possible that a catalogue can be partial for reasons - we will see in the example below.

In this demonstration, we are going to use the `M4CompetitionCatalogueYearly` catalogue:

```python
from sktime.catalogues import M4CompetitionCatalogueYearly

catalogue = M4CompetitionCatalogueYearly()
benchmark.add(catalogue)
```

This immediately registers the components of the catalogue to the benchmark. `M4CompetitionCatalogueYearly` is a catalogue that comes shipped with `sktime`. It currently contains the statistical baselines used in the M4 competition, the M4 yearly dataset, and the metrics used in the original competition. You can create your own catalogues by inheriting from sktime's `BaseCatalogue`. Catalogues simply provide a convenient shortcut for commonly used benchmark configurations.

Read more about catalogues here: https://www.sktime.net/en/latest/api_reference/catalogues.html

## Configuring the evaluation strategy

The original M4 competition used pre-defined test train dataset files. In `sktime`, a task is incomplete without a specified CV strategy, so we are going to add a CV splitter to the benchmark as well. This could have been added to the catalogue as well, but since a splitter was not specified in the original competition, we leave it for the users to decide on.

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

## Running the benchmark

The benchmark is executed with
```
results = benchmark.run("./M4_competition_yearly_results.csv")
```
This evaluates every estimator on every task using the configured splitter and writes the results to `M4_competition_yearly_results.csv`. You can also save the results as JSON or Parquet. The result saving process is crash-safe, which means that in the event of a crash/failure, the results would not be lost and upon re-running the benchmark, it will load the existing results and complete running the remaining experiments.

## Execution backend

Remember we created benchmark with `ForecastingBenchmark(backend="loky")`. The backend determines how benchmark jobs are executed. Currently, `sktime` provides parallelisation across CV folds and these backends offer different ways to parallelize it.

Please check the documentation on `ForecastingBenchmark` to know more about backends offered and the full API: https://www.sktime.net/en/latest/api_reference/auto_generated/sktime.benchmarking.forecasting.ForecastingBenchmark.html

## Running on Slurm

This repository includes a Slurm submission script `benchmark.slurm`. Jobs on slurm can be submitted by `sbatch`.

```bash
sbatch benchmark.slurm
```

The script performs four steps:

* creates a virtual environment if one does not already exist
* activates the environment
* installs the project dependencies
* executes the benchmark and logs the error and output

The benchmark itself is completely independent of Slurm. Running locally is simply `python run_benchmark.py`. Slurm is responsible for scheduling and resource allocation of the job on the compute cluster.

## Monitoring the Slurm job

Once the job is submitted to the Slurm, it can be automatically run or can be queued if other jobs are in progress. You can check the status by `squeue -u $USER`.

To view the logs, do `tail -f logs/output.log` or `tail -f logs/error.log`.

## Running your own benchmark on a Slurm cluster

You can create your own benchmark using the steps demonstrated above. The Slurm configuration can be changed according to your needs, for example, you may want to increase or decrease the memory allocated to the job, or the maximum amount of time a job should run etc.

Depending on the estimators and dataset loaders you use, you will need to update `pyproject.toml` with the required dependencies.

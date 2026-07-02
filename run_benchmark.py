"""sktime Forecasting Leaderboard run on the cluster."""

from sktime.benchmarking.forecasting import ForecastingBenchmark
from catalogue.forecasting_catalogue import ForecastingCatalogue

benchmark = ForecastingBenchmark(backend="loky")

catalogue = ForecastingCatalogue()

forecasters = catalogue.get(object_type="forecaster", as_object=True)
dataset_loaders = catalogue.get(object_type="dataset", as_object=True)
scorers = catalogue.get(object_type="metric", as_object=True)
cv_splitter = catalogue.get(object_type="cv_splitter", as_object=True)  

for forecaster in forecasters:
    benchmark.add_estimator(forecaster)

for dataset_loader in dataset_loaders:
    for cv in cv_splitter:
        benchmark.add_task(
            dataset_loader,
            cv,
            scorers,
        )

results = benchmark.run("./forecasting_results.csv")
print(results)

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

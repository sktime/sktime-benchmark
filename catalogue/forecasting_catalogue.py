"""Catalogue for forecasting benchmarks."""

__author__ = ["jgyasu"]
__all__ = ["ForecastingCatalogue"]

from sktime.catalogues.base import BaseCatalogue


class ForecastingCatalogue(BaseCatalogue):
    """Curated catalogue for forecasting benchmarks.

    Contains a representative set of forecasting models:
    foundation models, and classical statistical approaches.
    """

    _tags = {
        "authors": ["jgyasu"],
        "maintainers": ["jgyasu"],
        "object_type": "catalogue",
        "n_items": 8,
        "info:name": "sktime Forecasting Catalogue",
        "info:description": (
            "Representative forecasting models for benchmarking."
        ),
        "info:source": "",
    }

    def _get(self):
        """Return catalogue contents."""
        return {
            "forecaster": [
                {"Naive": "NaiveForecaster(strategy='last')"},
                {"Theta": "ThetaForecaster()"},
                {"AutoETS": "AutoETS()"},
                {"AutoARIMA": "AutoARIMA()"},
            ],
            "dataset": ["ForecastingData('cif_2016_dataset')", "ForecastingData('hospital_dataset')"],
            "metric": ["MeanSquaredPercentageError()"],
            "cv_splitter": ["ExpandingWindowSplitter(initial_window=12, step_length=2, fh=6)"],
        }

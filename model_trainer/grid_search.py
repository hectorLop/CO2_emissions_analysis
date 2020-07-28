from abc import ABC, abstractmethod
from ..models.custom_estimators import ARIMAEstimator, ProphetEstimator
import pandas
import numpy
import itertools
import warnings
warnings.filterwarnings("ignore")

class GridSearch(ABC):
    """
    Abstract class to implement GridSearch for each model
    """

    @abstractmethod
    def grid_search(self) -> dict:
        """
        Fit abstract method to be implemented with custom keyword parameters
        in each estimator.
        """
        pass

class ARIMAGridSearch(GridSearch):
    """
    Grid Search for ARIMA model

    Attributes
    ----------
    _range_limit : int
        Limit number to create the parameter combinations

    _pdq : tuple
        Tuple containing (p, d, q) parameters for the non-seasonal part

    _seasonal_pdq : tuple
        Tuple containing (p, d, q)m parameters for the seasonal part
    """

    def __init__(self, range_limit: int) -> None:
        self._range_limit = range_limit
        self._pdq, self._seasonal_pdq = self.__generate_combinations_of_parameters()
    
    def __generate_combinations_of_parameters(self):
        """
        Generates the parameters combination for grid search
        """
        # Assign initial values for each parameter
        p = d = q = range(0, self._range_limit)

        # Generate all different combinations of p, d and q triplets
        pdq = list(itertools.product(p, d, q))

        # Generate all different combinations of seasonal p, q and q triplets
        seasonal_pdq = [(x[0], x[1], x[2], 2) for x in list(itertools.product(p, d, q))]

        return pdq, seasonal_pdq

    def grid_search(self, train_data: pandas.DataFrame, test_data: pandas.DataFrame) -> dict:
        """
        Apply grid search on ARIMA model

        Parameters
        ----------
        train_data : pandas.DataFrame
            DataFrame containing the training data

        test_data : pandas.DataFrame
            DataFrame containing the test data

        Returns
        -------
        results : dict
            Dictionary containing grid search results
        """
        # Best parameters variables
        min_mae = numpy.inf
        best_params = ()
        best_seasonal_params = ()

        for param in self._pdq:
            for seasonal_param in self._seasonal_pdq:
                model = ARIMAEstimator(order=param, seasonal_order=seasonal_param)

                results = model.fit(train_data)
        
                predictions = results.predict()
                #predictions.predicted_mean = scipy.special.inv_boxcox(predictions.predicted_mean, lam)
        
                mae = model.score(test_data.values, predictions.values)
        
                if mae < min_mae:
                    min_mae = mae
                    best_params = param
                    best_seasonal_params = seasonal_param

        results = {}
        results['MAE'] = min_mae
        results['Params'] = (best_params, best_seasonal_params)
        results['Name'] = 'ARIMA'

        return results
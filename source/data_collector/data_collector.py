from source.bbdd.db_connector import DBConnector
from source.bbdd.connectors import TimescaleConnector
from datetime import date, timedelta
import requests
import json
from typing import Dict, List
from pymongo.results import InsertOneResult

class DataCollector:
    """
    This class is responsible for obtaining the data and storing it in a database.
    TimescaleDB is the chosen database. 

    Attributes
    ----------
    _db_connector : DBConnector
        DBConnector object that handles the creation of the connection with the database and
        the inserting data
    """

    DB_INFO_PATH = 'source/bbdd/db_info.ini'
    ENDPOINT_URL = 'https://demanda.ree.es/WSvisionaMovilesPeninsulaRest/resources/demandaGeneracionPeninsula?fecha='
    CO2_EMISSIONS_FACTOR = {
        'aut': 0.27,
        'car': 0.95,
        'cc': 0.37,
        'cogenResto': 0.27,
        'gf': 0.7,
        'termRenov': 0.27
    }
    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self) -> None:
        # Initializes a DBConnector with a Timescale database
        self._db_connector = DBConnector(TimescaleConnector())
        self._db_connector.connect_to_db(self.DB_INFO_PATH)

    def insert_data(self, values: dict) -> None:
        """
        Inserts a new record in the database

        Parameters
        ----------
        values : dict
            Dictionary containing the data to be inserted
        """
        
        return self._db_connector.insert_data('emissions', values)

    def retrieve_last_two_hours(self) -> dict:
        """
        Retrieves data from the last two hours

        Returns
        -------
        document : dict
            Dictionary containing information about the emissions from the last two hours
        """
        # Generates the endpoint from which obtain the data
        previous_day_str = self._generate_previous_day_date()
        endpoint = self.ENDPOINT_URL + previous_day_str
        # Retrieves the data from the endpoint
        energy_data = self._retrieve_energy_data(endpoint)
        # Generates the emissions data from the energy_data
        emissions = self._generate_emissions(energy_data)
        
        return emissions

    def _generate_previous_day_date(self) -> str:
        """
        Generates the endpoint for the previous day data

        Returns
        -------
        endpoint : str
            Endpoint to retrieve the previous day data
        """
        today = date.today()
        previous_day = today - timedelta(days=1)
        previous_day_str = previous_day.strftime(self.DATE_FORMAT)

        return previous_day_str

    def _retrieve_energy_data(self, url: str) -> List[Dict]:
        """
        Retrieve the energy data from the last two hours

        Parameters
        ----------
        url : str
            String containing the endpoint url

        Returns
        -------
        json_data : list 
            List containing a dictionary for each observation
        """
        # Gets the raw data in json format
        page = requests.get(url)
        data = page.text

        # Cleans the data to leave only the json part
        data = data.replace('null({"valoresHorariosGeneracion":', '')
        data = data.replace('});', '')

        json_data = json.loads(data)

        # Returns the last 12 elements which are the last 2 hours due to the data
        # is in a 10 minutes time format
        return json_data[-12:]

    def _generate_emissions(self, json_data: List[Dict]) -> dict:
        """
        Generates a new dictionary which contains the emissions for each timestamp.
        The dictionary has the following format e.g :
        {
            '2020-08-27 21:00': 1000,
            '2020-08-27 21:10': 1200,
            ...
        }
        """
        emissions = {}

        for observation in json_data:
            timestamp = observation['ts']
            emissions[timestamp] = self._compute_emissions(observation)

        return emissions

    def _compute_emissions(self, observation: dict) -> float:
        """
        Compute the emissions generated in an observation

        Parameters
        ----------
        observation : dict
            Dictionary representing an observation in time. It includes
            the timestamp along with the energy generated by each type of energy

        Returns
        -------
        total_emissions : float
            Total sum of emissions for the observation
        """
        # List of energies which generate CO2 emissions
        polluting_energies = ['aut', 'car', 'cc', 'cogenResto', 'gf', 'termRenov']

        # List with the emissions for each energy
        emissions = [observation[energy] * self.CO2_EMISSIONS_FACTOR[energy] for energy in polluting_energies]
        # Get an unique emissions value
        total_emissions = sum(emissions)

        return total_emissions
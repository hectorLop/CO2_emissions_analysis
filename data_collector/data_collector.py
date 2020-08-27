from ..bbdd.db_connector import DBConnector
from ..bbdd.connectors import MongoConnector
from datetime import date, timedelta
import requests
import json

class DataCollector:
    """
    This class is responsible for obtaining the data and storing it in a database.
    MongoDB is the chosen database. 
    """

    DB_INFO_PATH = 'bbdd/db_info.ini'
    ENDPOINT_URL = 'https://demanda.ree.es/WSvisionaMovilesPeninsulaRest/resources/demandaGeneracionPeninsula?fecha='

    def __init__(self) -> None:
        self._connection = self._create_connection()

    def _create_connection(self) -> object:
        """
        Creates a connection with a database

        Returns
        -------
        connection : object
            Object which handles the connection to the database
        """
        # Initializes a DBConnector with a MongoConnector
        db_connector = DBConnector(MongoConnector())

        return db_connector.connect_to_db(self.DB_INFO_PATH)

    def retrieve_last_day(self) -> None:
        """
        Retrieves data from the previous day
        """
        endpoint = self._generate_endpoint

        data = self._retrieve_energy_data(endpoint)

    def _generate_endpoint(self) -> str:
        """
        Generates the endpoint for the previous day data

        Returns
        -------
        endpoint : str
            Endpoint to retrieve the previous day data
        """
        today = date.today()
        previous_day = today - timedelta(days=1)
        previous_day_str = previous_day.strftime('%Y-%m-%d')

        return self.ENDPOINT_URL + previous_day_str

    def _retrieve_energy_data(self, url: str) -> dict:
        """
        Retrieve all the text from a given url

        Parameters
        ----------
        url : str
            String containing the endpoint url

        Returns
        -------
        json_data : dict 
            Dictionary containing the json data
        """
        # Gets the raw data in json format
        page = requests.get(url)
        data = page.text

        # Cleans the data to leave only the json part
        data = data.replace('null({"valoresHorariosGeneracion":', '')
        data = data.replace('});', '')
        # Decodes the json
        json_data = json.loads(data)

        return json_data

    def insert_raw_data(self, data: dict) -> None:
        """
        Inserts a new record in the database

        Parameters
        ----------
        data : dict
            Dictionary containing the data to be stored
        """
        # Gets the collection which stores raw data
        collection = self._connection.raw_collector

        collection.insert_one(data)
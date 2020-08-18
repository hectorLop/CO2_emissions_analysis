from configparser import ConfigParser
from typing import Any, Tuple
import os
import boto3
import joblib
from io import BytesIO

class ModelRegistry:
    """
    This class represents a Model Registry to save models and have a log of it

    Parameters
    ----------
    connection : object
        Database session

    table_name : str
        Registry table name. Default is 'registry'

    Attributes
    ----------
    _connection : object
        Database session

    _table_name : str
        Registry table name
    """

    KEYS_FILENAME = 'aws_config.ini'

    def __init__(self, connection: object, table_name='registry') -> None:
        self._connection = connection
        self._table_name = table_name

    def _insert(self, values: tuple) -> None:
        """
        Inserts info to the database

        Parameters
        ----------
        values : tuple
            Tuple containing the values to be inserted
        """
        query = """
                INSERT INTO {}
                (name, model, parameters, metrics, remote_path, training_path, dataset)
                VALUES (?, ?, ?, ?, ?, ?, ?)""".format(self._table_name)
        self._query(query, values)

    def _query(self, query: str, values=None) -> None:
        """
        Makes a query to the database

        Parameters
        ----------
        query : str
            Query as a string

        values : tuple
            Tuple containing the query values. Default is None
        """
        cursor = self._connection.cursor()
        cursor.execute(query, values)
        cursor.close()
    
    def _read_aws_config(self) -> dict:
        """
        Gets the access and secret keys
        
        Returns
        -------
        access_key, secret_acces_key : tuple
            Tuple containing both keys as strings
        """
        # Gets the absolute path of the file containing the keys
        ini_path = os.path.join(os.getcwd(), self.KEYS_FILENAME)

        parser = ConfigParser()
        # Reads the config file
        parser.read(ini_path)

        return parser['settings']

    def _dump_model(self, model: object) -> BytesIO:
        """
        Dump a model into a in-memory buffer

        Parameters
        ----------
        model : object
            Trained model

        Returns
        -------
        buffer : BytesIO
            In-memory buffer containing the model data
        """
        with BytesIO() as buffer:
            # Dump the model into a buffer
            joblib.dump(model, buffer)
            # Sets the buffer stream at the start
            buffer.seek(0)

        return buffer

    def _upload_to_aws(self, access_key: str, secret_access_key: str, bucket: str,
                        model_data: BytesIO, remote_path : str) -> None:
        """
        Upload a file to a s3 bucket

        Parameters
        ----------
        model_data : BytesIO
            In-memory buffer containing the model data

        filename : str
            Desired filename of the model in the S3 bucket

        remote_path : str
            Destination file

        Returns
        -------
        uploaded : bool
            True if the file is uploaded succesfully
        """
        # Creates a client with the custom keys
        s3 = boto3.client('s3', aws_access_key_id=access_key,
                        aws_secret_access_key=secret_access_key)

        try:
            # Upload the model to a S3 bucket
            s3.upload_fileobj(Bucket=bucket, Key=remote_path, Fileobj=model_data)
        except FileNotFoundError:
            raise FileNotFoundError("The file was not found")

    def _save_to_remote(self, access_key: str, secret_access_key: str, 
                        remote_path: str, bucket: str, model: object) -> None:
        """
        Saves a model into a remote repository

        Parameters
        ----------
        filename : str
            Desired filename of the model in the remote repository
        
        model : object
            Trained model
        """
        model_data = self._dump_model(model)
        self._upload_to_aws(access_key, secret_access_key, bucket, model_data, remote_path)

    def publish_model(self, model: object, metrics: dict, training_time: float) -> None:
        """
        Publish a model into a remote repository

        Parameters
        ----------
        model : object
            Trained model

        metrics : dict
            Dictionary containing the model metrics

        training_time : float
            Time necessary to train the model
        """
        pass

    def get_model_info(self, name: str) -> str:
        pass 
import pymongo
import mysql.connector
from py2neo import Graph, NodeMatcher
import logging
import json
from datetime import datetime, timedelta
import pytz
import time
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, concat, datediff, current_date
from pyspark.sql.types import StructType, StructField, StringType, ArrayType

# Configuration - Using the exact connectors you provided
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"

# Multiple MongoDB databases with their respective connection details
MONGO_DATABASES = [
    {
        "name": "Person",
        "uri": "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/Person",
        "collections": ["person"]
    },
    {
        "name": "PrimaryApplicant", 
        "uri": "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/PrimaryApplicant",
        "collections": ["primary_applicant"]
    },
    {
        "name": "Loan",
        "uri": "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/Loan",
        "collections": ["loan"]
    }
]

# MySQL Connection Details
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "adi93066"

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class MongoDBConnector:
    def __init__(self, databases):
        """
        Initialize MongoDB connections for multiple databases
        """
        self.connections = {}
        self.databases = databases
        self._connect()
    
    def _connect(self):
        """
        Establish connections to all specified MongoDB databases
        """
        for db_config in self.databases:
            try:
                # Create MongoDB client
                client = pymongo.MongoClient(db_config['uri'])
                
                # Connect to specific database
                db = client[db_config['name']]
                
                # Store connection for each database
                self.connections[db_config['name']] = {
                    'client': client,
                    'database': db
                }
                
                logger.info(f"Connected to MongoDB database: {db_config['name']}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB database {db_config['name']}: {str(e)}")
    
    def get_collection(self, database_name, collection_name):
        """
        Retrieve a specific collection from a database
        """
        try:
            db_info = self.connections.get(database_name)
            if db_info:
                return db_info['database'][collection_name]
            else:
                logger.error(f"No connection found for database: {database_name}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving collection {collection_name} from {database_name}: {str(e)}")
            return None
    
    def close_connections(self):
        """
        Close all MongoDB connections
        """
        for db_name, db_info in self.connections.items():
            try:
                db_info['client'].close()
                logger.info(f"Closed connection to {db_name}")
            except Exception as e:
                logger.error(f"Error closing connection to {db_name}: {str(e)}")

class MySQLConnector:
    def __init__(self, host, port, user, password):
        """
        Initialize MySQL connection
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        self._connect()
    
    def _connect(self):
        """
        Establish MySQL connection
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("Successfully connected to MySQL")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
    
    def execute_query(self, query, params=None):
        """
        Execute a MySQL query
        """
        try:
            if not self.connection or not self.connection.is_connected():
                self._connect()
            
            self.cursor.execute(query, params or {})
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"MySQL query execution error: {str(e)}")
            return None
    
    def close_connection(self):
        """
        Close MySQL connection
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("MySQL connection closed")
        except Exception as e:
            logger.error(f"Error closing MySQL connection: {str(e)}")

class ETLPipeline:
    def __init__(self):
        # Initialize MongoDB Connector
        self.mongo_connector = MongoDBConnector(MONGO_DATABASES)
        
        # Initialize MySQL Connector
        self.mysql_connector = MySQLConnector(
            MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
        )
        
        # Initialize Spark Session
        self.spark = SparkSession.builder \
            .appName("MongoDB to Neo4j ETL Pipeline") \
            .config("spark.jars.packages", 
                    "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,"
                    "mysql:mysql-connector-java:8.0.26") \
            .getOrCreate()
        
        # Initialize Neo4j Connection
        self.neo4j_graph = Graph(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
    
    def extract_from_mongodb(self, database_config):
        """
        Extract data from specified MongoDB database and collection
        """
        try:
            # Get the collection using MongoDBConnector
            collection = self.mongo_connector.get_collection(
                database_config['name'], 
                database_config['collections'][0]
            )
            
            # Convert MongoDB cursor to list of dictionaries
            data = list(collection.find())
            
            # Convert to Spark DataFrame
            df = self.spark.createDataFrame(data)
            
            logger.info(f"Extracted {df.count()} records from {database_config['name']}")
            return df
        except Exception as e:
            logger.error(f"Error extracting from MongoDB: {str(e)}")
            return None
    
    def run_etl_pipeline(self):
        """
        Main ETL pipeline orchestrator
        """
        try:
            # Extract data from each MongoDB database
            extracted_data = {}
            for db_config in MONGO_DATABASES:
                df = self.extract_from_mongodb(db_config)
                if df:
                    extracted_data[db_config['name'].lower()] = df
            
            # You can add transformation and loading steps here
            
            logger.info("ETL Pipeline completed successfully!")
        
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
        finally:
            # Close all connections
            self.mongo_connector.close_connections()
            self.mysql_connector.close_connection()
            self.spark.stop()

# Main execution
if __name__ == "__main__":
    etl_pipeline = ETLPipeline()
    etl_pipeline.run_etl_pipeline()
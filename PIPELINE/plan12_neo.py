import logging
from pyspark.sql import SparkSession
from py2neo import Graph
import os
import findspark
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("neo4j_to_sql_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Find spark installation
findspark.init()

# Neo4j connection parameters
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"  # Replace with your actual password

# SQL Database connection parameters
SQL_CONNECTION_STRING = "mysql+pymysql://root:adi93066@localhost:3306/sql_sync"  # Replace with your SQL database connection string

def setup_spark():
    """Create and return a SparkSession"""
    try:
        spark = SparkSession.builder \
            .appName("Neo4j to SQL Data Sync") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Error creating Spark session: {str(e)}", exc_info=True)
        return None

def connect_to_neo4j():
    """Establish connection to Neo4j database"""
    try:
        graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        logger.info("Connected to Neo4j successfully")
        return graph
    except Exception as e:
        logger.error(f"Error connecting to Neo4j: {str(e)}", exc_info=True)
        return None

def create_sql_engine():
    """Create SQLAlchemy engine for SQL database connection"""
    try:
        engine = create_engine(SQL_CONNECTION_STRING)
        logger.info("SQL database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error creating SQL database engine: {str(e)}", exc_info=True)
        return None

def extract_nodes_from_neo4j(graph, label):
    """
    Extract all nodes of a specific label from Neo4j
    
    Args:
        graph (Graph): Neo4j graph connection
        label (str): Node label to extract (e.g., 'Person', 'Loan', 'Company')
    
    Returns:
        list of dictionaries representing nodes
    """
    try:
        # Cypher query to extract all nodes of a specific label
        query = f"MATCH (n:{label}) RETURN properties(n) AS properties"
        nodes = graph.run(query).data()
        
        # Convert to list of dictionaries
        node_dicts = [node['properties'] for node in nodes]
        
        logger.info(f"Extracted {len(node_dicts)} {label} nodes from Neo4j")
        return node_dicts
    except Exception as e:
        logger.error(f"Error extracting {label} nodes: {str(e)}")
        return []

def convert_to_spark_dataframe(spark, nodes):
    """
    Convert a list of node dictionaries to a Spark DataFrame
    
    Args:
        spark (SparkSession): Spark session
        nodes (list): List of node dictionaries
    
    Returns:
        Spark DataFrame
    """
    try:
        if not nodes:
            return spark.createDataFrame([])
        
        # Convert any nested dictionaries or lists to JSON strings
        processed_nodes = []
        for node in nodes:
            processed_node = {}
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    processed_node[k] = json.dumps(v)
                else:
                    processed_node[k] = v
            processed_nodes.append(processed_node)
        
        df = spark.createDataFrame(processed_nodes)
        return df
    except Exception as e:
        logger.error(f"Error converting nodes to Spark DataFrame: {str(e)}")
        return spark.createDataFrame([])

def write_to_sql(df, table_name, engine):
    """
    Write Spark DataFrame to SQL database
    
    Args:
        df (Spark DataFrame): DataFrame to write
        table_name (str): Target table name in SQL database
        engine (SQLAlchemy Engine): Database connection engine
    """
    try:
        # Convert Spark DataFrame to Pandas (for SQLAlchemy compatibility)
        pandas_df = df.toPandas()
        
        # Write to SQL, replace existing table
        pandas_df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        logger.info(f"Successfully wrote {len(pandas_df)} records to {table_name}")
    except Exception as e:
        logger.error(f"Error writing to SQL table {table_name}: {str(e)}")

def sync_neo4j_to_sql():
    """
    Main synchronization function to extract data from Neo4j and write to SQL
    """
    spark = setup_spark()
    graph = connect_to_neo4j()
    sql_engine = create_sql_engine()
    
    if not (spark and graph and sql_engine):
        logger.error("Failed to establish necessary connections")
        return False
    
    try:
        # Define node labels to extract
        node_labels = ['Person', 'Loan', 'Company']
        
        for label in node_labels:
            # Extract nodes from Neo4j
            nodes = extract_nodes_from_neo4j(graph, label)
            
            # Convert to Spark DataFrame
            df = convert_to_spark_dataframe(spark, nodes)
            
            # Write to SQL table
            write_to_sql(df, label.lower(), sql_engine)
        
        logger.info("Neo4j to SQL synchronization completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Synchronization error: {str(e)}")
        return False
    finally:
        # Always stop Spark session
        if spark:
            spark.stop()

if __name__ == "__main__":
    sync_neo4j_to_sql()
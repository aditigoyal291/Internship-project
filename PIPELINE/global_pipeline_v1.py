from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from py2neo import Graph
import os
import findspark
import logging
import json
from datetime import datetime, timedelta
import pytz
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_db_neo4j_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
findspark.init()

# Database Connection Parameters
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "Tester_mongo_flower"

MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "adi93066"

SYNC_MINUTES_LOOKBACK = 120000000

def setup_spark():
    """Create and return a SparkSession with MongoDB and MySQL connectors"""
    try:
        spark = SparkSession.builder \
            .appName("Multi-DB to Neo4j Pipeline") \
            .config("spark.jars.packages", 
                    "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,"
                    "mysql:mysql-connector-java:8.0.26") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Error creating Spark session: {str(e)}", exc_info=True)
        return None

def get_last_sync_timestamp():
    """Calculate a timestamp from SYNC_MINUTES_LOOKBACK minutes ago"""
    try:
        lookback_time = datetime.now(pytz.UTC) - timedelta(minutes=SYNC_MINUTES_LOOKBACK)
        timestamp = lookback_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        logger.info(f"Looking for updates since: {timestamp} ({SYNC_MINUTES_LOOKBACK} minutes ago)")
        return timestamp
    except Exception as e:
        logger.error(f"Error calculating sync timestamp: {str(e)}")
        return "1970-01-01T00:00:00.000+00:00"

def read_mongo_collection(spark, collection_name, last_sync_timestamp):
    """Read data from MongoDB collection with timestamp filter"""
    try:
        df = spark.read.format("mongo") \
            .option("uri", f"{MONGO_URI}{MONGO_DB_NAME}.{collection_name}") \
            .load()
        
        # Filter by timestamp
        filtered_df = df.filter(col("updatedAt") > last_sync_timestamp)
        
        logger.info(f"MongoDB {collection_name}: {filtered_df.count()} records found")
        return filtered_df
    except Exception as e:
        logger.error(f"Error reading MongoDB collection {collection_name}: {str(e)}")
        return spark.createDataFrame([], df.schema) if 'df' in locals() else None

def read_mysql_table(spark, table_name, last_sync_timestamp):
    """Read data from MySQL table with timestamp filter"""
    try:
        # Dynamically determine the database name based on table name
        database_map = {
            "Company": "Company",
            "Coapplicant": "Coapplicant",
            "Reference": "Reference"
        }
        database_name = database_map.get(table_name, table_name)
        
        jdbc_url = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{database_name}"
        
        df = spark.read.format("jdbc") \
            .option("url", jdbc_url) \
            .option("driver", "com.mysql.cj.jdbc.Driver") \
            .option("dbtable", table_name) \
            .option("user", MYSQL_USER) \
            .option("password", MYSQL_PASSWORD) \
            .load()
        
        # Filter by timestamp
        filtered_df = df.filter(col("updatedAt") > last_sync_timestamp)
        
        logger.info(f"MySQL {database_name}.{table_name}: {filtered_df.count()} records found")
        return filtered_df
    except Exception as e:
        logger.error(f"Error reading MySQL table {table_name}: {str(e)}")
        return spark.createDataFrame([], df.schema) if 'df' in locals() else None

def read_collections(spark, last_sync_timestamp):
    """Read data from all collections and tables"""
    try:
        # MongoDB Collections
        person_df = read_mongo_collection(spark, "Person", last_sync_timestamp)
        loan_df = read_mongo_collection(spark, "Loan", last_sync_timestamp)
        primary_applicant_df = read_mongo_collection(spark, "PrimaryApplicant", last_sync_timestamp)
        
        # MySQL Tables
        company_df = read_mysql_table(spark, "Company", last_sync_timestamp)
        coapplicant_df = read_mysql_table(spark, "Coapplicant", last_sync_timestamp)
        reference_df = read_mysql_table(spark, "Reference", last_sync_timestamp)
        
        return {
            "person": person_df,
            "loan": loan_df,
            "primary_applicant": primary_applicant_df,
            "company": company_df,
            "co_applicant": coapplicant_df,
            "reference": reference_df
        }
    except Exception as e:
        logger.error(f"Error reading collections: {str(e)}")
        raise e

def main_pipeline():
    spark = setup_spark()
    
    try:
        while True:
            # Get timestamp for incremental sync
            last_sync_timestamp = get_last_sync_timestamp()
            
            # Read data from all sources
            dataframes = read_collections(spark, last_sync_timestamp)
            
            # Check if any updates exist
            has_updates = any(df.count() > 0 for df in dataframes.values())
            
            if has_updates:
                logger.info("Updates found. Syncing to Neo4j...")
                # TODO: Implement Neo4j sync logic
            else:
                logger.info("No updates found.")
            
            # Wait for next sync interval
            time.sleep(SYNC_MINUTES_LOOKBACK * 60)
    
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main_pipeline()
import logging
import os
from datetime import datetime, timedelta
import pytz
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mysql_mongodb_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Configuration Constants
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "adi93066"
MYSQL_DATABASE = "MysqlDB"

MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DATABASE = "mysql_sync_db"

# Sync configuration
SYNC_MINUTES_LOOKBACK = 5

def setup_spark():
    """Create and return a SparkSession with MySQL and MongoDB connectors"""
    try:
        spark = SparkSession.builder \
            .appName("MySQL to MongoDB Pipeline") \
            .config("spark.jars.packages", 
                    "mysql:mysql-connector-java:8.0.26," + 
                    "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Error creating Spark session: {str(e)}", exc_info=True)
        return None

def get_mysql_connection_options():
    """Generate MySQL connection options"""
    return {
        "url": f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}",
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "driver": "com.mysql.cj.jdbc.Driver"
    }

def get_last_sync_timestamp():
    """Calculate a timestamp from SYNC_MINUTES_LOOKBACK minutes ago"""
    try:
        # Get current time and subtract minutes
        lookback_time = datetime.now(pytz.UTC) - timedelta(minutes=SYNC_MINUTES_LOOKBACK)
        timestamp = lookback_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Looking for updates since: {timestamp} ({SYNC_MINUTES_LOOKBACK} minutes ago)")
        return timestamp
    except Exception as e:
        logger.error(f"Error calculating sync timestamp: {str(e)}")
        return "1970-01-01 00:00:00"  # Fallback to epoch time

def identify_timestamp_columns(spark, table_name):
    """Attempt to identify timestamp columns in the table"""
    try:
        connection_options = get_mysql_connection_options()
        
        query = f"(SELECT * FROM {table_name} LIMIT 1) AS {table_name}_columns"
        
        df = spark.read.format("jdbc") \
            .option("url", connection_options["url"]) \
            .option("dbtable", query) \
            .option("user", connection_options["user"]) \
            .option("password", connection_options["password"]) \
            .option("driver", connection_options["driver"]) \
            .load()
        
        # Find potential timestamp columns
        timestamp_columns = [
            col for col in df.columns 
            if 'created_at' in col.lower() or 
               'updated_at' in col.lower() or 
               'timestamp' in col.lower()
        ]
        
        return timestamp_columns
    except Exception as e:
        logger.error(f"Error identifying timestamp columns for {table_name}: {str(e)}")
        return []

def read_mysql_table(spark, table_name, timestamp_column=None, last_sync_timestamp=None):
    """
    Read data from a MySQL table with flexible timestamp filtering
    """
    try:
        connection_options = get_mysql_connection_options()
        
        # Base query
        base_query = f"(SELECT * FROM {table_name}) AS {table_name}_subquery"
        
        # If a timestamp column exists and last_sync_timestamp is provided, add filtering
        if timestamp_column and last_sync_timestamp:
            base_query = f"""
            (SELECT * FROM {table_name} 
             WHERE {timestamp_column} > '{last_sync_timestamp}') 
            AS {table_name}_subquery
            """
        
        df = spark.read.format("jdbc") \
            .option("url", connection_options["url"]) \
            .option("dbtable", base_query) \
            .option("user", connection_options["user"]) \
            .option("password", connection_options["password"]) \
            .option("driver", connection_options["driver"]) \
            .load()
        
        count = df.count()
        logger.info(f"Read {count} records from {table_name}")
        
        return df
    except Exception as e:
        logger.error(f"Error reading MySQL table {table_name}: {str(e)}")
        return None

def write_to_mongodb(df, collection_name):
    """Write DataFrame to MongoDB collection"""
    try:
        df.write.format("mongo") \
            .option("uri", f"{MONGODB_URI}{MONGODB_DATABASE}") \
            .option("collection", collection_name) \
            .mode("append") \
            .save()
        
        logger.info(f"Successfully wrote {df.count()} records to {collection_name}")
    except Exception as e:
        logger.error(f"Error writing to MongoDB collection {collection_name}: {str(e)}")

def run_pipeline(spark):
    """Execute the full data synchronization pipeline"""
    try:
        # Get last sync timestamp
        last_sync_timestamp = get_last_sync_timestamp()
        
        # List of tables to sync
        tables_to_sync = [
            "coapplicants",
            "companies", 
            "loans", 
            "persons", 
            "primary_applicants", 
            "references"
        ]
        
        # Track if any updates occurred
        updates_made = False
        
        # Sync each table
        for table in tables_to_sync:
            # Identify timestamp columns
            timestamp_columns = identify_timestamp_columns(spark, table)
            
            if not timestamp_columns:
                logger.warning(f"No timestamp column found for {table}. Skipping.")
                continue
            
            # Use the first identified timestamp column
            timestamp_column = timestamp_columns[0]
            
            # Read from MySQL
            mysql_df = read_mysql_table(spark, table, timestamp_column, last_sync_timestamp)
            
            if mysql_df and mysql_df.count() > 0:
                # Write to MongoDB
                write_to_mongodb(mysql_df, table)
                updates_made = True
        
        return updates_made
    
    except Exception as e:
        logger.error(f"Pipeline execution error: {str(e)}", exc_info=True)
        return False

def format_time_until_next_run(minutes):
    """Format the waiting time in a human-readable way"""
    if minutes < 1:
        return "less than a minute"
    elif minutes == 1:
        return "1 minute"
    else:
        return f"{minutes} minutes"

def main():
    """Main execution method with continuous running"""
    spark = setup_spark()
    
    if not spark:
        logger.error("Failed to create Spark session. Exiting.")
        return
    
    try:
        while True:
            logger.info("Starting pipeline run...")
            updates_made = run_pipeline(spark)
            
            next_run_time = datetime.now() + timedelta(minutes=SYNC_MINUTES_LOOKBACK)
            formatted_time = next_run_time.strftime("%H:%M:%S")
            time_until = format_time_until_next_run(SYNC_MINUTES_LOOKBACK)
            
            if updates_made:
                logger.info(f"Pipeline completed with updates. Next run in {time_until} at {formatted_time}.")
                print(f"Pipeline completed with updates. Next run in {time_until} at {formatted_time}.")
            else:
                logger.info(f"Nothing to update. Waiting for {time_until} until next run at {formatted_time}.")
                print(f"Nothing to update. Waiting for {time_until} until next run at {formatted_time}.")
            
            # Sleep for the same amount of time as the lookback period
            time.sleep(SYNC_MINUTES_LOOKBACK * 60)
    
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline execution error: {str(e)}", exc_info=True)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
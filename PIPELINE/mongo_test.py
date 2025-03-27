from pyspark.sql import SparkSession
import logging
import sys

# Enhanced logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_mongo_connection():
    try:
        # More verbose Spark session configuration
        spark = SparkSession.builder \
            .appName("MongoDB Connection Comprehensive Debug") \
            .config("spark.jars.packages", 
                "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1," + 
                "org.mongodb:mongodb-driver:3.12.10," + 
                "org.mongodb:mongodb-driver-core:3.12.10") \
            .config("spark.driver.extraClassPath", "/path/to/mongo-spark-connector.jar") \
            .config("spark.executor.extraClassPath", "/path/to/mongo-spark-connector.jar") \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.mongodb.input.uri", "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/Person") \
            .master("local[*]") \
            .getOrCreate()
        
        # Print Spark and connector versions for debugging
        print("Spark Version:", spark.version)
        print("Python Version:", sys.version)
        
        # Attempt to read from different collections to isolate the issue
        collections_to_try = ['Person', 'Loan', 'Plan5', 'PrimaryApplicant']
        
        for collection in collections_to_try:
            try:
                print(f"\nTrying to read collection: {collection}")
                df = spark.read.format("mongodb") \
                    .option("database", "Person") \
                    .option("collection", collection) \
                    .option("uri", "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/Person") \
                    .load()
                
                print(f"DataFrame Schema for {collection}:")
                df.printSchema()
                
                print(f"\nTotal Records in {collection}: {df.count()}")
                
            except Exception as collection_error:
                logger.error(f"Error reading collection {collection}: {str(collection_error)}", exc_info=True)
        
    except Exception as e:
        logger.error(f"Detailed Connection Error: {str(e)}", exc_info=True)
    finally:
        spark.stop()

if __name__ == "__main__":
    debug_mongo_connection()
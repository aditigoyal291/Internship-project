import logging
import json
from datetime import datetime, timedelta
import pytz
import time

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from py2neo import Graph
import findspark

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_neo4j_loan_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
findspark.init()

# Configuration
MONGO_URI = "mongodb+srv://chinthanamj:Contact1234@cluster0.dttff.mongodb.net/"
DB_NAME = "Loan"
COLLECTION_NAME = "loan"
SYNC_MINUTES_LOOKBACK = 5


def setup_spark():
    """Create and return a SparkSession with MongoDB connector"""
    try:
        spark = SparkSession.builder \
            .appName("MongoDB Atlas to Neo4j Loan Pipeline") \
            .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
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


def is_neo4j_empty(graph):
    """Check if Neo4j database is empty"""
    try:
        loan_count = graph.run("MATCH (l:Loan) RETURN count(l) as count").data()[0]['count']
        logger.info(f"Neo4j database has {loan_count} Loan nodes")
        return loan_count == 0
    except Exception as e:
        logger.error(f"Error checking if Neo4j is empty: {str(e)}")
        return False


def create_constraints(graph):
    """Create constraints for unique Loan IDs"""
    try:
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Loan) REQUIRE l.loanId IS UNIQUE")
        logger.info("Neo4j constraints created")
    except Exception as e:
        logger.error(f"Error creating constraints: {str(e)}")


def sanitize_value(value):
    """Sanitize complex values for Neo4j storage"""
    if isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list):
        return json.dumps(value)
    return value


def read_collection(spark, last_sync_timestamp):
    """Read loan data from MongoDB collection"""
    try:
        df = spark.read.format("mongo") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{COLLECTION_NAME}") \
            .load()

        # Filter by updatedAt timestamp
        df_filtered = df.filter(col("updatedAt") > last_sync_timestamp)

        count = df_filtered.count()
        logger.info(f"Found {count} records updated after {last_sync_timestamp}")

        return df_filtered
    except Exception as e:
        logger.error(f"Error reading collection: {str(e)}")
        return None


def upsert_loans(graph, loans):
    """Upsert loan nodes and their relationships"""
    latest_timestamp = None

    for row in loans.collect():
        try:
            # Convert Row to dictionary and sanitize values
            loan_data = {k: sanitize_value(v) for k, v in row.asDict().items()}

            # Track latest timestamp
            current_timestamp = loan_data.get("updatedAt")
            if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
                latest_timestamp = current_timestamp

            # Upsert Loan Node
            graph.run("""
            MERGE (l:Loan {loanId: $loanId})
            SET l += $properties
            """, loanId=loan_data.get('loanId'), properties=loan_data)

            # Create relationships
            # Primary Applicant Relationship
            if loan_data.get('primaryApplicantId'):
                graph.run("""
                MATCH (l:Loan {loanId: $loanId})
                MERGE (p:Person {personId: $personId})
                MERGE (p)-[:PRIMARY_APPLICANT]->(l)
                """, loanId=loan_data.get('loanId'), personId=loan_data.get('primaryApplicantId'))

            # Co-applicant Relationship
            if loan_data.get('coapplicantId'):
                graph.run("""
                MATCH (l:Loan {loanId: $loanId})
                MERGE (c:Person {personId: $personId})
                MERGE (l)-[:HAS_COAPPLICANT]->(c)
                """, loanId=loan_data.get('loanId'), personId=loan_data.get('coapplicantId'))

            # References Relationships
            references = loan_data.get('references', [])
            if isinstance(references, str):
                references = json.loads(references)

            for ref_id in references:
                graph.run("""
                MATCH (l:Loan {loanId: $loanId})
                MERGE (r:Person {personId: $personId})
                MERGE (l)-[:HAS_REFERENCE]->(r)
                """, loanId=loan_data.get('loanId'), personId=ref_id)

            logger.info(f"Upserted Loan node with ID: {loan_data.get('loanId')}")

        except Exception as e:
            logger.error(f"Error upserting loan: {str(e)}")

    return latest_timestamp


def run_pipeline(spark, graph):
    """Main pipeline execution"""
    try:
        # Create constraints
        create_constraints(graph)

        # Determine sync approach based on DB state
        if is_neo4j_empty(graph):
            logger.info("Neo4j is empty. Performing full sync...")
            df = spark.read.format("mongo") \
                .option("uri", f"{MONGO_URI}{DB_NAME}.{COLLECTION_NAME}") \
                .load()
        else:
            # Incremental sync
            last_sync_timestamp = get_last_sync_timestamp()
            df = read_collection(spark, last_sync_timestamp)

        # Check if there are any records to sync
        if df is None or df.count() == 0:
            logger.info("No records to sync.")
            return False

        # Upsert loans and track latest timestamp
        latest_timestamp = upsert_loans(graph, df)

        # Log sync completion
        if latest_timestamp:
            logger.info(f"Sync completed. Latest timestamp: {latest_timestamp}")
        else:
            logger.info("Sync completed without tracking timestamp.")

        return True

    except Exception as e:
        logger.error(f"Pipeline execution error: {str(e)}", exc_info=True)
        return False


def main():
    # Neo4j connection - replace with your credentials
    graph = Graph("bolt://localhost:7687",
                  auth=("neo4j", "password"))

    # Create Spark session
    spark = setup_spark()

    try:
        while True:
            logger.info("Starting pipeline run...")
            updates_made = run_pipeline(spark, graph)

            # Wait for next sync
            wait_time = SYNC_MINUTES_LOOKBACK * 60
            logger.info(f"Waiting {wait_time} seconds until next sync...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        if spark:
            spark.stop()


if __name__ == "__main__":
    main()
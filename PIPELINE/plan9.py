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
        logging.FileHandler("mongodb_neo4j_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
# Find spark installation
findspark.init()

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Tester_mongo_flower"
SYNC_MINUTES_LOOKBACK = 120000000

def setup_spark():
    """Create and return a SparkSession with MongoDB connector"""
    try:
        spark = SparkSession.builder \
            .appName("MongoDB Atlas to Neo4j Pipeline") \
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
        # Get current time and subtract minutes
        lookback_time = datetime.now(pytz.UTC) - timedelta(minutes=SYNC_MINUTES_LOOKBACK)
        # timestamp = lookback_time.isoformat()
        timestamp = lookback_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        logger.info(f"Looking for updates since: {timestamp} ({SYNC_MINUTES_LOOKBACK} minutes ago)")
        return timestamp
    except Exception as e:
        logger.error(f"Error calculating sync timestamp: {str(e)}")
        return "1970-01-01T00:00:00.000+00:00"  # Fallback to epoch time
def debug_mongo_timestamps(collection_name):
    """Print sample timestamps from MongoDB to debug format issues"""
    try:
        sample_df = spark.read.format("mongo") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{collection_name}") \
            .load()
        
        if sample_df.count() > 0:
            logger.info(f"Sample timestamps from {collection_name}:")
            sample_df.select("updatedAt").show(3, truncate=False)
            # Get the timestamp format
            sample_timestamp = sample_df.select("updatedAt").first()
            if sample_timestamp:
                logger.info(f"Example timestamp format: {sample_timestamp[0]}")
                logger.info(f"Timestamp type: {type(sample_timestamp[0])}")
    except Exception as e:
        logger.error(f"Error debugging timestamps: {str(e)}")

def is_neo4j_empty():
    """Check if Neo4j database is empty (has no Person, Loan, or Company nodes)"""
    try:
        # Count nodes of each main type
        person_count = graph.run("MATCH (p:Person) RETURN count(p) as count").data()[0]['count']
        loan_count = graph.run("MATCH (l:Loan) RETURN count(l) as count").data()[0]['count']
        company_count = graph.run("MATCH (c:Company) RETURN count(c) as count").data()[0]['count']
        
        total_count = person_count + loan_count + company_count
        logger.info(f"Neo4j database has {total_count} nodes (Person: {person_count}, Loan: {loan_count}, Company: {company_count})")
        
        return total_count == 0
    except Exception as e:
        logger.error(f"Error checking if Neo4j is empty: {str(e)}")
        # Assume not empty on error to be safe
        return False

spark = setup_spark()
# Neo4j connection
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))  # Update with your Neo4j credentials

# Create constraints for unique IDs if they don't exist yet
def create_constraints():
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.personId IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Loan) REQUIRE l.loanId IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE")
    logger.info("Neo4j constraints created or confirmed")

def read_all_collection(collection_name):
    """Read all data from MongoDB collection regardless of timestamp"""
    try:
        df = spark.read.format("mongo") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{collection_name}") \
            .load()
        
        count = df.count()
        logger.info(f"Read all {count} records from {collection_name}")
        
        return df
    except Exception as e:
        logger.error(f"Error reading collection {collection_name}: {str(e)}")
        return None
    
def read_all_collections():
        """Read all collections without timestamp filter for full sync"""
        try:
            person_df = read_all_collection("Person")
            company_df = read_all_collection("Company")
            loan_df = read_all_collection("Loan")
            primary_applicant_df = read_all_collection("PrimaryApplicant")
            co_applicant_df = read_all_collection("Coapplicant")
            reference_df = read_all_collection("Reference")

            # Register DataFrames as temporary views
            person_df.createOrReplaceTempView("person")
            company_df.createOrReplaceTempView("company")
            loan_df.createOrReplaceTempView("loan")
            primary_applicant_df.createOrReplaceTempView("primary_applicant")
            co_applicant_df.createOrReplaceTempView("co_applicant")
            reference_df.createOrReplaceTempView("reference")
            
            return {
                "person": person_df,
                "company": company_df,
                "loan": loan_df,
                "primary_applicant": primary_applicant_df,
                "co_applicant": co_applicant_df,
                "reference": reference_df
            }
        except Exception as e:
            logger.error(f"Error reading all collections: {str(e)}")
            raise e


# Read data from MongoDB Atlas with timestamp filter
def read_collection(collection_name, last_sync_timestamp):
    """Read data from MongoDB collection that was updated after the last sync timestamp"""
    # Debug the timestamp format
    logger.info(f"Filtering {collection_name} for records updated after: {last_sync_timestamp}")
    
    try:
        # First, load without filter to check if there's any data at all
        all_df = spark.read.format("mongo") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{collection_name}") \
            .load()
        
        total_count = all_df.count()
        logger.info(f"Total records in {collection_name}: {total_count}")
        
        # Convert timestamp string to datetime for proper comparison
        timestamp_obj = datetime.fromisoformat(last_sync_timestamp.replace('Z', '+00:00'))
        
        # Use Spark SQL filter instead of MongoDB pipeline for better compatibility
        df = all_df.filter(col("updatedAt") > last_sync_timestamp)
        filtered_count = df.count()
        
        logger.info(f"Found {filtered_count} records in {collection_name} updated after {last_sync_timestamp}")
        
        # Show sample data for debugging
        if filtered_count > 0:
            logger.info(f"Sample record from {collection_name}:")
            df.select("updatedAt").show(1, truncate=False)
        
        return df
    except Exception as e:
        logger.error(f"Error reading collection {collection_name}: {str(e)}")
        # Return empty dataframe on error
        return spark.createDataFrame([], all_df.schema) if 'all_df' in locals() and all_df.schema else None
# Helper function to convert Row to dictionary safely
def row_to_dict(row):
    if row is None:
        return {}
    
    # First convert Row to dictionary
    if hasattr(row, "asDict"):
        d = row.asDict()
    elif isinstance(row, dict):
        d = row
    else:
        d = dict(row)  # Try direct conversion
    
    # Then sanitize the values
    result = {}
    for k, v in d.items():
        if v is None:
            continue
        elif isinstance(v, (dict, list)):
            result[k] = json.dumps(v)  # Convert complex objects to JSON strings
        elif hasattr(v, "asDict"):  # Handle nested Row objects
            result[k] = json.dumps(row_to_dict(v))
        else:
            result[k] = v
    
    return result

# Read all collections with timestamp filter
def read_filtered_collections(last_sync_timestamp):
    try:
        person_df = read_collection("Person", last_sync_timestamp)
        company_df = read_collection("Company", last_sync_timestamp)
        loan_df = read_collection("Loan", last_sync_timestamp)
        primary_applicant_df = read_collection("PrimaryApplicant", last_sync_timestamp)
        co_applicant_df = read_collection("Coapplicant", last_sync_timestamp)
        reference_df = read_collection("Reference", last_sync_timestamp)

        # Register DataFrames as temporary views
        person_df.createOrReplaceTempView("person")
        company_df.createOrReplaceTempView("company")
        loan_df.createOrReplaceTempView("loan")
        primary_applicant_df.createOrReplaceTempView("primary_applicant")
        co_applicant_df.createOrReplaceTempView("co_applicant")
        reference_df.createOrReplaceTempView("reference")
        
        # Print schema for debugging
        logger.info("Collection schemas:")
        logger.info("Primary Applicant schema:")
        primary_applicant_df.printSchema()
        logger.info("Co-applicant schema:")
        co_applicant_df.printSchema()
        logger.info("Reference schema:")
        reference_df.printSchema()
        
        return {
            "person": person_df,
            "company": company_df,
            "loan": loan_df,
            "primary_applicant": primary_applicant_df,
            "co_applicant": co_applicant_df,
            "reference": reference_df
        }
    except Exception as e:
        logger.error(f"Error reading collections: {str(e)}")
        raise e

# Process and upsert nodes
def upsert_nodes(dataframes):
    # Get the latest updatedAt timestamp to save after sync completes
    latest_timestamp = None
    
    # Upsert Person nodes
    persons = dataframes["person"].collect()
    for row_person in persons:
        properties = row_to_dict(row_person)
        person_id = properties.get("personId", "")
        
        # Track latest timestamp
        current_timestamp = properties.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not person_id:  # Skip records with missing ID
            logger.warning("Skipping Person record with missing personId")
            continue
            
        # Check if this person is a primary applicant - convert to Python primitive immediately
        is_primary_row = spark.sql(f"""
            SELECT COUNT(*) as count FROM primary_applicant 
            WHERE personId = '{person_id}'
        """).first()
        is_primary = int(row_to_dict(is_primary_row).get("count", 0)) > 0
        
        # Check if this person is a co-applicant
        is_coapplicant_row = spark.sql(f"""
            SELECT COUNT(*) as count FROM co_applicant 
            WHERE personId = '{person_id}'
        """).first()
        is_coapplicant = int(row_to_dict(is_coapplicant_row).get("count", 0)) > 0
        
        # Check if this person is a reference
        is_reference_row = spark.sql(f"""
            SELECT COUNT(*) as count FROM reference 
            WHERE personId = '{person_id}'
        """).first()
        is_reference = int(row_to_dict(is_reference_row).get("count", 0)) > 0
        
        # First MERGE on just the Person label and personId
        query = """
        MERGE (p:Person {personId: $personId})
        SET p += $properties
        """

        # Then add the role labels in separate operations
        if is_primary:
            query += "\nSET p:PrimaryApplicant"
        if is_coapplicant:
            query += "\nSET p:CoApplicant"
        if is_reference:
            query += "\nSET p:Reference" 

        # Remove labels that no longer apply (optional)
        if not is_primary:
            query += "\nREMOVE p:PrimaryApplicant"
        if not is_coapplicant:
            query += "\nREMOVE p:CoApplicant"
        if not is_reference:
            query += "\nREMOVE p:Reference"
            
        try:
            graph.run(query, personId=person_id, properties=properties)
            logger.info(f"Upserted Person node with ID: {person_id}")
        except Exception as e:
            logger.error(f"Error upserting Person node: {str(e)}")
            logger.debug(f"Properties: {properties}")
        
    # Upsert Loan nodes
    loans = dataframes["loan"].collect()
    for row_loan in loans:
        properties = row_to_dict(row_loan)
        loan_id = properties.get("loanId", "")
        
        # Track latest timestamp
        current_timestamp = properties.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not loan_id:  # Skip records with missing ID
            logger.warning("Skipping Loan record with missing loanId")
            continue
            
        try:
            graph.run("""
            MERGE (l:Loan {loanId: $loanId})
            SET l += $properties
            """, loanId=loan_id, properties=properties)
            logger.info(f"Upserted Loan node with ID: {loan_id}")
        except Exception as e:
            logger.error(f"Error upserting Loan node: {str(e)}")
    
    # Upsert Company nodes
    companies = dataframes["company"].collect()
    for row_company in companies:
        properties = row_to_dict(row_company)
        company_id = properties.get("companyId", "")
        
        # Track latest timestamp
        current_timestamp = properties.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not company_id:  # Skip records with missing ID
            logger.warning("Skipping Company record with missing companyId")
            continue
            
        try:
            graph.run("""
            MERGE (c:Company {companyId: $companyId})
            SET c += $properties
            """, companyId=company_id, properties=properties)
            logger.info(f"Upserted Company node with ID: {company_id}")
        except Exception as e:
            logger.error(f"Error upserting Company node: {str(e)}")
    
    return latest_timestamp

def ensure_pan_mapping(dataframes):
    """
    Make sure PAN numbers are properly mapped in Neo4j for searching
    This function should be called after upsert_nodes() and before upsert_relationships()
    """
    logger.info("Ensuring PAN numbers are properly mapped...")
    
    # Get all Person nodes with PAN numbers that were updated
    persons = dataframes["person"].select("personId", "pan").collect()
    
    for row in persons:
        person_id = row["personId"]
        pan = row["pan"]
        
        if not person_id or not pan:
            continue
            
        try:
            # Update the Person node to ensure PAN is set as a queryable property
            graph.run("""
            MATCH (p:Person {personId: $personId})
            SET p.pan = $pan
            """, personId=person_id, pan=pan)
        except Exception as e:
            logger.error(f"Error updating PAN for person {person_id}: {str(e)}")
    
    # Create index on PAN for faster lookups (will be ignored if already exists)
    try:
        graph.run("CREATE INDEX ON :Person(pan)")
        logger.info("Index created on Person.pan")
    except Exception as e:
        # Index might already exist
        logger.warning(f"Note when creating PAN index: {str(e)}")

# Upsert relationships
def upsert_relationships(dataframes):
    latest_timestamp = None
    
    # Process primary applicants and their loans using the loans array
    primary_applicants = dataframes["primary_applicant"].collect()
    
    for row in primary_applicants:
        record = row_to_dict(row)
        person_id = record.get('personId')
        
        # Track latest timestamp
        current_timestamp = record.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not person_id:
            continue
            
        # Extract loans array from JSON string
        loans_str = record.get('loans', '[]')
        try:
            loans = json.loads(loans_str)
            if not isinstance(loans, list):
                loans = [loans]  # Convert to list if it's a single value
                
            for loan_id in loans:
                if not loan_id:  # Skip empty loan IDs
                    continue
                    
                try:
                    # Create or update HAS_LOAN relationship
                    graph.run("""
                    MATCH (p:Person {personId: $personId})
                    MATCH (l:Loan {loanId: $loanId})
                    MERGE (p)-[:HAS_LOAN]->(l)
                    """, personId=person_id, loanId=loan_id)
                    logger.info(f"Upserted HAS_LOAN relationship: Person {person_id} -> Loan {loan_id}")
                except Exception as e:
                    logger.error(f"Error upserting HAS_LOAN relationship: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing loans array for primary applicant {person_id}: {e}")
    
    # Process co-applicants
    co_applicants = dataframes["co_applicant"].collect()
    
    for row in co_applicants:
        record = row_to_dict(row)
        loan_id = record.get('loanId')
        person_id = record.get('personId')
        
        # Track latest timestamp
        current_timestamp = record.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not loan_id or not person_id:
            continue
            
        try:
            graph.run("""
            MATCH (l:Loan {loanId: $loanId})
            MATCH (p:Person {personId: $personId})
            MERGE (l)-[:HAS_COAPPLICANT]->(p)
            """, loanId=loan_id, personId=person_id)
            logger.info(f"Upserted HAS_COAPPLICANT relationship: Loan {loan_id} -> Person {person_id}")
        except Exception as e:
            logger.error(f"Error upserting HAS_COAPPLICANT relationship: {str(e)}")
    
    # Process references
    references = dataframes["reference"].collect()
    
    for row in references:
        record = row_to_dict(row)
        loan_id = record.get('loanId')
        person_id = record.get('personId')
        
        # Track latest timestamp
        current_timestamp = record.get("updatedAt")
        if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
            latest_timestamp = current_timestamp
        
        if not loan_id or not person_id:
            continue
            
        try:
            graph.run("""
            MATCH (l:Loan {loanId: $loanId})
            MATCH (p:Person {personId: $personId})
            MERGE (l)-[:HAS_REFERENCE]->(p)
            """, loanId=loan_id, personId=person_id)
            logger.info(f"Upserted HAS_REFERENCE relationship: Loan {loan_id} -> Person {person_id}")
        except Exception as e:
            logger.error(f"Error upserting HAS_REFERENCE relationship: {str(e)}")
    
    # Person to Company relationships (WORKS_IN)
    persons = dataframes["person"].collect()
    
    for row in persons:
        record = row_to_dict(row)
        person_id = record.get('personId')
        company_id = record.get('companyId')
        
        if not person_id or not company_id:
            continue
            
        try:
            graph.run("""
            MATCH (p:Person {personId: $personId})
            MATCH (c:Company {companyId: $companyId})
            MERGE (p)-[:WORKS_IN]->(c)
            """, personId=person_id, companyId=company_id)
            logger.info(f"Upserted WORKS_IN relationship: Person {person_id} -> Company {company_id}")
        except Exception as e:
            logger.error(f"Error upserting WORKS_IN relationship: {str(e)}")
    
    return latest_timestamp
def save_sync_timestamp(timestamp=None):
    """Save the current timestamp as the last sync time"""
    try:
        if timestamp is None:
            # Current time in ISO format with timezone
            timestamp = datetime.now(pytz.UTC).isoformat()
        
        # Log the timestamp instead of saving to file
        logger.info(f"Completed sync at timestamp: {timestamp}")
        
        # No actual file writing occurs - we're using the minutes-based approach
    except Exception as e:
        logger.error(f"Error processing sync timestamp: {str(e)}")


def run_pipeline():
        try:
        # Create Neo4j constraints if they don't exist
            create_constraints()

            # Check if Neo4j is empty
            if is_neo4j_empty():
                logger.info("Neo4j database appears to be empty. Performing full sync...")
                
                # Read alldata from MongoDB
                dataframes = read_all_collections()
                
                logger.info("Starting full data sync to Neo4j...")
            else:
                # Normal incremental sync
                debug_mongo_timestamps("Person")
                
                # Get the last sync timestamp
                last_sync_timestamp = get_last_sync_timestamp()
                logger.info(f"Starting incremental sync for data updated after: {last_sync_timestamp}")
                
                # Read data from MongoDB that has been updated since the last sync
                dataframes = read_filtered_collections(last_sync_timestamp)
            
            # If any collection has no updates, log and continue
            has_updates = False
            for collection, df in dataframes.items():
                count = df.count()
                logger.info(f"Collection {collection}: {count} records to sync")
                if count > 0:
                    has_updates = True
            
            if not has_updates:
                logger.info("No updates found. Nothing to update, waiting for next run.")
                return False
            
            # Upsert nodes and track the latest timestamp
            logger.info("Upserting nodes...")
            node_latest_timestamp = upsert_nodes(dataframes)
            
            logger.info("Ensuring PAN mapping...")
            ensure_pan_mapping(dataframes)
            
            logger.info("Upserting relationships...")
            rel_latest_timestamp = upsert_relationships(dataframes)
            
            # Determine the latest timestamp overall
            latest_timestamp = node_latest_timestamp
            if rel_latest_timestamp and (not latest_timestamp or rel_latest_timestamp > latest_timestamp):
                latest_timestamp = rel_latest_timestamp
            
            # Save the latest timestamp for next sync
            if latest_timestamp:
                save_sync_timestamp(latest_timestamp)
            else:
                save_sync_timestamp()  # Use current time if no timestamp found
            
            logger.info("Pipeline completed successfully!")
            return True
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

if __name__ == "__main__":
    try:
        while True:
            logger.info("Starting pipeline run...")
            updates_made = run_pipeline()
            
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
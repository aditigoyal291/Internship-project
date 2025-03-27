from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from py2neo import Graph
import os
import findspark
import logging
import json
import traceback
import sys
from datetime import datetime, timedelta
import pytz
import time
from typing import Optional, Dict, Any
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Enhanced Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_db_neo4j_sync.log"),
        logging.FileHandler("neo4j_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
findspark.init()

# Database Connection Parameters
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

MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "adi93066"

SYNC_MINUTES_LOOKBACK = 120000000

def debug_neo4j_connection(uri, username, password):
    """
    Comprehensive Neo4j connection debugging function
    
    Args:
        uri (str): Neo4j connection URI
        username (str): Neo4j username
        password (str): Neo4j password
    
    Returns:
        py2neo.Graph: Connected graph object or None
    """
    try:
        # Detailed connection logging
        logger.info(f"Attempting to connect to Neo4j at: {uri}")
        logger.info(f"Username used: {username}")
        
        # Create graph connection
        graph = Graph(uri, auth=(username, password))
        
        # Test connection with a simple query
        test_query = "RETURN 1 as test"
        result = graph.run(test_query)
        
        # Check if test query works
        test_value = list(result)[0]['test']
        if test_value == 1:
            logger.info("Neo4j connection successful!")
            return graph
        else:
            logger.error("Test query failed unexpectedly")
            return None
    
    except Exception as e:
        logger.error("Neo4j Connection Error:")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}")
        logger.error("Full Traceback:")
        logger.error(traceback.format_exc())
        return None

# Initialize graph connection with debugging
try:
    graph = debug_neo4j_connection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    if graph is None:
        raise ConnectionError("Could not establish Neo4j connection")
except Exception as e:
    logger.critical(f"Fatal Neo4j Connection Error: {e}")
    graph = None  # Fallback to ensure graph is always defined

def setup_custom_logger(name):
    """
    Create a custom logger with improved error handling and filtering
    
    Args:
        name (str): Name of the logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    class SupressSpecificErrorFilter(logging.Filter):
        def filter(self, record):
            if 'TABLE_OR_VIEW_NOT_FOUND' in str(record.getMessage()):
                return False
            return True
    
    console_handler.addFilter(SupressSpecificErrorFilter())
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

def verify_data_collection(dataframes):
    """
    Comprehensive verification of collected dataframes
    
    Args:
        dataframes (dict): Dictionary of collected dataframes
    """
    logger.info("Data Collection Verification:")
    for name, df in dataframes.items():
        logger.info(f"DataFrame: {name}")
        logger.info(f"Record Count: {df.count()}")
        logger.info("Schema:")
        df.printSchema()
        
        # Print first few rows for debugging
        try:
            logger.info("First 5 rows:")
            df.show(5, truncate=False)
        except Exception as e:
            logger.error(f"Could not display rows for {name}: {e}")

def setup_spark():
    """Create and return a SparkSession with MongoDB and MySQL connectors"""
    try:
        spark = SparkSession.builder \
            .appName("Multi-DB to Neo4j Pipeline") \
            .config("spark.jars.packages", 
                    "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1,"
                    "mysql:mysql-connector-java:8.0.26") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .master("local[*]") \
            .getOrCreate()
        
        logger.info("Spark session created successfully")
        return spark
    except Exception as e:
        logger.error(f"Error creating Spark session: {str(e)}", exc_info=True)
        return None

def create_constraints():
    """Create unique constraints for nodes and relationship types"""
    try:
        # Create unique constraints for Person, Loan, and Company nodes
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.personId IS UNIQUE")
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Loan) REQUIRE l.loanId IS UNIQUE")
        graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE")
        graph.run("CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.personId)")
        graph.run("CREATE INDEX IF NOT EXISTS FOR (l:Loan) ON (l.loanId)")
        graph.run("CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.companyId)")
        logger.info("Neo4j constraints created successfully")
    except Exception as e:
        logger.error(f"Error creating Neo4j constraints: {str(e)}")

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
# def row_to_dict(row):
#     """Convert Spark Row to a dictionary with safe conversion"""
#     if row is None:
#         return {}
    
#     # First convert Row to dictionary
#     if hasattr(row, "asDict"):
#         d = row.asDict()
#     elif isinstance(row, dict):
#         d = row
#     else:
#         d = dict(row)  # Try direct conversion
    
#     # Sanitize the values
#     result = {}
#     for k, v in d.items():
#         if v is None:
#             continue
#         elif isinstance(v, (dict, list)):
#             result[k] = json.dumps(v)  # Convert complex objects to JSON strings
#         elif hasattr(v, "asDict"):  # Handle nested Row objects
#             result[k] = json.dumps(row_to_dict(v))
#         else:
#             result[k] = v
    
#     return result

def check_role(table_name, spark, person_id=None, id_column='personId'):
    """
    Check role with improved error handling and fallback mechanism
    
    Args:
        table_name (str): Name of the table to check
        spark (SparkSession): Active Spark session
        person_id (str, optional): Specific person ID to check
        id_column (str, optional): Column to use for ID check. Defaults to 'personId'.
    
    Returns:
        bool: Whether the person has the specified role
    """
    try:
        # First, check if the table exists in the catalog
        existing_tables = [table.name.lower() for table in spark.catalog.listTables()]
        
        if table_name.lower() not in existing_tables:
            logger.warning(f"Table {table_name} not found in Spark catalog. Skipping role check.")
            return False
        
        # Get the DataFrame
        try:
            table_df = spark.table(table_name)
        except Exception as e:
            logger.warning(f"Could not retrieve table {table_name}: {str(e)}")
            return False
        
        # Check if personId column exists
        columns = table_df.columns
        if id_column not in columns:
            matching_columns = [col for col in columns if 'id' in col.lower()]
            if matching_columns:
                id_column = matching_columns[0]
                logger.warning(f"Using alternative ID column '{id_column}' for {table_name}")
        
        # If no suitable ID column found, return False
        if id_column not in columns:
            logger.warning(f"No suitable ID column found in {table_name}")
            return False
        
        # If person_id is provided, check specific record
        if person_id:
            count = table_df.filter(col(id_column) == person_id).count()
            return count > 0
        
        return False  # Default to False if no specific logic is implemented
    
    except Exception as e:
        logger.error(f"Unexpected error checking role in {table_name}: {str(e)}")
        return False

def upsert_relationships(spark, dataframes):
    """
    Comprehensive relationship upsert with specific relationship types
    
    Creates the following relationships:
    1. HAS_LOAN: Primary Applicant to Loan
    2. WORKS_IN: Person to Company
    3. IS_COAPPLICANT: Person (Coapplicant) to Loan
    4. IS_REFERENCE: Person (Reference) to Loan
    """
    latest_timestamp = None
    
    # Ensure all required dataframes exist with a default empty DataFrame
    required_dataframes = [
        'primary_applicant', 'person', 'loan', 'company', 
        'co_applicant', 'reference'
    ]
    for df_name in required_dataframes:
        if df_name not in dataframes:
            dataframes[df_name] = spark.createDataFrame([], StructType([]))
    
    # FIRST, DELETE ALL EXISTING RELATIONSHIPS
    try:
        delete_all_relationships_query = """
        MATCH ()-[r]->()
        DELETE r
        """
        graph.run(delete_all_relationships_query)
        logger.info("Deleted all existing relationships in the graph")
    except Exception as e:
        logger.error(f"Error deleting existing relationships: {str(e)}")
    
    # 1. HAS_LOAN: Primary Applicant to Loan
    primary_applicants = dataframes["primary_applicant"].collect()
    
    for row in primary_applicants:
        record = row_to_dict(row)
        person_id = record.get('personId')
        loan_id = record.get('loanId')
        
        if person_id and loan_id:
            try:
                cypher_query = """
                MATCH (p:Person {personId: $personId})
                MATCH (l:Loan {loanId: $loanId})
                MERGE (p)-[rel:HAS_LOAN]->(l)
                """
                
                graph.run(cypher_query, personId=person_id, loanId=loan_id)
                logger.info(f"Upserted HAS_LOAN relationship: Person {person_id} -> Loan {loan_id}")
            except Exception as e:
                logger.error(f"Error upserting HAS_LOAN relationship: {str(e)}")
    
    # 2. WORKS_IN: Person to Company
    persons = dataframes["person"].collect()
    
    for row in persons:
        record = row_to_dict(row)
        person_id = record.get('personId')
        company_id = record.get('companyId')
        
        if person_id and company_id:
            try:
                cypher_query = """
                MATCH (p:Person {personId: $personId})
                MATCH (c:Company {companyId: $companyId})
                MERGE (p)-[rel:WORKS_IN]->(c)
                """
                
                graph.run(cypher_query, personId=person_id, companyId=company_id)
                logger.info(f"Upserted WORKS_IN relationship: Person {person_id} -> Company {company_id}")
            except Exception as e:
                logger.error(f"Error upserting WORKS_IN relationship: {str(e)}")
    
    # 3. IS_COAPPLICANT: Person (Coapplicant) to Loan
    co_applicants = dataframes["co_applicant"].collect()
    
    for row in co_applicants:
        record = row_to_dict(row)
        person_id = record.get('personId')
        loan_id = record.get('loanId')
        
        if person_id and loan_id:
            try:
                cypher_query = """
                MATCH (p:Person {personId: $personId})
                MATCH (l:Loan {loanId: $loanId})
                MERGE (p)-[rel:IS_COAPPLICANT]->(l)
                """
                
                graph.run(cypher_query, personId=person_id, loanId=loan_id)
                logger.info(f"Upserted IS_COAPPLICANT relationship: Person {person_id} -> Loan {loan_id}")
            except Exception as e:
                logger.error(f"Error upserting IS_COAPPLICANT relationship: {str(e)}")
    
    # 4. IS_REFERENCE: Person (Reference) to Loan
    references = dataframes["reference"].collect()
    
    for row in references:
        record = row_to_dict(row)
        person_id = record.get('personId')
        loan_id = record.get('loanId')
        
        if person_id and loan_id:
            try:
                cypher_query = """
                MATCH (p:Person {personId: $personId})
                MATCH (l:Loan {loanId: $loanId})
                MERGE (p)-[rel:IS_REFERENCE]->(l)
                """
                
                graph.run(cypher_query, personId=person_id, loanId=loan_id)
                logger.info(f"Upserted IS_REFERENCE relationship: Person {person_id} -> Loan {loan_id}")
            except Exception as e:
                logger.error(f"Error upserting IS_REFERENCE relationship: {str(e)}")
    
    return latest_timestamp
def upsert_nodes(spark, dataframes):
    """Comprehensive node upsert for all node types with advanced label management"""
    latest_timestamp = None
    
    # Node types to process
    node_types = [
        'person', 'loan', 'company', 'reference', 'coapplicant'
    ]
    
    for node_type in node_types:
        if node_type in dataframes:
            df = dataframes[node_type]
            filtered_df = df.filter(col(f"{node_type}Id").isNotNull() & (col(f"{node_type}Id") != ""))
            
            if filtered_df.count() == 0:
                logger.info(f"No valid {node_type} records to process")
                continue
            
            for row in df.collect():
                properties = row_to_dict(row)
                
                # Determine ID column and value with less verbose error handling
                node_id = None
                if node_type == 'person':
                    node_id = properties.get("personId", "")
                elif node_type == 'loan':
                    node_id = properties.get("loanId", "")
                elif node_type == 'company':
                    node_id = properties.get("companyId", "")
                elif node_type == 'reference':
                    node_id = properties.get("referenceId", "")
                elif node_type == 'coapplicant':
                    node_id = properties.get("coapplicantId", "")
                
                # Skip record if no valid ID
                if not node_id:
                    continue
                
                # Track latest timestamp
                current_timestamp = properties.get("updatedAt")
                if current_timestamp and (latest_timestamp is None or current_timestamp > latest_timestamp):
                    latest_timestamp = current_timestamp
                
                # Special handling for Person nodes with multiple labels
                if node_type == 'person':
                    is_primary = False
                    is_coapplicant = False
                    is_reference = False

                    try:
                        # Check if this person is a primary applicant
                        is_primary_row = spark.sql(f"""
                            SELECT COUNT(*) as count FROM primary_applicant 
                            WHERE personId = '{node_id}'
                        """).first()
                        is_primary = int(row_to_dict(is_primary_row).get("count", 0)) > 0
                    except Exception as e:
                        logger.info(f"Could not check primary applicant status: {e}")
                 
                    try:
                        # Check if this person is a co-applicant
                        is_coapplicant_row = spark.sql(f"""
                            SELECT COUNT(*) as count FROM co_applicant 
                            WHERE personId = '{node_id}'
                        """).first()
                        is_coapplicant = int(row_to_dict(is_coapplicant_row).get("count", 0)) > 0
                    except Exception as e:
                        logger.info(f"Could not check co-applicant status: {e}")
                    
                    try:
                        # Check if this person is a reference
                        is_reference_row = spark.sql(f"""
                            SELECT COUNT(*) as count FROM reference 
                            WHERE personId = '{node_id}'
                        """).first()
                        is_reference = int(row_to_dict(is_reference_row).get("count", 0)) > 0
                    except Exception as e:
                        logger.info(f"Could not check reference status: {e}")
                    
                    # Construct query with dynamic label management
                    query = """
                    MERGE (p:Person {personId: $nodeId})
                    SET p += $properties
                    """

                    # Then add the role labels in separate operations
                    if is_primary:
                        query += "\nSET p:PrimaryApplicant"
                    if is_coapplicant:
                        query += "\nSET p:CoApplicant"
                    if is_reference:
                        query += "\nSET p:Reference" 

                    # Remove labels that no longer apply
                    if not is_primary:
                        query += "\nREMOVE p:PrimaryApplicant"
                    if not is_coapplicant:
                        query += "\nREMOVE p:CoApplicant"
                    if not is_reference:
                        query += "\nREMOVE p:Reference"
                    
                    try:
                        graph.run(query, nodeId=node_id, properties=properties)
                        logger.info(f"Upserted Person node with ID: {node_id}")
                    except Exception as e:
                        logger.info(f"Error upserting Person node: {str(e)}")
                
                # Handling for Loan and Company nodes
                else:
                    try:
                        query = f"""
                        MERGE (n:{node_type.capitalize()} {{`{node_type}Id`: $nodeId}})
                        SET n += $properties
                        """
                        graph.run(query, nodeId=node_id, properties=properties)
                        logger.info(f"Upserted {node_type.capitalize()} node with ID: {node_id}")
                    except Exception as e:
                        logger.info(f"Error upserting {node_type.capitalize()} node: {str(e)}")
    
    return latest_timestamp
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

# def read_mongo_collection(spark, database_config, last_sync_timestamp):
#     """Read data from MongoDB collection with timestamp filter"""
#     try:
#         dataframes = {}
#         for collection in database_config['collections']:
#             df = spark.read.format("mongo") \
#                 .option("uri", f"{database_config['uri']}.{collection}") \
#                 .load()
            
#             # Filter by timestamp
#             filtered_df = df.filter(col("updatedAt") > last_sync_timestamp)
            
#             logger.info(f"MongoDB {database_config['name']}.{collection}: {filtered_df.count()} records found")
#             dataframes[collection] = filtered_df
        
#         return dataframes
#     except Exception as e:
#         logger.error(f"Error reading MongoDB database {database_config['name']}: {str(e)}")
#         return {}

def read_mongo_collection(spark, database_config, last_sync_timestamp):
    """Read data from MongoDB collection with dynamic schema handling"""
    try:
        dataframes = {}
        for collection in database_config['collections']:
            # Dynamic column specification to handle schema variations
            df = spark.read.format("mongo") \
                .option("uri", f"{database_config['uri']}.{collection}") \
                .option("inferSchema", "true") \
                .load()
            
            # List of potential timestamp columns to check
            timestamp_columns = ['updatedAt', 'created_at', 'timestamp', 'createdAt']
            
            # Find a valid timestamp column
            timestamp_col = None
            for col_name in timestamp_columns:
                if col_name in df.columns:
                    timestamp_col = col_name
                    break
            
            # If no timestamp column found, log and return full dataset
            if timestamp_col is None:
                logger.warning(f"No timestamp column found in {collection}. Returning full dataset.")
                dataframes[collection] = df
                continue
            
            # Filter by timestamp if column exists
            filtered_df = df.filter(col(timestamp_col) > last_sync_timestamp)
            
            logger.info(f"MongoDB {database_config['name']}.{collection}: {filtered_df.count()} records found")
            dataframes[collection] = filtered_df
        
        return dataframes
    except Exception as e:
        logger.error(f"Error reading MongoDB database {database_config['name']}: {str(e)}")
        logger.error(f"Full error details: {traceback.format_exc()}")
        return {}

# Modify the schema reading to be more flexible
def row_to_dict(row):
    """More robust Row to dictionary conversion"""
    if row is None:
        return {}
    
    # First convert Row to dictionary
    try:
        if hasattr(row, "asDict"):
            d = row.asDict()
        elif isinstance(row, dict):
            d = row
        else:
            d = dict(row)  # Try direct conversion
        
        # Sanitize the values
        result = {}
        for k, v in d.items():
            if v is None:
                continue
            elif isinstance(v, (dict, list)):
                try:
                    result[k] = json.dumps(v)  # Convert complex objects to JSON strings
                except:
                    result[k] = str(v)  # Fallback to string representation
            elif hasattr(v, "asDict"):  # Handle nested Row objects
                try:
                    result[k] = json.dumps(row_to_dict(v))
                except:
                    result[k] = str(v)
            else:
                result[k] = v
        
        return result
    except Exception as e:
        logger.error(f"Error converting row to dictionary: {e}")
        return {}


def read_mysql_table(spark, table_name, last_sync_timestamp):
    try:
        # Comprehensive database mapping
        database_map = {
            "Company": "Company",
            "Coapplicant": "Coapplicant",
            "Reference": "Reference"
        }

        collection_to_table_map = {
            "company": "Company",
            "coapplicant": "Coapplicant",
            "reference": "Reference"
        }
        
        # Get the specific database name for the table
        database_name = database_map.get(table_name, table_name)
        
        jdbc_url = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{database_name}"
        print(f"Connecting to:")
        print(f"URL: {jdbc_url}")
        print(f"Table: {table_name}")
        
        
        df = spark.read.format("jdbc") \
            .option("url", jdbc_url) \
            .option("driver", "com.mysql.cj.jdbc.Driver") \
            .option("dbtable", table_name) \
            .option("user", MYSQL_USER) \
            .option("password", MYSQL_PASSWORD) \
            .load()
        
        return df
    
    except Exception as e:
        print(f"Comprehensive MySQL Reading Error for {table_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def read_collections(spark, last_sync_timestamp):
    """Read data from all collections and tables with comprehensive error handling"""
    try:
        all_dataframes = {}

        logger.info("MongoDB Database Configurations:")
        for db_config in MONGO_DATABASES:
            logger.info(f"Database: {db_config['name']}, Collections: {db_config['collections']}")
        
        # Read MongoDB databases
        for db_config in MONGO_DATABASES:
            try:
                mongo_dfs = read_mongo_collection(spark, db_config, last_sync_timestamp)
                all_dataframes.update(mongo_dfs)
            except Exception as mongo_error:
                logger.error(f"Error reading MongoDB database {db_config['name']}: {mongo_error}")
        
        # Explicitly handle co-applicant data
        try:
            # Try reading from MySQL first
            mysql_coapplicant_df = read_mysql_table(spark, "Coapplicant", last_sync_timestamp)
            
            # If MySQL reading fails, try alternative methods
            if mysql_coapplicant_df is None or mysql_coapplicant_df.count() == 0:
                logger.warning("No co-applicant data found in MySQL. Attempting alternative sources.")
                
                # Check if co-applicant exists in MongoDB
                for db_config in MONGO_DATABASES:
                    if "coapplicant" in [c.lower() for c in db_config.get('collections', [])]:
                        mongo_coapplicant_df = read_mongo_collection(spark, db_config, last_sync_timestamp)
                        if mongo_coapplicant_df and 'coapplicant' in mongo_coapplicant_df:
                            mysql_coapplicant_df = mongo_coapplicant_df['coapplicant']
                            break
                
                # If still no data, create an empty DataFrame
                if mysql_coapplicant_df is None:
                    logger.error("Could not find co-applicant data in any source")
                    mysql_coapplicant_df = spark.createDataFrame([], 
                        StructType([
                            StructField("personId", StringType(), True),
                            StructField("loanId", StringType(), True)
                        ])
                    )
            
            # Add to dataframes and create temp view
            all_dataframes['co_applicant'] = mysql_coapplicant_df
            mysql_coapplicant_df.createOrReplaceTempView("co_applicant")
            
            logger.info(f"Co-applicant DataFrame created with {mysql_coapplicant_df.count()} records")
            logger.info("Co-applicant DataFrame Schema:")
            mysql_coapplicant_df.printSchema()
        except Exception as coapplicant_error:
            logger.error(f"Comprehensive error reading co-applicant data: {coapplicant_error}")
            # Create an empty DataFrame to prevent pipeline failure
            empty_coapplicant_df = spark.createDataFrame([], 
                StructType([
                    StructField("personId", StringType(), True),
                    StructField("loanId", StringType(), True)
                ])
            )
            all_dataframes['co_applicant'] = empty_coapplicant_df
            empty_coapplicant_df.createOrReplaceTempView("co_applicant")
        
        # Process other MySQL tables similarly
        mysql_tables = ["Company", "Coapplicant", "Reference"]
        for table in mysql_tables:
            try:
                df = read_mysql_table(spark, table, last_sync_timestamp)
                if df is not None:
                    collection_name = table.lower()
                    all_dataframes[collection_name] = df
                    df.createOrReplaceTempView(collection_name)
            except Exception as table_error:
                logger.error(f"Error processing {table}: {table_error}")

         # Attempt to create primary_applicant view with a safe, empty DataFrame if it doesn't exist
        try:
            # Check if primary_applicant data exists in existing sources
            for db_config in MONGO_DATABASES:
                if "primary_applicant" in [c.lower() for c in db_config.get('collections', [])]:
                    mongo_primary_applicant_df = read_mongo_collection(spark, db_config, last_sync_timestamp)
                    if mongo_primary_applicant_df and 'primary_applicant' in mongo_primary_applicant_df:
                        primary_applicant_df = mongo_primary_applicant_df['primary_applicant']
                        break
            
            # If no data found, create an empty DataFrame
            if 'primary_applicant_df' not in locals():
                primary_applicant_df = spark.createDataFrame([], 
                    StructType([
                        StructField("personId", StringType(), True),
                        StructField("loanId", StringType(), True)
                    ])
                )
            
            # Add to dataframes and create temp view
            all_dataframes['primary_applicant'] = primary_applicant_df
            primary_applicant_df.createOrReplaceTempView("primary_applicant")
            
            logger.info(f"Primary Applicant DataFrame created with {primary_applicant_df.count()} records")
        except Exception as primary_applicant_error:
            logger.error(f"Error creating primary_applicant view: {primary_applicant_error}")
            empty_primary_applicant_df = spark.createDataFrame([], 
                StructType([
                    StructField("personId", StringType(), True),
                    StructField("loanId", StringType(), True)
                ])
            )
            all_dataframes['primary_applicant'] = empty_primary_applicant_df
            empty_primary_applicant_df.createOrReplaceTempView("primary_applicant")
        
        # Comprehensive logging of registered views
        logger.info("Registered Temporary Views:")
        for table in spark.catalog.listTables():
            logger.info(f"- {table.name}")

        logger.info("Dataframes created:")
        for name, df in all_dataframes.items():
            logger.info(f"{name}: {df.count()} records")
    
        
        return all_dataframes
    except Exception as e:
        logger.error(f"Critical error in read_collections: {str(e)}")
        raise e

def main_pipeline(spark):
    """Main pipeline to sync data from multiple sources to Neo4j"""
    try:
        # Create constraints (if not exists)
        create_constraints()
        
        # Get timestamp for incremental sync
        lookback_time = datetime.now(pytz.UTC) - timedelta(minutes=SYNC_MINUTES_LOOKBACK)
        last_sync_timestamp = lookback_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Read data from all sources with timestamp filter
        dataframes = read_collections(spark, last_sync_timestamp)
        print("ALL DATAFRAMES:")
        for name, df in dataframes.items():
            print(f"{name}: {df.count()} records")
            df.printSchema()
        
        # Verify data collection
        verify_data_collection(dataframes)
        
        # Check if any updates exist
        has_updates = any(df.count() > 0 for df in dataframes.values())
        
        if has_updates:
            logger.info("Updates found. Syncing to Neo4j...")
            
            # Upsert nodes first
            node_latest_timestamp = upsert_nodes(spark,dataframes)
            
            # Upsert relationships
            rel_latest_timestamp = upsert_relationships( spark, dataframes)
            
            # Determine the latest timestamp
            latest_timestamp = node_latest_timestamp
            if rel_latest_timestamp and (not latest_timestamp or rel_latest_timestamp > latest_timestamp):
                latest_timestamp = rel_latest_timestamp
            
            logger.info(f"Sync completed. Latest timestamp: {latest_timestamp}")
        else:
            logger.info("No updates found.")
        
    except Exception as e:
        logger.error(f"Pipeline execution error: {str(e)}")

if __name__ == "__main__":
    # Create Spark session before calling main_pipeline
    spark_session = setup_spark()
    
    if spark_session:
        try:
            main_pipeline(spark_session)
        finally:
            # Stop the Spark session
            spark_session.stop()
    else:
        logger.error("Failed to create Spark session. Pipeline cannot run.")
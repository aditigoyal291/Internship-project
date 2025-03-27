import os
import time
import yaml
import logging
from typing import Dict, List, Any
from pymongo import MongoClient
from neo4j import GraphDatabase
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongo_neo4j_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MongoNeo4jSynchronizer:
    def __init__(self, config_path: str = 'sync_config.yaml'):
        """
        Initialize synchronizer with configuration
        
        :param config_path: Path to the YAML configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

        # MongoDB Connection
        try:
            self.mongo_client = MongoClient(self.config['mongodb']['connection_string'])
            self.mongo_db = self.mongo_client[self.config['mongodb']['database']]
        except Exception as e:
            logger.error(f"MongoDB Connection Error: {e}")
            raise

        # Neo4j Connection
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.config['neo4j']['uri'],
                auth=(self.config['neo4j']['username'], self.config['neo4j']['password'])
            )
        except Exception as e:
            logger.error(f"Neo4j Connection Error: {e}")
            raise

    def transform_document(self, document: Dict[str, Any], transforms: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Apply transformations to a document
        
        :param document: Source document
        :param transforms: List of transformation rules
        :return: Transformed document
        """
        if not transforms:
            return document

        transformed_doc = document.copy()
        for transform in transforms:
            field = transform.get('field')
            action = transform.get('action')

            if action == 'remove' and field in transformed_doc:
                del transformed_doc[field]
            
            elif action == 'anonymize' and field in transformed_doc:
                # Example anonymization (replace with your specific logic)
                if isinstance(transformed_doc[field], str):
                    transformed_doc[field] = transformed_doc[field][:4] + '****'
                elif isinstance(transformed_doc[field], dict):
                    # Optionally anonymize nested fields
                    for k in list(transformed_doc[field].keys()):
                        if isinstance(transformed_doc[field][k], str):
                            transformed_doc[field][k] = transformed_doc[field][k][:4] + '****'

        return transformed_doc

    def sync_collection(self, collection_config: Dict[str, Any]):
        """
        Synchronize a single collection from MongoDB to Neo4j
        
        :param collection_config: Configuration for the collection
        """
        try:
            # Get MongoDB collection
            mongo_collection = self.mongo_db[collection_config['mongo_collection']]
            
            # Determine sync criteria
            sync_criteria = {}
            if 'last_sync_field' in collection_config:
                # Find last sync time from Neo4j or use a default
                with self.neo4j_driver.session() as session:
                    last_sync_time = session.run(
                        f"MATCH (sync:SyncTracker:{collection_config['neo4j_node_label']}) "
                        "RETURN sync.last_sync_time AS last_sync_time "
                        "ORDER BY sync.last_sync_time DESC LIMIT 1"
                    ).single()
                
                if last_sync_time:
                    sync_criteria[collection_config['last_sync_field']] = {
                        '$gt': last_sync_time.get('last_sync_time')
                    }

            # Fetch documents
            documents = list(mongo_collection.find(sync_criteria))
            logger.info(f"Found {len(documents)} documents to sync for {collection_config['name']}")

            # Sync documents to Neo4j
            with self.neo4j_driver.session() as session:
                for doc in documents:
                    # Transform document
                    transformed_doc = self.transform_document(
                        doc, 
                        collection_config.get('transforms', [])
                    )

                    # Prepare upsert query
                    upsert_query = f"""
                    MERGE (n:{collection_config['neo4j_node_label']} 
                           {{{collection_config['unique_field']}: $unique_value}})
                    ON CREATE SET n = $properties
                    ON MATCH SET n += $properties
                    """

                    # Execute upsert
                    session.run(upsert_query, {
                        'unique_value': str(transformed_doc[collection_config['unique_field']]),
                        'properties': transformed_doc
                    })

                # Update sync tracker
                current_time = datetime.utcnow()
                session.run(
                    f"MERGE (sync:SyncTracker:{collection_config['neo4j_node_label']}) "
                    "SET sync.last_sync_time = $last_sync_time",
                    {'last_sync_time': current_time}
                )

            logger.info(f"Successfully synced {collection_config['name']} collection")

        except Exception as e:
            logger.error(f"Error syncing collection {collection_config['name']}: {e}")

    def run_sync(self):
        """
        Run synchronization for all configured collections
        """
        logger.info("Starting synchronization process")
        
        while True:
            try:
                # Sync each configured collection
                for collection in self.config['sync_config']['collections']:
                    self.sync_collection(collection)
                
                # Wait for next sync cycle
                sync_interval = self.config['sync_config'].get('interval_seconds', 300)
                logger.info(f"Waiting {sync_interval} seconds before next sync")
                time.sleep(sync_interval)

            except Exception as e:
                logger.error(f"Synchronization cycle error: {e}")
                # Wait before retrying
                time.sleep(300)

    def close(self):
        """
        Close database connections
        """
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()

def main():
    try:
        sync_app = MongoNeo4jSynchronizer('sync_config.yaml')
        
        # Graceful shutdown handling
        import signal
        import sys

        def signal_handler(sig, frame):
            logger.info("Interrupt received. Shutting down...")
            sync_app.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run synchronization
        sync_app.run_sync()

    except Exception as e:
        logger.error(f"Failed to start synchronization: {e}")

if __name__ == "__main__":
    main()
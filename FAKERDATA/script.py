import uuid
import random
from faker import Faker
from pymongo import MongoClient
import mysql.connector
import neo4j
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Initialize Faker for generating realistic data
fake = Faker()

class DatabaseSynchronizer:
    def __init__(self):
        # MongoDB Connection
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo_client['Tester_mongo_flower']

        # MySQL Connection
        self.mysql_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='adi93066',
            database='MysqlDB'
        )
        self.mysql_cursor = self.mysql_conn.cursor()

        # Neo4j Connection
        self.neo4j_driver = neo4j.GraphDatabase.driver(
            "bolt://localhost:7687", 
            auth=("neo4j", "password")
        )

    def generate_person_data(self):
        """Generate comprehensive person data with UUID"""
        person_id = str(uuid.uuid4())
        return {
            'id': person_id,
            'firstName': fake.first_name(),
            'lastName': fake.last_name(),
            'email': fake.email(),
            'phoneNumber': fake.phone_number(),
            'dateOfBirth': fake.date_of_birth(minimum_age=18, maximum_age=65).isoformat(),
            'createdAt': datetime.now().isoformat()
        }

    def generate_loan_data(self, primary_applicant_id, coapplicant_id, company_id):
        """Generate loan data with references"""
        return {
            'id': str(uuid.uuid4()),
            'primaryApplicantId': primary_applicant_id,
            'coapplicantId': coapplicant_id,
            'companyId': company_id,
            'loanAmount': round(random.uniform(1000, 500000), 2),
            'interestRate': round(random.uniform(2.5, 15.5), 2),
            'loanTerm': random.choice([12, 24, 36, 48, 60]),
            'status': random.choice(['PENDING', 'APPROVED', 'REJECTED']),
            'createdAt': datetime.now().isoformat()
        }

    def generate_primary_applicant_data(self, person_id):
        """Generate primary applicant data"""
        return {
            'id': str(uuid.uuid4()),
            'personId': person_id,
            'employmentDetails': {
                'jobTitle': fake.job(),
                'employerName': fake.company(),
                'annualIncome': round(random.uniform(30000, 250000), 2)
            },
            'creditScore': random.randint(300, 850)
        }

    def generate_coapplicant_data(self, person_id):
        """Generate coapplicant data"""
        return {
            'id': str(uuid.uuid4()),
            'personId': person_id,
            'relationshipToPrimaryApplicant': random.choice([
                'Spouse', 'Parent', 'Sibling', 'Friend'
            ])
        }

    def generate_company_data(self):
        """Generate company data"""
        return {
            'id': str(uuid.uuid4()),
            'name': fake.company(),
            'industry': fake.bs(),
            'registrationNumber': fake.bothify(text='########'),
            'address': {
                'street': fake.street_address(),
                'city': fake.city(),
                'country': fake.country()
            }
        }

    def generate_reference_data(self, person_id, loan_id):
        """Generate reference data"""
        return {
            'id': str(uuid.uuid4()),
            'personId': person_id,
            'loanId': loan_id,
            'referenceType': random.choice(['PERSONAL', 'PROFESSIONAL']),
            'relationship': fake.word(),
            'contactVerified': random.choice([True, False])
        }

    def sync_data(self, num_records=5):
        """Synchronize data across all databases"""
        for _ in range(num_records):
            # Generate core person data
            person_data = self.generate_person_data()
            
            # Generate related entities
            primary_applicant_data = self.generate_primary_applicant_data(person_data['id'])
            coapplicant_person_data = self.generate_person_data()
            coapplicant_data = self.generate_coapplicant_data(coapplicant_person_data['id'])
            company_data = self.generate_company_data()
            
            # MongoDB Insertion
            self.mongo_db.persons.insert_one(person_data)
            self.mongo_db.persons.insert_one(coapplicant_person_data)
            self.mongo_db.primary_applicants.insert_one(primary_applicant_data)
            self.mongo_db.coapplicants.insert_one(coapplicant_data)
            self.mongo_db.companies.insert_one(company_data)

            # MySQL Insertion (Simplified - you'd need to create tables first)
            mysql_insert_person = """
            INSERT INTO persons 
            (id, first_name, last_name, email, phone_number, date_of_birth, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.mysql_cursor.execute(mysql_insert_person, (
                person_data['id'], 
                person_data['firstName'], 
                person_data['lastName'], 
                person_data['email'], 
                person_data['phoneNumber'], 
                person_data['dateOfBirth'], 
                person_data['createdAt']
            ))

            # Neo4j Insertion
            with self.neo4j_driver.session() as session:
                session.run("""
                CREATE (p:Person {
                    id: $id, 
                    firstName: $firstName, 
                    lastName: $lastName, 
                    email: $email
                })
                """, person_data)

            # Generate and sync loan data
            loan_data = self.generate_loan_data(
                primary_applicant_data['id'], 
                coapplicant_data['id'], 
                company_data['id']
            )
            
            # Insert loan data into respective databases
            self.mongo_db.loans.insert_one(loan_data)

            # Generate reference
            reference_data = self.generate_reference_data(person_data['id'], loan_data['id'])
            self.mongo_db.references.insert_one(reference_data)

        # Commit MySQL changes
        self.mysql_conn.commit()

    def __del__(self):
        # Close all database connections
        self.mongo_client.close()
        self.mysql_cursor.close()
        self.mysql_conn.close()
        self.neo4j_driver.close()

# Usage
def main():
    synchronizer = DatabaseSynchronizer()
    synchronizer.sync_data(num_records=10)  # Generates and synchronizes 10 records
    print("Data synchronized across MongoDB, MySQL, and Neo4j!")

if __name__ == "__main__":
    main()
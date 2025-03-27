from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import random
from datetime import datetime, timedelta
import os

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# Database connection (replace with your MySQL connection details)
DATABASE_URL = "mysql+pymysql://root:adi93066@localhost/MysqlDB"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Model Definitions
class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(10), unique=True)
    name = Column(String(100))
    sector = Column(String(50))
    address = Column(String(200))
    phone = Column(String(15))
    website = Column(String(100))
    founded = Column(String(4))
    gst_number = Column(String(20))


class Person(Base):
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(String(10), unique=True)
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(15))
    address = Column(String(200))
    date_of_birth = Column(String(10))
    pan = Column(String(10), unique=True)
    aadhar = Column(String(12), unique=True)
    income = Column(Float)
    company_id = Column(String(10))
    position = Column(String(50))
    years_employed = Column(Integer)


class PrimaryApplicant(Base):
    __tablename__ = 'primary_applicants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_applicant_id = Column(String(10), unique=True)
    person_id = Column(String(10))
    name = Column(String(100))
    pan = Column(String(10))


class Loan(Base):
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String(10), unique=True)
    primary_applicant_id = Column(String(10))
    loan_type = Column(String(20))
    amount = Column(Float)
    term = Column(Integer)
    interest_rate = Column(Float)
    application_date = Column(DateTime)
    decision_date = Column(DateTime)
    status = Column(String(20))
    coapplicant_id = Column(String(10), nullable=True)


class Coapplicant(Base):
    __tablename__ = 'coapplicants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    coapplicant_id = Column(String(10), unique=True)
    person_id = Column(String(10))
    loan_id = Column(String(10))
    name = Column(String(100))
    pan = Column(String(10))
    relation_to_primary = Column(String(20))


class Reference(Base):
    __tablename__ = 'references'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_id = Column(String(10), unique=True)
    person_id = Column(String(10))
    loan_id = Column(String(10))
    name = Column(String(100))
    pan = Column(String(10))
    relation_to_borrower = Column(String(20))
    years_known = Column(Integer)


# Helper Functions
def generate_indian_phone():
    first_digit = random.choice(['6', '7', '8', '9'])
    rest_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return f"+91 {first_digit}{rest_digits}"

def generate_pan():
    letters1 = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
    digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    letter2 = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    return f"{letters1}{digits}{letter2}"

def generate_aadhar():
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])

# Indian-specific data
INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow"
]

INDIAN_SECTORS = [
    "IT Services", "Pharmaceuticals", "Automotive", "Textiles",
    "Banking & Finance", "Energy", "Telecom", "FMCG",
    "Infrastructure", "Steel"
]

LOAN_TYPES = {
    "Personal": (100000, 1500000),
    "Home": (2000000, 10000000),
    "Car": (500000, 3000000),
    "Education": (500000, 4000000),
    "Business": (1000000, 15000000)
}

LOAN_STATUSES = ["Pending", "Approved", "Rejected", "In Review"]

# Data Generation Function
def generate_data():
    # Create all tables
    # Add this before generating data
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
   

    # Generate Companies
    companies = []
    for i in range(30):
        company_id = f"E{(i + 1):03d}"
        company = Company(
            company_id=company_id,
            name=fake.company(),
            sector=random.choice(INDIAN_SECTORS),
            address=f"{fake.building_number()}, {fake.street_name()}, {random.choice(INDIAN_CITIES)} - {fake.postcode()}",
            phone=generate_indian_phone(),
            website=fake.domain_name(),
            founded=fake.year(),
            gst_number=f"27{fake.numerify('AAAAA####A')}1ZY"
        )
        companies.append(company)
    session.add_all(companies)
    session.commit()

    # Generate Persons
    persons = []
    person_ids = []
    person_pan_map = {}

    for i in range(90):
        pan = generate_pan()
        person_id = f"PERSON{i + 1:03d}"
        person = Person(
            person_id=person_id,
            name=fake.name(),
            email=fake.email(),
            phone=generate_indian_phone(),
            address=f"{fake.building_number()}, {fake.street_name()}, {random.choice(INDIAN_CITIES)} - {fake.postcode()}",
            date_of_birth=fake.date_of_birth(minimum_age=21, maximum_age=65).strftime("%Y-%m-%d"),
            pan=pan,
            aadhar=generate_aadhar(),
            income=random.randint(250000, 2500000),
            company_id=random.choice([c.company_id for c in companies]),
            position=fake.job(),
            years_employed=random.randint(1, 15)
        )
        persons.append(person)
        person_ids.append(person_id)
        person_pan_map[pan] = person_id
    session.add_all(persons)
    session.commit()

    # Generate Primary Applicants
    primary_applicants = []
    primary_applicant_ids = []

    for i in range(40):
        person_id = person_ids[i]
        person_info = session.query(Person).filter_by(person_id=person_id).first()

        primary_id = f"P{(i + 1):03d}"
        primary_applicant = PrimaryApplicant(
            primary_applicant_id=primary_id,
            person_id=person_id,
            name=person_info.name,
            pan=person_info.pan
        )
        primary_applicants.append(primary_applicant)
        primary_applicant_ids.append(primary_id)
    session.add_all(primary_applicants)
    session.commit()

    # Generate Loans
    loans = []
    loan_ids = []

    for primary_id in primary_applicant_ids:
        num_loans = random.randint(1, 3)
        
        for _ in range(num_loans):
            loan_id = f"L{len(loan_ids) + 1:03d}"
            loan_type = random.choice(list(LOAN_TYPES.keys()))
            min_amount, max_amount = LOAN_TYPES[loan_type]

            loan = Loan(
                loan_id=loan_id,
                primary_applicant_id=primary_id,
                loan_type=loan_type,
                amount=random.randint(min_amount, max_amount),
                term=random.choice([12, 24, 36, 48, 60, 120, 180, 240]),
                interest_rate=round(random.uniform(7.5, 14.0), 2),
                application_date=fake.date_time_between(start_date="-1y", end_date="now"),
                decision_date=datetime.now(),
                status=random.choice(LOAN_STATUSES)
            )
            loans.append(loan)
            loan_ids.append(loan_id)
    session.add_all(loans)
    session.commit()

    # Generate Co-applicants
    coapplicants = []
    
    for loan_id in loan_ids:
        loan = session.query(Loan).filter_by(loan_id=loan_id).first()
        
        # Select a different person as co-applicant
        possible_persons = [p for p in persons if p.person_id != 
                            session.query(PrimaryApplicant)
                            .filter_by(primary_applicant_id=loan.primary_applicant_id)
                            .first().person_id]
        
        if possible_persons:
            selected_person = random.choice(possible_persons)
            
            coapplicant = Coapplicant(
                coapplicant_id=f"C{len(coapplicants) + 1:03d}",
                person_id=selected_person.person_id,
                loan_id=loan_id,
                name=selected_person.name,
                pan=selected_person.pan,
                relation_to_primary=random.choice(["Spouse", "Parent", "Child", "Sibling"])
            )
            
            # Update loan with coapplicant
            loan.coapplicant_id = coapplicant.coapplicant_id
            coapplicants.append(coapplicant)
    
    session.add_all(coapplicants)
    session.commit()

    # Generate References
    references = []
    
    for loan_id in loan_ids:
        num_references = random.randint(1, 3)
        
        for _ in range(num_references):
            # Select a reference person different from primary and co-applicant
            loan = session.query(Loan).filter_by(loan_id=loan_id).first()
            primary = session.query(PrimaryApplicant).filter_by(primary_applicant_id=loan.primary_applicant_id).first()
            coapplicant = session.query(Coapplicant).filter_by(loan_id=loan_id).first()
            
            possible_references = [p for p in persons 
                                   if p.person_id != primary.person_id and 
                                   (not coapplicant or p.person_id != coapplicant.person_id)]
            
            if possible_references:
                selected_person = random.choice(possible_references)
                
                reference = Reference(
                    reference_id=f"R{len(references) + 1:03d}",
                    person_id=selected_person.person_id,
                    loan_id=loan_id,
                    name=selected_person.name,
                    pan=selected_person.pan,
                    relation_to_borrower=random.choice(["Family", "Friend", "Colleague"]),
                    years_known=random.randint(1, 20)
                )
                references.append(reference)
    
    session.add_all(references)
    session.commit()

    # Close the session
    session.close()

    print("Data generation complete!")

# Run the data generation
if __name__ == "__main__":
    generate_data()
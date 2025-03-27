from faker import Faker
from py2neo import Graph, Node, Relationship, NodeMatcher
import random
from datetime import datetime, timedelta

def create_neo4j_connection():
    """
    Establish a connection to Neo4j database with error handling
    """
    try:
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))
        # Test the connection
        graph.begin()
        return graph
    except Exception as e:
        print(f"Error connecting to Neo4j database: {e}")
        raise

# Initialize Faker with Indian locale
fake = Faker('en_IN')

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

def generate_data():
    # Establish Neo4j connection
    graph = create_neo4j_connection()
    matcher = NodeMatcher(graph)

    # Clear existing data
    try:
        graph.delete_all()
        print("Existing data cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")
        return

    # Generate Companies
    companies = []
    for i in range(30):
        company = Node("Company", 
            company_id=f"E{(i + 1):03d}",
            name=fake.company(),
            sector=random.choice(INDIAN_SECTORS),
            address=f"{fake.building_number()}, {fake.street_name()}, {random.choice(INDIAN_CITIES)} - {fake.postcode()}",
            phone=generate_indian_phone(),
            website=fake.domain_name(),
            founded=fake.year(),
            gst_number=f"27{fake.numerify('AAAAA####A')}1ZY"
        )
        graph.create(company)
        companies.append(company)

    # Generate Persons
    persons = []
    for i in range(90):
        pan = generate_pan()
        person = Node("Person",
            person_id=f"PERSON{i + 1:03d}",
            name=fake.name(),
            email=fake.email(),
            phone=generate_indian_phone(),
            address=f"{fake.building_number()}, {fake.street_name()}, {random.choice(INDIAN_CITIES)} - {fake.postcode()}",
            date_of_birth=fake.date_of_birth(minimum_age=21, maximum_age=65).strftime("%Y-%m-%d"),
            pan=pan,
            aadhar=generate_aadhar(),
            income=random.randint(250000, 2500000),
            position=fake.job(),
            years_employed=random.randint(1, 15)
        )
        
        # Create relationship with a random company
        company = random.choice(companies)
        employed_at = Relationship(person, "EMPLOYED_AT", company)
        graph.create(person)
        graph.create(employed_at)
        persons.append(person)

    # Generate Primary Applicants
    primary_applicants = []
    for i in range(40):
        person = persons[i]
        primary_applicant = Node("PrimaryApplicant",
            primary_applicant_id=f"P{(i + 1):03d}",
            name=person['name'],
            pan=person['pan']
        )
        
        # Create relationship with person
        is_primary = Relationship(primary_applicant, "IS_PERSON", person)
        graph.create(primary_applicant)
        graph.create(is_primary)
        primary_applicants.append(primary_applicant)

    # Generate Loans with improved relationship handling
    primary_applicant_loans = {}
    for primary_applicant in primary_applicants:
        num_loans = random.randint(1, 3)
        
        for _ in range(num_loans):
            loan_type = random.choice(list(LOAN_TYPES.keys()))
            min_amount, max_amount = LOAN_TYPES[loan_type]

            loan = Node("Loan",
                loan_id=f"L{len(primary_applicant_loans.get(primary_applicant, [])) + 1:03d}",
                loan_type=loan_type,
                amount=random.randint(min_amount, max_amount),
                term=random.choice([12, 24, 36, 48, 60, 120, 180, 240]),
                interest_rate=round(random.uniform(7.5, 14.0), 2),
                application_date=fake.date_time_between(start_date="-1y", end_date="now").strftime("%Y-%m-%d"),
                decision_date=datetime.now().strftime("%Y-%m-%d"),
                status=random.choice(LOAN_STATUSES)
            )
            
            # Create relationships
            primary_loan = Relationship(primary_applicant, "HAS_LOAN", loan)
            graph.create(loan)
            graph.create(primary_loan)
            
            # Track loans for each primary applicant
            if primary_applicant not in primary_applicant_loans:
                primary_applicant_loans[primary_applicant] = []
            primary_applicant_loans[primary_applicant].append(loan)

    # Generate Co-applicants
    for primary_applicant, loans in primary_applicant_loans.items():
        for loan in loans:
            # Select a different person as co-applicant
            possible_coapplicants = [p for p in persons if p['pan'] != primary_applicant['pan']]
            
            if possible_coapplicants:
                coapplicant_person = random.choice(possible_coapplicants)
                
                coapplicant = Node("Coapplicant",
                    coapplicant_id=f"C{len(loans):03d}",
                    name=coapplicant_person['name'],
                    pan=coapplicant_person['pan'],
                    relation_to_primary=random.choice(["Spouse", "Parent", "Child", "Sibling"])
                )
                
                # Create relationships
                coapplicant_loan = Relationship(coapplicant, "HAS_LOAN", loan)
                graph.create(coapplicant)
                graph.create(coapplicant_loan)

    # Generate References
    for primary_applicant, loans in primary_applicant_loans.items():
        for loan in loans:
            num_references = random.randint(1, 3)
            
            for _ in range(num_references):
                # Select a reference person different from primary and co-applicant
                possible_references = [p for p in persons 
                                       if p['pan'] != primary_applicant['pan']]
                
                if possible_references:
                    reference_person = random.choice(possible_references)
                    
                    reference = Node("Reference",
                        reference_id=f"R{len(loans):03d}",
                        name=reference_person['name'],
                        pan=reference_person['pan'],
                        relation_to_borrower=random.choice(["Family", "Friend", "Colleague"]),
                        years_known=random.randint(1, 20)
                    )
                    
                    # Create relationships
                    reference_loan = Relationship(reference, "REFERENCES", loan)
                    graph.create(reference)
                    graph.create(reference_loan)

    print("Data generation complete!")

# Run the data generation
if __name__ == "__main__":
    generate_data()
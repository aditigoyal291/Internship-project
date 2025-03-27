import json
import os
from datetime import datetime

def convert_mongo_date(mongo_date):
    """ Convert MongoDB date format to MySQL DATETIME format """
    if isinstance(mongo_date, dict) and '$date' in mongo_date:
        try:
            dt = datetime.strptime(mongo_date['$date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Handle cases without milliseconds
            dt = datetime.strptime(mongo_date['$date'], "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    return mongo_date  # Return as-is if no conversion needed

def json_to_sql(json_file_path, output_sql_file, db_name="your_db_name"):
    """
    Convert JSON data to SQL INSERT queries with MongoDB date handling.
    """
    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Ensure the data is in list format
    if isinstance(data, dict):
        data = [data]

    # Generate table name dynamically
    table_name = "your_table_name"  # You can customize this
    first_record = data[0]

    # Remove `_id` field from table schema if it exists
    filtered_keys = [key for key in first_record.keys() if key != "_id"]

    # SQL script starts with the database declaration
    sql_script = f"USE {db_name};\n\n"

    # Create table query (excluding `_id`)
    create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` (\n"
    create_table_query += "    `id` INT AUTO_INCREMENT PRIMARY KEY,\n"

    for key in filtered_keys:
        value = first_record[key]

        # Identify MongoDB date format and use DATETIME column type
        if isinstance(value, dict) and '$date' in value:
            create_table_query += f"    `{key}` DATETIME,\n"
        elif isinstance(value, int):
            create_table_query += f"    `{key}` INT,\n"
        elif isinstance(value, str) and len(value) < 255:
            create_table_query += f"    `{key}` VARCHAR(255),\n"
        else:
            create_table_query += f"    `{key}` TEXT,\n"

    create_table_query = create_table_query.rstrip(",\n") + "\n);\n\n"
    sql_script += create_table_query

    # Generate INSERT queries (excluding `_id`)
    insert_queries = []
    for record in data:
        # Remove the `_id` field
        filtered_record = {key: value for key, value in record.items() if key != "_id"}

        # Convert MongoDB date format to MySQL DATETIME
        for key, value in filtered_record.items():
            if isinstance(value, dict) and '$date' in value:
                filtered_record[key] = convert_mongo_date(value)

        # Generate INSERT query
        columns = ", ".join([f"`{key}`" for key in filtered_record.keys()])
        values = ", ".join(
            [f"'{value}'" if isinstance(value, str) else str(value) for value in filtered_record.values()]
        )

        insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({values});"
        insert_queries.append(insert_query)

    # Write the SQL file
    with open(output_sql_file, 'w', encoding='utf-8') as sql_file:
        sql_file.write(sql_script)
        for query in insert_queries:
            sql_file.write(query + "\n")

    print(f"✅ SQL file generated successfully: {output_sql_file}")

# ----------------------------
# 🔥 Example Usage:
# ----------------------------
if __name__ == "__main__":
    json_file_path = input("Enter the path to your JSON file: ").strip()
    output_sql_file = os.path.splitext(json_file_path)[0] + ".sql"
    
    # Prompt for the target MySQL database name
    database_name = input("Enter the target MySQL database name: ").strip()

    json_to_sql(json_file_path, output_sql_file, database_name)

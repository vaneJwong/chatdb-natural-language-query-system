from sql_handler import SQLDatabaseHandler
from nosql_handler import NoSQLDatabaseHandler
from utils import parse_natural_language
from console_utils import ConsoleFormatter as cf
import os
import time

# Get absolute path of project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Dataset location can be overridden without changing the source code.
DATA_FOLDER = os.getenv("CHATDB_DATA_DIR", os.path.join(BASE_DIR, "data"))

SQL_CONFIG = {
    "host": os.getenv("CHATDB_MYSQL_HOST", "localhost"),
    "port": int(os.getenv("CHATDB_MYSQL_PORT", "3306")),
    "user": os.getenv("CHATDB_MYSQL_USER", "root"),
    "password": os.getenv("CHATDB_MYSQL_PASSWORD", ""),
    "database": os.getenv("CHATDB_MYSQL_DATABASE", "selected_data"),
}
MONGO_CONNECTION_STRING = os.getenv(
    "CHATDB_MONGO_URI", "mongodb://localhost:27017/"
)
MONGO_DATABASE = os.getenv("CHATDB_MONGO_DATABASE", "selected_data")

SELECTED_FILES = [
    "Air Conditioners.csv",
    "All Appliances.csv",
    "All Car and Motorbike Products.csv"
]

def print_welcome():
    """Display welcome message"""
    print("\n" + "="*60)
    print(cf.highlight("🔍 Natural Language Database Query System"))
    print("="*60)
    print(cf.info("Select your database:"))
    print("1. " + cf.success("SQL    - Full features with price analysis"))
    print("2. " + cf.success("NoSQL  - Fast queries for ratings and reviews"))
    print("="*60)

def print_help(db_type):
    """Display help information"""
    print("\n" + cf.header("Quick Guide"))
    
    # Basic structure examples
    print(cf.info("\n📝 Basic Query Structure:"))
    print("   show me [category] + [conditions] + [sorting] + [limit]")
    
    # Categories
    print(cf.info("\n📦 Available Categories:"))
    print("   • air conditioners")
    print("   • appliances")
    print("   • car and motorbike products")
    
    # Database specific features
    if db_type == "sql":
        print(cf.info("\n💡 Available Conditions:"))
        print("   • with rating greater than X")
        print("   • with comments greater than X")
        print("   • with price greater than X")
        print("   • with price between X and Y")
        print("   • with discount greater than X")
        
        print(cf.info("\n📊 Sorting Options:"))
        print("   • in ascending price")
        print("   • in descending price")
        
        print(cf.info("\n⚡ SQL Query Examples:"))
        print("   1. Basic Queries:")
        print("      show me appliances limit 10 records")
        print("      show me air conditioners with rating greater than 4 limit 15 records")
        
        print("\n   2. Rating Analysis:")
        print("      show me appliances with rating greater than 4.5 limit 10 records")
        print("      show average rating for air conditioners group by category")
        
        print("\n   3. Comments Analysis:")
        print("      show me air conditioners with comments greater than 2000 limit 10 records")
        print("      show total number of appliances with comments greater than 5000 group by category")
        
        print("\n   4. Join Queries:")
        print("      # Two-table joins")
        print("      show me appliances including air conditioners with rating greater than 4")
        print("      show me appliances related to air conditioners with comments greater than 1000")
        print("      # Three-table joins")
        print("      show me appliances together with air conditioners connected to car and motorbike products")
        
        print("\n   5. Join with Conditions:")
        print("      show me appliances including air conditioners with rating greater than 4.5")
        print("      show total number of appliances related to air conditioners group by category")
        
        print("\n   6. Advanced Statistics:")
        print("      show average rating for appliances group by category")
        print("      show total number of air conditioners with rating greater than 4 group by category")
        
        print("\n   7. Combined Conditions:")
        print("      show me appliances with rating greater than 4.2 and comments greater than 3000")
        print("      show me air conditioners with rating greater than 4 and comments greater than 1000")
        
        print("\n   8. Complex Analysis:")
        print("      show me appliances with rating greater than 4.5 and comments greater than 5000 limit 20 records")
        print("      show total number of air conditioners with rating greater than 4 group by category")
        print("      show me appliances including air conditioners with rating greater than 4 and comments greater than 2000")
    else:
        print(cf.info("\n💡 Available Conditions:"))
        print("   • with rating greater than X")
        print("   • with comments greater than X")
        
        print(cf.info("\n📊 Group By Options:"))
        print("   • show total number of [category] group by category")
        print("   • show total number of [category] with rating greater than X group by category")
        print("   • show total number of [category] with comments greater than X group by category")
        
        print(cf.info("\n⚡ NoSQL Query Examples:"))
        print("   1. Basic Queries:")
        print("      show me appliances limit 10 records")
        print("      show me air conditioners with rating greater than 4 limit 15 records")
        
        print("\n   2. Rating Analysis:")
        print("      show me appliances with rating greater than 4.5 limit 10 records")
        print("      show average rating for air conditioners group by category")
        
        print("\n   3. Comments Analysis:")
        print("      show me air conditioners with comments greater than 2000 limit 10 records")
        print("      show total number of appliances with comments greater than 5000 group by category")
        
        print("\n   4. Join Queries:")
        print("      # Two-collection lookups")
        print("      show me appliances including air conditioners with rating greater than 4")
        print("      show me appliances related to air conditioners with comments greater than 1000")
        print("      # Three-collection lookups")
        print("      show me appliances together with air conditioners connected to car and motorbike products")
        
        print("\n   5. Join with Conditions:")
        print("      show me appliances including air conditioners with rating greater than 4.5")
        print("      show total number of appliances related to air conditioners group by category")
        
        print("\n   6. Advanced Statistics:")
        print("      show average rating for appliances group by category")
        print("      show total number of air conditioners with rating greater than 4 group by category")
        
        print("\n   7. Combined Conditions:")
        print("      show me appliances with rating greater than 4.2 and comments greater than 3000")
        print("      show me air conditioners with rating greater than 4 and comments greater than 1000")
        
        print("\n   8. Complex Analysis:")
        print("      show me appliances with rating greater than 4.5 and comments greater than 5000 limit 20 records")
        print("      show total number of air conditioners with rating greater than 4 group by category")
        print("      show me appliances including air conditioners with rating greater than 4 and comments greater than 2000")

    print(cf.info("\n⌨️  Special Commands:"))
    print("   • help  - Show this guide")
    print("   • exit  - Return to database selection")
    print("="*60)

def initialize_database(db_type):
    """Initialize database and import data"""
    print(cf.header("\n🔄 Database Initialization"))
    
    if not os.path.exists(DATA_FOLDER):
        raise FileNotFoundError(cf.error(f"❌ Data directory not found: {DATA_FOLDER}"))
    
    for file in SELECTED_FILES:
        file_path = os.path.join(DATA_FOLDER, file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(cf.error(f"❌ Data file not found: {file_path}"))

    print(cf.info("📥 Importing data..."))
    if db_type == "sql":
        handler = SQLDatabaseHandler(**SQL_CONFIG)
        handler.create_database_and_tables(DATA_FOLDER, SELECTED_FILES)
    else:
        handler = NoSQLDatabaseHandler(MONGO_CONNECTION_STRING, MONGO_DATABASE)
        handler.import_data(DATA_FOLDER, SELECTED_FILES)
    
    print(cf.success("\n✅ Database initialization completed!"))
    return handler

def main():
    print_welcome()
    
    while True:
        db_type = input("\n" + cf.info("👉 Choose database (SQL/NoSQL/exit): ")).strip().lower()
        if db_type == "exit":
            print(cf.success("\n👋 Thank you for using our system. Goodbye!"))
            break
        if db_type not in ["sql", "nosql"]:
            print(cf.error("❌ Invalid choice. Please enter 'SQL' or 'NoSQL'."))
            continue

        print(cf.highlight(f"\n🔄 Selected {db_type.upper()} database"))
        
        init_db = input(cf.info("📥 Initialize database? (yes/no): ")).strip().lower()
        if init_db == "yes":
            try:
                handler = initialize_database(db_type)
            except Exception as e:
                print(cf.error(f"❌ Initialization failed: {e}"))
                continue
        else:
            if db_type == "sql":
                handler = SQLDatabaseHandler(**SQL_CONFIG)
            else:
                handler = NoSQLDatabaseHandler(MONGO_CONNECTION_STRING, MONGO_DATABASE)

        print(cf.success("\n✅ Connected successfully!"))
        print_help(db_type)

        while True:
            try:
                question = input("\n" + cf.info("🔍 Enter query (help/exit): ")).strip()
                if question.lower() == "exit":
                    print(cf.success("👈 Returning to database selection..."))
                    break
                elif question.lower() == "help":
                    print_help(db_type)
                    continue

                if db_type == "sql":
                    table_name, condition, order_by, limit, group_by, aggregate, join_table, join_type, join_condition = parse_natural_language(question, db_type)
                    result = handler.query(
                        table_name=table_name,
                        condition=condition,
                        order_by=order_by,
                        limit=limit,
                        group_by=group_by,
                        aggregate=aggregate,
                        join_table=join_table,
                        join_type=join_type,
                        join_condition=join_condition
                    )
                    
                    if result == "modify":
                        continue  # 让用户输入修改后的查询
                    elif result == "similar":
                        continue  # 让用户输入类似的查询
                    elif result == "new":
                        continue  # 让用户输入新的查询
                    elif result == "exit":
                        break    # 返回主菜单
                    elif result == "error":
                        print(cf.error("Query execution failed. Please try again."))
                        continue
                else:
                    table_name, condition, order_by, limit, group_by, aggregate, _, _, _ = parse_natural_language(question, db_type)
                    handler.query(
                        collection_name=table_name,
                        condition=condition,
                        limit=limit,
                        group_by=group_by,
                        aggregate=aggregate
                    )

            except ValueError as e:
                print(cf.error(f"Error parsing query: {e}"))
            except Exception as e:
                print(cf.error(f"An error occurred: {e}"))

if __name__ == "__main__":
    main()

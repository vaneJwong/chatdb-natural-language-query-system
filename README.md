# ChatDB: Natural-Language Database Query System

ChatDB is a command-line learning tool that translates a small, documented set of
natural-language requests into database queries. It supports the same product datasets
in both MySQL and MongoDB, executes generated queries, and displays their results.

## Features

- Choose MySQL or MongoDB from one interface.
- Import three CSV datasets into the selected database.
- Filter products by rating, review count, price, and discount.
- Sort, limit, aggregate, group, and join query results.
- View generated database queries and formatted results.
- Ask for help and example commands from the interactive prompt.

## Repository layout

```text
.
├── main.py             # CLI entry point and database selection
├── sql_handler.py      # MySQL import and query execution
├── nosql_handler.py    # MongoDB import and query execution
├── utils.py            # Natural-language command parser
├── console_utils.py    # Terminal formatting
├── requirements.txt    # Python dependencies
├── .env.example        # Configuration variable template
├── data/README.md      # Dataset setup and licensing note
└── examples/commands.txt
```

## Requirements

- Python 3.11 or newer
- MySQL 5.7 or newer
- MongoDB 4.0 or newer

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Configure database connections. The application reads the following environment
   variables; the values shown in `.env.example` are templates, not automatically loaded:

   ```bash
   export CHATDB_MYSQL_HOST=localhost
   export CHATDB_MYSQL_PORT=3306
   export CHATDB_MYSQL_USER=root
   export CHATDB_MYSQL_PASSWORD='your-password'
   export CHATDB_MYSQL_DATABASE=selected_data
   export CHATDB_MONGO_URI='mongodb://localhost:27017/'
   export CHATDB_MONGO_DATABASE=selected_data
   ```

4. Follow `data/README.md` to provide the three CSV files. If they are stored elsewhere,
   set `CHATDB_DATA_DIR` to that directory.

5. Start the program:

   ```bash
   python main.py
   ```

Choose `SQL` or `NoSQL`. Select `yes` when asked to initialize the database for the first
run, then enter `help` to see supported requests. More examples are available in
`examples/commands.txt`.

## Example requests

```text
show me appliances limit 10 records
show me air conditioners with rating greater than 4 limit 15 records
show me appliances with price between 5000 and 20000 in ascending price
show total number of appliances with comments greater than 5000 group by category
```

## Security and data notes

- Keep passwords and connection strings in environment variables; never commit `.env`.
- The original third-party datasets are not included in this cleaned repository. Confirm
  their licenses before publishing them.
- Database initialization can recreate project tables. Use a dedicated local database,
  not a production database.

## Limitations

- The natural-language interface is pattern-based, not a general-purpose language model.
- The application expects the documented CSV column structure and filenames.
- MySQL and MongoDB services must already be running.

## Publish to GitHub

This directory is already initialized as a Git repository. After creating an empty GitHub
repository named `chatdb`, run:

```bash
git add .
git commit -m "Prepare ChatDB for public release"
git remote add origin https://github.com/YOUR_USERNAME/chatdb.git
git push -u origin main
```

Review `git status` before committing. Do not add the excluded datasets or a local `.env`
file unless you have checked the data license and removed every secret.

## License

No open-source license is included. Add one only if every contributor agrees to the chosen
terms and the course or dataset policies permit publication.

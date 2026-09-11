# Datasets

The datasets are separated by database-oriented format:

- `sql/` contains CSV files.
- `nosql/` contains JSON exports.

The current initialization flow reads these CSV files from `sql/` for both database modes:

- `air_conditioners.csv`
- `all_appliances.csv`
- `all_car_and_motorbike_products.csv`

When MongoDB is selected, ChatDB converts the CSV rows into MongoDB documents. The JSON
files in `nosql/` are retained exports for inspection and reuse; the current importer does
not read them directly.

To use CSV files stored elsewhere, set `CHATDB_DATA_DIR` to their directory.

Confirm that the applicable dataset license permits redistribution before making a fork or
copy public.

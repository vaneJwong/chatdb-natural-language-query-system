# Dataset setup

The `processed/` directory contains the cleaned CSV and JSON exports retained with this
repository.

The current application initialization flow expects these three source CSV files:

- `Air Conditioners.csv`
- `All Appliances.csv`
- `All Car and Motorbike Products.csv`

The source files use different names and schemas from the processed exports. Place them in
this directory, or keep them elsewhere and set `CHATDB_DATA_DIR` to that directory.

Confirm that the applicable dataset license permits redistribution before making a fork or
copy public.

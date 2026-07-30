# MySQL Grant Generator

This small Python program reads a CSV file of MySQL table names and creates a SQL script with one `GRANT SELECT` statement per table. It only writes SQL text: it never connects to MySQL or executes statements.

## CSV structure

Use one table name per row. A header is optional; common headers such as `TABLE_NAME` are skipped. Empty rows are ignored. The program accepts comma-, semicolon-, and tab-delimited CSV exports, but each populated row must contain exactly one table name.

```csv
TABLE_NAME
pds_actions_on_bonds
pds_advisors
```

For safety, table names must start with `pds_` and may contain only letters, numbers, and underscores.

## Configuration

The default database, username, host, input path, and output path are together at the top of [generate_grants.py](generate_grants.py). Change them there for a regular workflow, or override any value on the command line.

The supplied defaults are:

- Database: `platform`
- Username: `x`
- Host: `217.x.x.x`
- Input: `examples/tables.csv`
- Output: `examples/generated-grants.sql`

## Run it

Python 3.9 or newer is sufficient; there are no third-party dependencies.

```powershell
python generate_grants.py
```

To use the supplied CSV export and write a separate SQL script, run:

```powershell
python generate_grants.py --input "C:\Users\MehmetBaydur\Downloads\listOfPdsTables.csv" --output generated-grants.sql
```

You can also override connection values without editing code:

```powershell
python generate_grants.py --input tables.csv --output grants.sql --database platform --username michele --host 217.86.173.97
```

## Generated files

The output is a plain `.sql` file, which is convenient to inspect in an editor and run later with a MySQL client. `examples/generated-grants.sql` shows the result for `examples/tables.csv`.

For example:

```sql
GRANT SELECT ON platform.pds_actions_on_bonds TO 'michele'@'217.86.173.97';
```

Always review the generated SQL and execute it manually in the appropriate MySQL environment. The program does not execute SQL on your behalf.

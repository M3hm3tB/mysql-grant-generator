"""Generate MySQL GRANT SELECT statements from a CSV list of table names."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


# Change these defaults here, or override them with command-line options.
DEFAULT_DATABASE = "platform"
DEFAULT_USERNAME = "x"
DEFAULT_HOST = "217.x.x.x"
DEFAULT_INPUT_PATH = Path("examples/tables.csv")
DEFAULT_OUTPUT_PATH = Path("examples/generated-grants.sql")

MYSQL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PDS_TABLE_NAME = re.compile(r"^pds_[A-Za-z0-9_]+$")
HEADER_NAMES = {"table", "table_name", "tablename"}


class GrantGeneratorError(Exception):
    """Raised when the input or configuration cannot produce safe SQL."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate one MySQL GRANT SELECT statement for each CSV table name."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Input CSV path.")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output SQL path."
    )
    parser.add_argument("--database", default=DEFAULT_DATABASE, help="MySQL database name.")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="MySQL username.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="MySQL host for the user.")
    return parser


def is_header(row: list[str]) -> bool:
    """Return True for common one-column table-name headers."""
    return len(row) == 1 and row[0].strip().lower().replace(" ", "_") in HEADER_NAMES


def read_table_names(input_path: Path) -> list[str]:
    """Read and validate one table name from each non-empty CSV row."""
    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            sample = csv_file.read(4096)
            csv_file.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel

            table_names: list[str] = []
            first_data_row = True
            for line_number, row in enumerate(csv.reader(csv_file, dialect), start=1):
                values = [value.strip() for value in row if value.strip()]
                if not values:
                    continue

                if first_data_row and is_header(values):
                    first_data_row = False
                    continue
                first_data_row = False

                if len(values) != 1:
                    raise GrantGeneratorError(
                        f"Invalid CSV row {line_number}: expected one table name."
                    )

                table_name = values[0]
                if not PDS_TABLE_NAME.fullmatch(table_name):
                    raise GrantGeneratorError(
                        f"Invalid table name on row {line_number}: {table_name!r}. "
                        "Table names must start with 'pds_' and contain only letters, numbers, "
                        "and underscores."
                    )
                table_names.append(table_name)
    except FileNotFoundError as error:
        raise GrantGeneratorError(f"Input file not found: {input_path}") from error
    except UnicodeDecodeError as error:
        raise GrantGeneratorError(f"Input file is not valid UTF-8 text: {input_path}") from error
    except csv.Error as error:
        raise GrantGeneratorError(f"Could not read CSV file {input_path}: {error}") from error
    except OSError as error:
        raise GrantGeneratorError(f"Could not read input file {input_path}: {error}") from error

    if not table_names:
        raise GrantGeneratorError("The input CSV does not contain any table names.")
    return table_names


def validate_configuration(database: str, username: str, host: str) -> None:
    """Reject values that would make the generated SQL malformed or unsafe."""
    if not MYSQL_IDENTIFIER.fullmatch(database):
        raise GrantGeneratorError(
            "Invalid database name. Use letters, numbers, and underscores only."
        )
    if not username or not host or "'" in username or "'" in host:
        raise GrantGeneratorError("Username and host must be non-empty and cannot contain apostrophes.")


def generate_statements(table_names: list[str], database: str, username: str, host: str) -> list[str]:
    """Create the SQL lines without connecting to MySQL."""
    return [
        f"GRANT SELECT ON {database}.{table_name} TO '{username}'@'{host}';"
        for table_name in table_names
    ]


def write_statements(output_path: Path, statements: list[str]) -> None:
    """Write a SQL script, creating the output directory when needed."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
            output_file.write("\n".join(statements) + "\n")
    except OSError as error:
        raise GrantGeneratorError(f"Could not write output file {output_path}: {error}") from error


def main() -> int:
    args = build_parser().parse_args()
    try:
        validate_configuration(args.database, args.username, args.host)
        table_names = read_table_names(args.input)
        statements = generate_statements(table_names, args.database, args.username, args.host)
        write_statements(args.output, statements)
    except GrantGeneratorError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Generated {len(statements)} GRANT statement(s) in {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

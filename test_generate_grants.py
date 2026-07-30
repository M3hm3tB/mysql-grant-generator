"""Basic checks for the CSV-to-SQL conversion."""

import tempfile
import unittest
from pathlib import Path

from generate_grants import GrantGeneratorError, generate_statements, read_table_names


class GrantGeneratorTests(unittest.TestCase):
    def test_reads_header_and_ignores_blank_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "tables.csv"
            input_path.write_text("TABLE_NAME\n\npds_first\npds_second\n", encoding="utf-8")

            self.assertEqual(read_table_names(input_path), ["pds_first", "pds_second"])

    def test_rejects_multiple_table_names_in_a_row(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_path = Path(temporary_directory) / "tables.csv"
            input_path.write_text("pds_first,pds_second\n", encoding="utf-8")

            with self.assertRaises(GrantGeneratorError):
                read_table_names(input_path)

    def test_generates_expected_statement(self) -> None:
        statements = generate_statements(
            ["pds_example"], "platform", "michele", "217.86.173.97"
        )
        self.assertEqual(
            statements,
            ["GRANT SELECT ON platform.pds_example TO 'michele'@'217.86.173.97';"],
        )


if __name__ == "__main__":
    unittest.main()

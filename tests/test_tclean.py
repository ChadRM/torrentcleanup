# File: tests/test_tclean.py

import unittest

from tclean import bytes_to_gb


class TestBytesToGb(unittest.TestCase):

    def test_bytes_to_gb_exact_conversion(self):
        self.assertEqual("1.00 GB", bytes_to_gb(1073741824))

    def test_bytes_to_gb_small_number(self):
        self.assertEqual("0.00 GB", bytes_to_gb(512))

    def test_bytes_to_gb_zero_bytes(self):
        self.assertEqual("0.00 GB", bytes_to_gb(0))

    def test_bytes_to_gb_negative_bytes(self):
        self.assertEqual("-1.00 GB", bytes_to_gb(-1073741824))


if __name__ == "__main__":
    unittest.main()

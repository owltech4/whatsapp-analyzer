import unittest
from datetime import datetime

from src.parser import decode_upload, parse_chat


class ParserTests(unittest.TestCase):
    def test_bracketed_header_without_dash(self):
        messages, line_count = parse_chat(
            "[20/10/24, 21:28:11] Lari: Oi\n[20/10/24, 21:29:00] Marcelo: Olá"
        )
        self.assertEqual(line_count, 2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].author, "Lari")
        self.assertEqual(messages[0].timestamp, datetime(2024, 10, 20, 21, 28, 11))

    def test_standard_header_and_multiline_message(self):
        messages, _ = parse_chat("20/10/2024, 21:28 - Ana: primeira linha\ncontinuação")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "primeira linha\ncontinuação")

    def test_us_date_when_requested(self):
        messages, _ = parse_chat("10/20/24, 9:05 PM - Ana: hello", day_first=False)
        self.assertEqual(messages[0].timestamp, datetime(2024, 10, 20, 21, 5))

    def test_utf16_upload(self):
        self.assertEqual(decode_upload("olá".encode("utf-16")), "olá")


if __name__ == "__main__":
    unittest.main()


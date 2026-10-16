import unittest
from datetime import date, datetime

import pandas as pd

from src.conflict_detector import detect_conflicts
from src.parser import Message
from src.statistics import filter_by_date_range


class AnalysisTests(unittest.TestCase):
    def test_date_filter_keeps_only_selected_period(self):
        frame = pd.DataFrame({
            "data": pd.to_datetime(["2024-10-01", "2024-10-02", "2024-10-03", None]),
            "linha": [1, 2, 3, 4],
        })
        result = filter_by_date_range(frame, date(2024, 10, 2), date(2024, 10, 2))
        self.assertEqual(result["linha"].tolist(), [2])

    def test_full_date_range_can_keep_undated_messages(self):
        frame = pd.DataFrame({
            "data": pd.to_datetime(["2024-10-01", None]),
            "linha": [1, 2],
        })
        result = filter_by_date_range(
            frame, date(2024, 10, 1), date(2024, 10, 1), include_undated=True
        )
        self.assertEqual(result["linha"].tolist(), [1, 2])

    def test_conflict_detector_returns_context_and_trigger_lines(self):
        messages = [
            Message(datetime(2024, 10, 1, 12, 0), "A", "Oi", 1),
            Message(datetime(2024, 10, 1, 12, 1), "B", "Cala a boca", 2),
            Message(datetime(2024, 10, 1, 12, 2), "A", "Vamos conversar", 3),
        ]
        episodes = detect_conflicts(messages, context_messages=1)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].trigger_lines, [2])
        self.assertEqual(episodes[0].trigger_terms, ["cala a boca"])
        self.assertEqual([m.line for m in episodes[0].messages], [1, 2, 3])

    def test_ordinary_generalization_and_emotion_word_are_not_conflict_signals(self):
        messages = [
            Message(datetime(2024, 10, 1, 12, 0), "A", "Você sempre gostou de viajar; que ódio desse resfriado", 1),
        ]
        self.assertEqual(detect_conflicts(messages), [])


if __name__ == "__main__":
    unittest.main()


"""Regression checks for the model response formats seen in local analysis."""
import unittest

from pydantic import ValidationError
from tasks.audio_analysis import parse_sentiment_response


class SentimentResponseTests(unittest.TestCase):
    def test_plain_and_markdown_json(self):
        payload = '{"sentiment_analysis": [{"text": "I helped.", "sentiment": "POSITIVE", "confidence": 0.9}]}'
        for content in (payload, f"```json\n{payload}\n```", f"```\n{payload}\n```"):
            with self.subTest(content=content):
                result = parse_sentiment_response(content)
                self.assertEqual(result.sentiment_analysis[0].text, "I helped.")

    def test_invalid_json_and_invalid_schema_are_rejected(self):
        for content in ('not JSON', '{"sentiment_analysis": [{"sentiment": "UNKNOWN"}]}'):
            with self.subTest(content=content):
                with self.assertRaises(ValidationError):
                    parse_sentiment_response(content)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest

try:
    import environment
except ModuleNotFoundError:
    import environment_template as environment

    sys.modules["environment"] = environment

from operation_engine import _map_answer_indices, _normalize_option, _normalize_stem
from question_engine import load_question_list


class QuestionMatchingTests(unittest.TestCase):
    def test_normalization_removes_number_and_option_prefixes(self):
        self.assertEqual(
            _normalize_stem("12. 任何电气设备（测试）"),
            _normalize_stem("任何电气设备测试"),
        )
        self.assertEqual(_normalize_option("A、安全电压"), "安全电压")

    def test_every_bundled_answer_maps_to_its_options(self):
        questions = load_question_list(environment.question_path)
        self.assertGreater(len(questions), 0)
        for question in questions:
            with self.subTest(stem=question.stem):
                chosen = _map_answer_indices(
                    question.correct_answers,
                    question.answers,
                )
                self.assertEqual(len(chosen), len(question.correct_answers))


if __name__ == "__main__":
    unittest.main()

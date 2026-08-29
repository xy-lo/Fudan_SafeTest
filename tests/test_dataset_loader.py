import sys
import unittest

try:
    import environment  # noqa: F401
except ModuleNotFoundError:
    import environment_template

    sys.modules["environment"] = environment_template

from dataset_loader import get_questions_from_result_html


class ResultPageParserTests(unittest.TestCase):
    def test_parse_current_result_page_structure(self):
        html = """
        <div class="panel-group">
          <div class="panel panel-info">
            <div class="panel-body">
              <div class="col-md-10">
                <div class="row"><label>1</label><label>.</label><span>示例题</span></div>
                <div class="row"><label>选项A</label><label>:</label><span>答案甲</span></div>
                <div class="row"><label>选项B</label><label>:</label><span>答案乙</span></div>
                <div class="row"><label>正确答案</label><label>:</label><span>选项A,选项B</span></div>
                <div class="row"><label>考生答案</label><label>:</label><span>选项A</span></div>
              </div>
            </div>
          </div>
        </div>
        """
        questions = get_questions_from_result_html(html)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].stem, "示例题")
        self.assertEqual(questions[0].answers, ["答案甲", "答案乙"])
        self.assertEqual(questions[0].correct_answers, ["答案甲", "答案乙"])


if __name__ == "__main__":
    unittest.main()

from typing import List

from bs4 import BeautifulSoup
import re

from cookie_engine import close_driver, driver_get_with_cookies
from environment import dataset_path, main_page
from operation_engine import goto_result
from question import Question
from question_engine import load_question_list


# 还有一些没答案的，这里没有处理

def default_load() -> List[Question]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')

    result = ""
    for item in soup.findAll("p"):
        cur_text = item.text.replace(" ", "").replace("\n", "").replace("\xa0", "")
        if len(cur_text) > 0:
            result += cur_text
    return get_questions_from_text(result)


def local_load(path) -> List[Question]:
    return load_question_list(path)


def web_load() -> List[Question]:
    driver = driver_get_with_cookies(main_page)
    try:
        goto_result(driver)
        result_html = driver.page_source
    finally:
        close_driver(driver)
    return get_questions_from_result_html(result_html)


def get_questions_from_result_html(raw_html) -> List[Question]:
    """按当前成绩详情页的 DOM 结构解析题干、选项和正确答案。"""
    def clean_text(node):
        if node is None:
            return ""
        return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()

    soup = BeautifulSoup(raw_html, "html.parser")
    root = soup.select_one(".panel-group")
    if root is None:
        raise ValueError("成绩详情页中未找到题目区域")

    questions = []
    for block in root.select(".panel-body > .col-md-10"):
        rows = [
            item
            for item in block.find_all("div", recursive=False)
            if "row" in item.get("class", [])
        ]
        if not rows:
            continue

        stem = clean_text(rows[0].find("span"))
        option_by_code = {}
        correct_raw = ""

        for row in rows[1:]:
            labels = row.find_all("label", recursive=False)
            spans = row.find_all("span", recursive=False)
            key = clean_text(labels[0] if labels else None)
            value = clean_text(spans[0] if spans else None)
            option_match = re.fullmatch(r"选项([A-Z])", key)
            if option_match:
                option_by_code[option_match.group(1)] = value
            elif key == "正确答案":
                correct_raw = value

        codes = re.findall(r"选项([A-Z])", correct_raw)
        answers = [option_by_code[code] for code in sorted(option_by_code)]
        correct_answers = [
            option_by_code[code]
            for code in codes
            if code in option_by_code
        ]
        if not stem or not answers or len(correct_answers) != len(codes):
            raise ValueError(f"成绩详情页题目解析不完整：{stem or '<空题干>'}")
        questions.append(Question(stem, answers, correct_answers))

    if not questions:
        raise ValueError("成绩详情页未解析出任何题目")
    return questions


def get_questions_from_text(raw_text) -> List[Question]:
    raw_question_list = re.findall("(?<=\d\.).*?:[0-9]\.[0-9](?=\d*\.\D|[一二三四五六])", raw_text)

    question_list = []
    for question in raw_question_list:
        stem = re.findall("^.*?(?=选项A)", question)[0]

        answers = []
        if question.find("正确答案") != -1:
            raw_answers = re.findall("(?<=选项A:).*(?=正确答案)", question)[0]
        else:
            raw_answers = re.findall("(?<=选项A:).*(?=考生答案)", question)[0]
        answers = re.split("选项.:", raw_answers)

        correct_answers = []
        raw_correct_answers = re.findall("(?<=正确答案:).*(?=考生答案)", question)
        if len(raw_correct_answers) > 0:
            raw_correct_answers = raw_correct_answers[0]
            raw_correct_answers_list = raw_correct_answers.split(",")
            correct_answers = [ord(answer.split("选项")[1]) - ord('A') for answer in raw_correct_answers_list]
            correct_answers = [answers[index] for index in correct_answers]
        question_list.append(Question(stem, answers, correct_answers))
    return question_list

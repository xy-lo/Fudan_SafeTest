import json
from typing import Dict, List

from question import Question


def validate_question_list(question_list: List[Question]):
    seen_stems = set()
    for index, question in enumerate(question_list, start=1):
        if not question.stem.strip():
            raise ValueError(f"第 {index} 题缺少题干")
        if question.stem in seen_stems:
            raise ValueError(f"题干重复：{question.stem}")
        seen_stems.add(question.stem)

        if len(question.answers) < 2 or any(
            not answer.strip() for answer in question.answers
        ):
            raise ValueError(f"题目选项不完整：{question.stem}")
        if not question.correct_answers:
            raise ValueError(f"题目缺少正确答案：{question.stem}")
        if any(
            answer not in question.answers
            for answer in question.correct_answers
        ):
            raise ValueError(f"正确答案不在选项中：{question.stem}")


def question_list_merge(
    a: List[Question],
    b: List[Question],
) -> Dict[str, int]:
    """把 b 合并到 a；同题干以 b 中的最新题目和答案为准。"""
    index_by_stem = {
        question.stem: index
        for index, question in enumerate(a)
    }
    added = 0
    updated = 0
    for question in b:
        index = index_by_stem.get(question.stem)
        if index is None:
            index_by_stem[question.stem] = len(a)
            a.append(question)
            added += 1
            continue

        if a[index].to_dict() != question.to_dict():
            a[index] = question
            updated += 1

    return {"added": added, "updated": updated}


def save_question_list(question_list: List[Question], path):
    validate_question_list(question_list)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(
            [question.to_dict() for question in question_list],
            ensure_ascii=False,
            indent=2,
        ))


def load_question_list(path):
    with open(path, 'r', encoding='utf8') as f:
        question_list_json = json.loads(f.read())
    return [Question.from_dict(question) for question in question_list_json]

import argparse
import os

from dataset_loader import local_load, web_load
from environment import question_path
from question_engine import question_list_merge, save_question_list


def main():
    parser = argparse.ArgumentParser(description="从已完成试卷更新本地题库")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="仅保留当前结果页中的这套试卷，不合并历史题目",
    )
    args = parser.parse_args()

    latest_questions = web_load()
    if not latest_questions:
        raise RuntimeError("结果页未解析出任何题目，题库未修改")

    if args.replace:
        question_result = latest_questions
        stats = {"added": len(latest_questions), "updated": 0}
    else:
        question_result = []
        if os.path.exists(question_path):
            question_list_merge(question_result, local_load(question_path))
        stats = question_list_merge(question_result, latest_questions)

    save_question_list(question_result, question_path)
    print(
        f"题库更新完成：共 {len(question_result)} 题，"
        f"新增 {stats['added']} 题，更新 {stats['updated']} 题。"
    )


if __name__ == "__main__":
    main()

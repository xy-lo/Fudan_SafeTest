import argparse
import platform
import sys

from cookie_engine import close_driver, create_driver, driver_get_with_cookies
from environment import keep_browser_open, main_page, question_path
from operation_engine import answer_all_question, take_exam
from question_engine import load_question_list


def check_environment():
    questions = load_question_list(question_path)
    if not questions:
        raise RuntimeError("题库为空")
    if any(
        not item.stem or not item.answers or not item.correct_answers
        for item in questions
    ):
        raise RuntimeError("题库中存在缺少题干、选项或答案的记录")

    driver = create_driver()
    try:
        driver.get(
            "data:text/html;charset=utf-8,"
            "<title>SafeTest Check</title><h1>OK</h1>"
        )
        capabilities = driver.capabilities
        print(
            f"浏览器：{capabilities.get('browserName')} "
            f"{capabilities.get('browserVersion')}"
        )
    finally:
        close_driver(driver)
    print(f"题库：{len(questions)} 题")
    system = platform.system()
    if system == "Windows":
        launcher = "双击“一键运行.bat”"
    elif system == "Darwin":
        launcher = "双击“一键运行.command”"
    else:
        launcher = "执行 bash run.sh"
    print(f"环境检查通过，可以{launcher}开始。")


def run_exam():
    question_result = load_question_list(question_path)
    question_dict = {
        question.stem: question
        for question in question_result
    }
    driver = driver_get_with_cookies(main_page)
    try:
        take_exam(driver)
        results = answer_all_question(driver, question_dict)
        print(f"\n已填写 {len(results)} 题。脚本不会自动交卷。")
        if keep_browser_open:
            input(
                "请在浏览器中检查并手动交卷；"
                "完成后回到这里按回车关闭浏览器……"
            )
    except Exception:
        print("\n自动填写已停止，浏览器将保留供你检查。", file=sys.stderr)
        if keep_browser_open and sys.stdin.isatty():
            input("查看上方错误和当前题目后，按回车关闭浏览器……")
        raise
    finally:
        close_driver(driver)


def main():
    parser = argparse.ArgumentParser(
        description="复旦大学实验室安全考试辅助脚本"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="只检查环境和浏览器驱动，不进入考试",
    )
    args = parser.parse_args()
    if args.check:
        check_environment()
    else:
        run_exam()


if __name__ == "__main__":
    main()

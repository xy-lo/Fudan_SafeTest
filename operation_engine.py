import re
import time

from rapidfuzz import fuzz, process
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support.ui import WebDriverWait

import environment


def _setting(name, default=None):
    return getattr(environment, name, default)


def _clean_text(text):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", str(text or "")).lower()


def _normalize_stem(text):
    text = re.sub(r"^\s*\d+\s*[.、．]\s*", "", str(text or ""))
    return _clean_text(text)


def _normalize_option(text):
    text = re.sub(
        r"^\s*[A-ZＡ-Ｚ]\s*[、.．:：)）]\s*",
        "",
        str(text or ""),
        flags=re.I,
    )
    return _clean_text(text)


def _safe_click(driver: WebDriver, element: WebElement):
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


def _find_by_text(driver: WebDriver, by, value, expected_text):
    expected = _clean_text(expected_text)
    partial_match = None
    for element in driver.find_elements(by, value):
        actual = _clean_text(element.text)
        if actual == expected:
            return element
        if partial_match is None and expected in actual:
            partial_match = element
    return partial_match


def _current_stem(driver: WebDriver):
    return driver.find_element(By.CSS_SELECTOR, ".exams p").text.strip()


def take_exam(driver: WebDriver):
    if driver.find_elements(By.CSS_SELECTOR, ".exams"):
        return

    online_exam = _find_by_text(driver, By.CLASS_NAME, "fl", "在线考试")
    if online_exam is None:
        raise RuntimeError(f"未找到“在线考试”入口，当前页面：{driver.current_url}")
    _safe_click(driver, online_exam)
    time.sleep(1)

    confirm = _find_by_text(driver, By.TAG_NAME, "button", "确认")
    if confirm is not None:
        _safe_click(driver, confirm)
        time.sleep(1)

    WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: _find_by_text(
            current,
            By.CLASS_NAME,
            "fl",
            "实验室安全在线校级卷",
        )
        is not None
    )
    exam_entry = _find_by_text(
        driver,
        By.CLASS_NAME,
        "fl",
        "实验室安全在线校级卷",
    )
    enter_btn = exam_entry.find_element(By.ID, "intoExamRoom")
    _safe_click(driver, enter_btn)
    time.sleep(1)

    begin_btn = WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: current.find_element(By.ID, "examOnlineStrat")
    )
    _safe_click(driver, begin_btn)
    WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: bool(current.find_elements(By.CSS_SELECTOR, ".exams"))
    )


def goto_result(driver: WebDriver):
    result_entry = _find_by_text(
        driver,
        By.CLASS_NAME,
        "fl",
        "考试成绩查询及合格证打印",
    )
    if result_entry is None:
        raise RuntimeError("未找到“考试成绩查询及合格证打印”入口")
    _safe_click(driver, result_entry)
    time.sleep(1)

    row = WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: current.find_elements(By.CLASS_NAME, "odd")[0]
    )
    _safe_click(driver, row.find_elements(By.TAG_NAME, "a")[0])
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])


def goto_next_question(driver: WebDriver):
    old_stem = _current_stem(driver)
    next_btn = _find_by_text(driver, By.TAG_NAME, "button", "下一题")
    if next_btn is None or not next_btn.is_enabled():
        return False
    _safe_click(driver, next_btn)
    WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: _current_stem(current) != old_stem
    )
    return True


def _goto_section(driver: WebDriver, section_name):
    section_link = _find_by_text(driver, By.TAG_NAME, "a", section_name)
    if section_link is None:
        raise RuntimeError(f"未找到“{section_name}”题型入口")
    _safe_click(driver, section_link)
    WebDriverWait(driver, int(_setting("page_wait_time", 30))).until(
        lambda current: bool(current.find_elements(By.CSS_SELECTOR, ".exams"))
    )


def _discover_sections(driver: WebDriver):
    sections = []
    for element in driver.find_elements(By.TAG_NAME, "a"):
        text = element.text.replace(" ", "")
        match = re.search(r"(单选题|多选题|判断题).*?共(\d+)题", text)
        if match and all(item[0] != match.group(1) for item in sections):
            sections.append((match.group(1), int(match.group(2))))
    return sections


def _map_answer_indices(correct_answers, option_texts):
    option_norms = [_normalize_option(text) for text in option_texts]
    chosen = set()

    for correct_answer in correct_answers:
        normalized_answer = _normalize_option(correct_answer)
        exact = [
            index
            for index, option in enumerate(option_norms)
            if option == normalized_answer and index not in chosen
        ]
        if len(exact) == 1:
            chosen.add(exact[0])
            continue

        candidates = [
            (index, fuzz.ratio(normalized_answer, option))
            for index, option in enumerate(option_norms)
            if index not in chosen
        ]
        candidates.sort(key=lambda item: item[1], reverse=True)
        threshold = float(_setting("option_match_threshold", 88))
        if not candidates or candidates[0][1] < threshold:
            raise RuntimeError(
                f"答案选项无法可靠匹配：{correct_answer!r}；页面选项：{option_texts!r}"
            )
        chosen.add(candidates[0][0])

    return chosen


def answer_question(driver: WebDriver, question_dict: dict):
    question_stem_list = list(question_dict.keys())
    question_area = driver.find_elements(By.CLASS_NAME, "exams")[0]

    stem = question_area.find_elements(By.TAG_NAME, "p")[0].text
    matched = process.extractOne(
        stem,
        question_stem_list,
        scorer=fuzz.ratio,
        processor=_normalize_stem,
    )
    if matched is None:
        raise RuntimeError(f"题库为空，无法匹配题目：{stem}")
    match_question_stem, score, _ = matched
    threshold = float(_setting("match_threshold", 78))
    if score < threshold:
        raise RuntimeError(
            f"题干匹配度过低（{score:.1f} < {threshold:.1f}），已停止以防误答：{stem}"
        )

    match_question = question_dict[match_question_stem]
    answer_rows = question_area.find_elements(By.CSS_SELECTOR, "[id='radiolist']")
    controls = question_area.find_elements(
        By.CSS_SELECTOR,
        "input[type='radio'], input[type='checkbox']",
    )
    if not controls:
        raise RuntimeError(f"未找到题目选项控件：{stem}")

    if len(answer_rows) == len(controls):
        option_texts = [row.text.strip() for row in answer_rows]
    else:
        option_texts = [
            control.find_element(By.XPATH, "..").text.strip()
            for control in controls
        ]

    chosen = _map_answer_indices(match_question.correct_answers, option_texts)
    for index, control in enumerate(controls):
        should_select = index in chosen
        if control.is_selected() != should_select:
            driver.execute_script("arguments[0].click();", control)

    selected = [control.is_selected() for control in controls]
    expected = [index in chosen for index in range(len(controls))]
    if selected != expected:
        raise RuntimeError(f"选项写入后校验失败：{stem}")

    confirm = _find_by_text(driver, By.TAG_NAME, "button", "确定")
    if confirm is None:
        raise RuntimeError(f"未找到“确定”按钮：{stem}")
    _safe_click(driver, confirm)
    time.sleep(float(_setting("answer_delay", 0.35)))

    return {
        "stem": stem,
        "matched_stem": match_question_stem,
        "score": score,
        "selected": [option_texts[index] for index in sorted(chosen)],
    }


def answer_all_question(driver: WebDriver, question_dict: dict):
    sections = _discover_sections(driver)
    if not sections:
        raise RuntimeError("未识别到单选题、多选题、判断题入口")

    total = sum(count for _, count in sections)
    completed = 0
    results = []
    for section_name, count in sections:
        _goto_section(driver, section_name)
        print(f"\n开始填写{section_name}（{count}题）")
        for index in range(count):
            result = answer_question(driver, question_dict)
            completed += 1
            results.append(result)
            choices = " / ".join(result["selected"])
            print(f"[{completed}/{total}] 匹配 {result['score']:.1f}：{choices}")
            if index < count - 1 and not goto_next_question(driver):
                raise RuntimeError(
                    f"{section_name}第 {index + 1} 题后无法进入下一题"
                )

    return results

"""浏览器启动与登录状态管理。

旧版项目把 Cookie 写入文本文件，并要求用户手工配置 chromedriver。
现在改用独立的持久化浏览器资料目录，并让 Selenium Manager 自动匹配驱动。
"""

import os
import platform
import shutil
import socket
import subprocess
import time
import urllib.request
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="urllib3 v2 only supports OpenSSL.*",
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait

import environment


def _setting(name, default=None):
    return getattr(environment, name, default)


def _browser_candidates(browser_name):
    system = platform.system()
    candidates = []

    if system == "Darwin":
        if browser_name == "chrome":
            candidates.append(
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            )
        else:
            candidates.append(
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
            )
    elif system == "Windows":
        roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        if browser_name == "chrome":
            relative = Path("Google/Chrome/Application/chrome.exe")
        else:
            relative = Path("Microsoft/Edge/Application/msedge.exe")
        candidates.extend(Path(root) / relative for root in roots if root)

    executable_names = {
        "chrome": [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "chrome.exe",
        ],
        "edge": [
            "microsoft-edge",
            "microsoft-edge-stable",
            "msedge.exe",
        ],
    }
    for executable_name in executable_names[browser_name]:
        located = shutil.which(executable_name)
        if located:
            candidates.append(Path(located))

    return candidates


def _browser_executable(browser_name, configured_path):
    if configured_path:
        path = Path(configured_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"browser_binary 指向的文件不存在：{path}")
        return path

    candidates = _browser_candidates(browser_name)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    checked = "、".join(str(item) for item in candidates) or "系统 PATH"
    raise FileNotFoundError(
        f"未自动找到 {browser_name} 浏览器（已检查：{checked}）。"
        "请安装浏览器，或在 environment.py 中设置 browser_binary。"
    )


def _free_local_port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def _launch_browser_process(browser_name, browser_binary, profile_dir):
    port = _free_local_port()
    command = [
        str(browser_binary),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-search-engine-choice-screen",
        "--start-maximized",
        "about:blank",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    status_url = f"http://127.0.0.1:{port}/json/version"
    for _ in range(80):
        if process.poll() is not None:
            raise RuntimeError(f"{browser_name} 启动失败，退出码：{process.returncode}")
        try:
            urllib.request.urlopen(status_url, timeout=1).read()
            return process, port
        except Exception:
            time.sleep(0.25)

    process.terminate()
    raise TimeoutError(f"{browser_name} 远程调试接口启动超时")


def create_driver():
    browser_name = str(_setting("browser_name", "chrome")).lower()
    if browser_name not in {"chrome", "edge"}:
        raise ValueError("browser_name 仅支持 'chrome' 或 'edge'")

    configured_profile = str(_setting("profile_path", "")).strip()
    if configured_profile:
        profile_dir = Path(configured_profile).expanduser().resolve()
    else:
        project_root = Path(_setting("project_root", Path.cwd())).resolve()
        platform_name = platform.system().lower() or "unknown"
        profile_dir = project_root / ".browser-profile" / (
            f"{platform_name}-{browser_name}"
        )
    profile_dir.mkdir(parents=True, exist_ok=True)
    driver_path = str(_setting("driver_path", "")).strip()
    browser_binary = _browser_executable(
        browser_name,
        str(_setting("browser_binary", "")).strip(),
    )

    process, port = _launch_browser_process(
        browser_name,
        browser_binary,
        profile_dir,
    )

    try:
        if browser_name == "edge":
            options = EdgeOptions()
            options.debugger_address = f"127.0.0.1:{port}"
            service = EdgeService(executable_path=driver_path) if driver_path else EdgeService()
            browser = webdriver.Edge(service=service, options=options)
        else:
            options = ChromeOptions()
            options.debugger_address = f"127.0.0.1:{port}"
            service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
            browser = webdriver.Chrome(service=service, options=options)
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        raise

    browser._safetest_browser_process = process
    browser.set_page_load_timeout(int(_setting("page_wait_time", 30)))
    return browser


def close_driver(browser):
    process = getattr(browser, "_safetest_browser_process", None)
    try:
        browser.quit()
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _on_fudan_exam_site(browser):
    return "lsem.fudan.edu.cn" in browser.current_url and "authserver" not in browser.current_url


def driver_get_with_cookies(url, path=None):
    """打开考试系统；首次运行时等待用户在浏览器内完成统一身份认证。"""
    browser = create_driver()
    try:
        browser.get(url)

        if not _on_fudan_exam_site(browser):
            print("\n首次运行：请在打开的浏览器中完成复旦统一身份认证。")
            print("脚本不会读取或保存你的账号密码，登录状态保存在本项目的独立浏览器资料目录。\n")

        WebDriverWait(browser, int(_setting("login_wait_time", 300))).until(
            _on_fudan_exam_site
        )
        WebDriverWait(browser, int(_setting("page_wait_time", 30))).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        return browser
    except Exception:
        close_driver(browser)
        raise


if __name__ == "__main__":
    driver = driver_get_with_cookies(environment.main_page)
    input()
    close_driver(driver)

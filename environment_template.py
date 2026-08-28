from pathlib import Path


project_root = Path(__file__).resolve().parent

# chrome / edge。默认使用本机 Chrome；驱动由 Selenium Manager 自动匹配。
browser_name = "chrome"
browser_binary = ""
driver_path = ""

# 留空时按操作系统和浏览器分别创建独立资料目录，不读取日常浏览器资料。
profile_path = ""

main_page = "https://lsem.fudan.edu.cn/fd_aqks_new/examProgress/examBase/examIndex"
auth_url = "https://id.fudan.edu.cn/"

dataset_path = str(project_root / "asset/dataset/index.html")
cookie_path = str(project_root / "asset/cookie.txt")  # 仅为兼容旧配置保留
question_path = str(project_root / "asset/questions.json")

# 首次运行时，脚本会等待用户在浏览器内完成统一身份认证。
login_wait_time = 300
page_wait_time = 30

# 题干低于此相似度时停止自动填写，防止新题被强行套用旧答案。
match_threshold = 78
option_match_threshold = 88
answer_delay = 0.35

# 填题完成后保留浏览器，交卷由用户手动完成。
keep_browser_open = True

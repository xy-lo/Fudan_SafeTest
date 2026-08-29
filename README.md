# Fudan SafeTest

复旦大学实验室安全考试辅助脚本。项目已迁移到 Selenium 4，可自动准备 Python 环境、匹配 Chrome/Edge 驱动，并按单选题、多选题、判断题三个分区填写。

> 脚本不会自动点击“交卷”。题库更新或匹配度不足时会停在当前题，避免强行套用旧答案。

## 支持范围

| 平台 | 启动方式 | 状态 |
| --- | --- | --- |
| macOS | 双击 **一键运行.command**，或执行 **bash run.sh** | 已在 Apple Silicon、Chrome 151 和 Edge 151 验证 |
| Windows 10/11 | 双击 **一键运行.bat** | 已实现 PowerShell 自动安装流程和浏览器路径探测 |
| Linux 桌面版 | 执行 **bash run.sh**；部分文件管理器可直接双击 | 支持 Chrome、Chromium 和 Edge 路径探测 |
| iPhone/iPad/Android | 不支持 | 移动系统不能运行 Selenium 桌面浏览器环境 |

Windows 和 Linux 逻辑已通过静态检查与平台探测单元测试，但本仓库是在 macOS 上完成配置；首次在真实 Windows/Linux 设备使用时，建议先运行环境检查。

## 前置条件

- Python 3.9 或更高版本
- Google Chrome、Chromium 或 Microsoft Edge
- 能正常访问复旦统一身份认证和实验室安全考试系统

不需要手工下载 chromedriver 或 msedgedriver。Selenium Manager 会自动选择匹配驱动。

## 一键运行

### macOS

在 Finder 中双击 **一键运行.command**。

如果系统阻止打开，可右键该文件选择“打开”，或在终端执行：

~~~bash
cd /项目所在路径/Fudan_SafeTest
bash run.sh
~~~

仅检查环境、不进入考试：

~~~bash
bash run.sh --check
~~~

### Windows 10/11

在资源管理器中双击 **一键运行.bat**，也可以在 CMD 或 PowerShell 中执行：

~~~powershell
./一键运行.bat
~~~

仅检查环境：

~~~powershell
./一键运行.bat --check
~~~

批处理入口只会为本次进程临时使用 ExecutionPolicy Bypass，不会修改系统级 PowerShell 执行策略。

### Linux 桌面版

在项目目录执行：

~~~bash
bash run.sh
~~~

仅检查环境：

~~~bash
bash run.sh --check
~~~

若希望直接执行，可先运行一次：

~~~bash
chmod +x run.sh
./run.sh
~~~

## 首次运行流程

1. 检查 Python 版本。
2. 创建当前操作系统专用的虚拟环境。
3. 按 requirements.txt 安装固定版本依赖。
4. 从 environment_template.py 生成本地 environment.py。
5. 自动查找 Chrome/Chromium/Edge，并由 Selenium Manager 匹配驱动。
6. 打开独立浏览器资料目录，等待用户完成复旦统一身份认证。
7. 进入考试并逐题匹配、写入、回读和确认答案。
8. 填写完成后保持浏览器打开，由用户检查并手动交卷。

依赖只有在首次运行或 requirements.txt 变化时才会重新安装。

## 配置

本地配置文件为 environment.py，已加入 .gitignore。常用设置：

~~~python
browser_name = "chrome"       # chrome 或 edge
browser_binary = ""           # 留空自动探测
driver_path = ""              # 留空由 Selenium Manager 自动配置
profile_path = ""             # 留空按系统和浏览器自动隔离

login_wait_time = 300          # 登录最长等待秒数
page_wait_time = 30            # 页面操作超时
match_threshold = 78           # 题干最低可信度
option_match_threshold = 88    # 选项最低可信度
answer_delay = 0.35            # 每题确认后的等待时间
keep_browser_open = True       # 填完后保留浏览器
~~~

如果自动探测不到浏览器，可手工指定：

~~~python
# Windows 示例
browser_binary = "C:/Program Files/Google/Chrome/Application/chrome.exe"

# Linux 示例
browser_binary = "/usr/bin/google-chrome"
~~~

## 登录信息与隐私

- 脚本不会读取、记录或上传账号密码。
- 登录操作始终由用户在复旦统一身份认证页面完成。
- 登录状态按系统和浏览器隔离保存在 .browser-profile/。
- Python 依赖保存在本机虚拟环境中。
- 浏览器资料、虚拟环境和 environment.py 均不会被 Git 提交。
- 切勿把浏览器资料目录或 Cookie 文件发送给他人。

若要重置登录状态，请先关闭 SafeTest 启动的浏览器，再删除 .browser-profile/。

## 题库与匹配策略

默认题库位于 asset/questions.json，当前包含 100 条记录，来自 2026-08-27 完成的校级考试卷（单选 30 题、多选 40 题、判断 30 题）。脚本会：

1. 去除题号、空格和常见标点后匹配题干。
2. 再次独立匹配页面选项。
3. 写入并回读校验单选、多选和判断题控件。
4. 点击“确定”保存当前题。
5. 匹配度低于阈值时立即停止并保留浏览器。

题库可能落后于最新考试。遇到新题时应人工核对，不建议为了继续运行而盲目降低阈值。

已有考试结果页时，可尝试合并题目：

~~~bash
python load_question.py
~~~

合并时，同一题干以最新结果页中的选项和正确答案为准。若只想保留当前完成的这一套试卷：

~~~bash
python load_question.py --replace
~~~

写入前会检查重复题干、空题干、空选项、空答案及“正确答案不在选项中”等异常；解析或校验失败时不会写入题库。

## 环境检查与测试

环境检查会启动本地浏览器测试页，但不会打开或进入考试：

~~~bash
# macOS / Linux
bash run.sh --check

# Windows
./一键运行.bat --check
~~~

开发测试使用 Python 标准库 unittest：

~~~bash
python -m unittest discover -s tests -v
~~~

测试覆盖浏览器路径探测、登录入口识别、成绩详情页解析、题库新旧记录合并、题干规范化和全部内置题库答案映射。

## 常见问题

### 提示未找到 Python

- macOS：安装 Python 3，或设置 SAFETEST_PYTHON 为 Python 可执行文件。
- Windows：从 [python.org](https://www.python.org/downloads/) 安装，并勾选 Add Python to PATH。
- Ubuntu/Debian：安装 python3、python3-venv 和 python3-pip。

### 提示未自动找到浏览器

安装 Chrome/Chromium/Edge，或在 environment.py 中设置 browser_binary 的完整路径。

### 浏览器资料目录正在使用

关闭此前由 SafeTest 打开的浏览器窗口和终端，再重新运行。不要同时启动两个 SafeTest 实例。

### 驱动下载失败

确认网络可访问浏览器驱动下载源后重试；也可以手工下载匹配驱动，并通过 driver_path 指定。

### 脚本在某道题停止

这通常表示题库没有对应的新题，或页面选项已修改。浏览器会保留在当前题，请人工处理并更新题库。

## 项目结构

| 文件 | 用途 |
| --- | --- |
| main.py | 命令行入口、环境检查和答题流程 |
| cookie_engine.py | 跨平台浏览器探测、独立资料目录和登录等待 |
| operation_engine.py | 题型切换、题目匹配、选项校验与写入 |
| question_engine.py | 题库读写与合并 |
| environment_template.py | 默认配置模板 |
| requirements.txt | 固定 Python 依赖 |
| run.sh | macOS/Linux 自动启动器 |
| run.ps1 | Windows PowerShell 自动启动器 |
| 一键运行.command | macOS 双击入口 |
| 一键运行.bat | Windows 双击入口 |
| tests/ | 跨平台探测和题库匹配测试 |

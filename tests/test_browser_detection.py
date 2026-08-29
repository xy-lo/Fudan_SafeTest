import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import environment  # noqa: F401
except ModuleNotFoundError:
    import environment_template

    sys.modules["environment"] = environment_template

import cookie_engine


class BrowserDetectionTests(unittest.TestCase):
    def test_exam_site_detection_requires_exam_application_path(self):
        class Browser:
            current_url = "https://lsem.fudan.edu.cn/fd_aqks_new/index"

        self.assertTrue(cookie_engine._on_fudan_exam_site(Browser()))
        Browser.current_url = "https://lsem.fudan.edu.cn/wz/websit/index.jsp"
        self.assertFalse(cookie_engine._on_fudan_exam_site(Browser()))
        Browser.current_url = "https://id.fudan.edu.cn/ac/"
        self.assertFalse(cookie_engine._on_fudan_exam_site(Browser()))

    def test_exam_login_entry_uses_application_root(self):
        self.assertEqual(
            cookie_engine._exam_login_entry(
                "https://lsem.fudan.edu.cn/fd_aqks_new/"
                "examProgress/examBase/examIndex"
            ),
            "https://lsem.fudan.edu.cn/fd_aqks_new/index",
        )

    def test_configured_browser_path_takes_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "browser"
            executable.touch()
            result = cookie_engine._browser_executable(
                "chrome",
                str(executable),
            )
            self.assertEqual(result, executable.resolve())

    @patch("cookie_engine.shutil.which", return_value=None)
    @patch("cookie_engine.platform.system", return_value="Darwin")
    def test_macos_candidates(self, _system, _which):
        candidates = cookie_engine._browser_candidates("chrome")
        self.assertIn(
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            candidates,
        )

    @patch("cookie_engine.shutil.which", return_value=None)
    @patch("cookie_engine.platform.system", return_value="Windows")
    @patch.dict(
        os.environ,
        {
            "PROGRAMFILES": "C:/Program Files",
            "PROGRAMFILES(X86)": "C:/Program Files (x86)",
            "LOCALAPPDATA": "C:/Users/test/AppData/Local",
        },
    )
    def test_windows_candidates(self, _system, _which):
        candidates = cookie_engine._browser_candidates("edge")
        rendered = [str(item).replace("\\", "/") for item in candidates]
        self.assertTrue(
            any(
                item.endswith("Microsoft/Edge/Application/msedge.exe")
                for item in rendered
            )
        )

    @patch("cookie_engine.platform.system", return_value="Linux")
    @patch(
        "cookie_engine.shutil.which",
        side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None,
    )
    def test_linux_path_lookup(self, _which, _system):
        candidates = cookie_engine._browser_candidates("chrome")
        self.assertIn(Path("/usr/bin/chromium"), candidates)


if __name__ == "__main__":
    unittest.main()

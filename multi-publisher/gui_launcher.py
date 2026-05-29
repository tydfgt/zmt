#!/usr/bin/env python3
"""
多平台内容分发工具 - Qt GUI 启动器

用法:
    python gui_launcher.py
"""

import sys
import os
from pathlib import Path

# 确保能找到 publisher 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MultiPublisher")
    app.setOrganizationName("zmt")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

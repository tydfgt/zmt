"""
多平台内容分发工具 - Qt GUI 主界面

运行方式:
    python gui_launcher.py
    或
    cd multi-publisher && python -m gui.main_window
"""

import sys
import os
import threading
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QCheckBox, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QSplitter, QApplication,
    QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QWaitCondition
from PyQt5.QtGui import QFont, QIcon, QTextCursor


# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from publisher.converter import ArticleProcessor
from publisher.platforms.cnblogs import CnblogsPlatform
from publisher.platforms.oschina import OschinaPlatform
from publisher.platforms.wechat import WechatPlatform
from publisher.platforms.zhihu import ZhihuPlatform
from publisher.platforms.xiaohongshu import XiaohongshuPlatform

# ---- 平台注册表 ----
PLATFORMS = [
    ("cnblogs",     "博客园",     CnblogsPlatform),
    ("oschina",     "开源中国",   OschinaPlatform),
    ("wechat",      "微信公众号", WechatPlatform),
    ("zhihu",       "知乎",       ZhihuPlatform),
    ("xiaohongshu", "小红书",     XiaohongshuPlatform),
]


# ============================================================
# 发布线程
# ============================================================

class PublishThread(QThread):
    """后台发布线程，避免阻塞 UI"""
    log_signal = pyqtSignal(str)          # 实时日志
    done_signal = pyqtSignal(str)         # 完成摘要
    progress_signal = pyqtSignal(int, int) # 当前/总数

    def __init__(self, md_file: str, platforms: list, optimize: bool, dry_run: bool, config: dict):
        super().__init__()
        self.md_file = md_file
        self.platforms = platforms
        self.optimize = optimize
        self.dry_run = dry_run
        self.config = config

    def run(self):
        md_text = Path(self.md_file).read_text(encoding="utf-8")
        processor = ArticleProcessor(self.config)
        total = len(self.platforms)
        results = []

        for i, plat_key in enumerate(self.platforms):
            label = next((l for k, l, _ in PLATFORMS if k == plat_key), plat_key)
            self.log_signal.emit(f"⏳ [{label}] 正在转换格式...")
            self.progress_signal.emit(i + 1, total)

            # 转换
            try:
                convert_result = processor.convert(md_text, plat_key,
                                                   optimize=self.optimize)
            except Exception as e:
                self.log_signal.emit(f"❌ [{label}] 转换失败: {e}")
                continue

            # 发布
            if self.dry_run:
                self.log_signal.emit(f"🔍 [{label}] 模拟发布: {len(convert_result.content)} 字符")
                results.append(f"✅ [{label}] 模拟完成")
            else:
                _, cls = [(k, c) for k, _, c in PLATFORMS if k == plat_key][0]
                platform = cls(self.config.get(plat_key, {}))
                try:
                    pub_result = platform.publish(convert_result)
                    if pub_result.success:
                        self.log_signal.emit(f"✅ [{label}] {pub_result.message.split(chr(10))[0]}")
                        results.append(f"✅ [{label}] 成功")
                    else:
                        self.log_signal.emit(f"❌ [{label}] {pub_result.message}")
                        results.append(f"❌ [{label}] 失败")
                except Exception as e:
                    self.log_signal.emit(f"❌ [{label}] 异常: {e}")
                    results.append(f"❌ [{label}] 异常")

        self.progress_signal.emit(total, total)
        self.done_signal.emit("\n".join(results) or "没有可发布的平台")


# ============================================================
# 主窗口
# ============================================================

class MainWindow(QMainWindow):
    TITLE = "🚀 多平台内容分发工具"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.TITLE)
        self.resize(1100, 720)

        # 加载配置
        self.config = self._load_config()
        self._thread = None

        # 构建 UI
        self._build_ui()
        self._apply_style()

        # 状态栏
        self.statusBar().showMessage("就绪 · 选择一个 Markdown 文件开始")

    # ================================================================
    # 配置
    # ================================================================

    def _load_config(self) -> dict:
        cfg_path = PROJECT_ROOT / "config.yaml"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _reload_config(self):
        self.config = self._load_config()
        self.statusBar().showMessage("配置已重新加载")

    # ================================================================
    # UI 构建
    # ================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ---- 顶部：文件选择 ----
        file_box = QHBoxLayout()
        file_box.addWidget(QLabel("📄 文章:"))
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择 Markdown 文件...")
        file_box.addWidget(self.file_edit)
        btn_browse = QPushButton("浏览...")
        btn_browse.clicked.connect(self._browse_file)
        file_box.addWidget(btn_browse)
        btn_reload = QPushButton("🔄 重载配置")
        btn_reload.clicked.connect(self._reload_config)
        file_box.addWidget(btn_reload)
        root.addLayout(file_box)

        # ---- 中部：平台勾选 + 预览 + 控制 ----
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：平台勾选
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        platform_group = QGroupBox("目标平台")
        pf_layout = QVBoxLayout(platform_group)
        self.platform_checks = {}
        for key, label, _ in PLATFORMS:
            cb = QCheckBox(label)
            cb.setChecked(self.config.get(key, {}).get("enabled", False))
            pf_layout.addWidget(cb)
            self.platform_checks[key] = cb
        pf_layout.addStretch()
        left_layout.addWidget(platform_group)

        # 发布选项
        options_group = QGroupBox("选项")
        opt_layout = QVBoxLayout(options_group)
        self.opt_optimize = QCheckBox("🧠 DeepSeek AI 优化")
        self.opt_optimize.setToolTip("用 AI 按平台风格改写文章（需在 config.yaml 配置 api_key）")
        opt_layout.addWidget(self.opt_optimize)
        self.opt_dryrun = QCheckBox("🔍 试运行（不真正发布）")
        self.opt_dryrun.setChecked(True)
        opt_layout.addWidget(self.opt_dryrun)
        left_layout.addWidget(options_group)

        # 发布按钮
        self.btn_publish = QPushButton("🚀 一键发布")
        self.btn_publish.setMinimumHeight(44)
        self.btn_publish.clicked.connect(self._publish)
        left_layout.addWidget(self.btn_publish)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        left_layout.addWidget(self.progress)

        splitter.addWidget(left_panel)

        # 中间：预览区
        preview_group = QGroupBox("内容预览")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Noto Sans Mono", 11))
        preview_layout.addWidget(self.preview)
        btn_preview = QPushButton("👁 预览选中平台格式")
        btn_preview.clicked.connect(self._preview)
        preview_layout.addWidget(btn_preview)
        splitter.addWidget(preview_group)

        # 右侧：日志区
        log_group = QGroupBox("发布日志")
        log_layout = QVBoxLayout(log_group)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Noto Sans Mono", 10))
        log_layout.addWidget(self.log_view)
        btn_clear = QPushButton("清空日志")
        btn_clear.clicked.connect(lambda: self.log_view.clear())
        log_layout.addWidget(btn_clear)
        splitter.addWidget(log_group)

        splitter.setSizes([280, 400, 400])
        root.addWidget(splitter)

        # ---- 底部：快捷按钮 ----
        bottom = QHBoxLayout()
        btn_check = QPushButton("✅ 检查配置")
        btn_check.clicked.connect(self._check_config)
        bottom.addWidget(btn_check)
        bottom.addStretch()
        btn_about = QPushButton("关于")
        btn_about.clicked.connect(self._about)
        bottom.addWidget(btn_about)
        root.addLayout(bottom)

    # ================================================================
    # 操作
    # ================================================================

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Markdown 文件",
            str(Path.home()), "Markdown (*.md *.markdown);;全部文件 (*)"
        )
        if path:
            self.file_edit.setText(path)
            self._preview()
            self.statusBar().showMessage(f"已加载: {path}")

    def _selected_platforms(self) -> list:
        return [k for k, cb in self.platform_checks.items() if cb.isChecked()]

    def _preview(self):
        md_file = self.file_edit.text().strip()
        if not md_file or not Path(md_file).exists():
            self.preview.setPlainText("请先选择一个有效的 Markdown 文件")
            return
        platforms = self._selected_platforms()
        if not platforms:
            self.preview.setPlainText("请至少选择一个目标平台")
            return

        md_text = Path(md_file).read_text(encoding="utf-8")
        processor = ArticleProcessor(self.config)
        # 预览第一个选中平台的格式
        plat = platforms[0]
        label = next((l for k, l, _ in PLATFORMS if k == plat), plat)
        try:
            result = processor.convert(md_text, plat, optimize=self.opt_optimize.isChecked())
            preview_text = result.content
            if len(preview_text) > 10000:
                preview_text = preview_text[:10000] + f"\n\n... (共 {len(result.content)} 字符，已截断)"
            self.preview.setPlainText(preview_text)
            self.statusBar().showMessage(f"预览 [{label}] · {len(result.content)} 字符")
        except Exception as e:
            self.preview.setPlainText(f"预览失败: {e}")

    def _publish(self):
        md_file = self.file_edit.text().strip()
        if not md_file or not Path(md_file).exists():
            QMessageBox.warning(self, "错误", "请先选择一个 Markdown 文件")
            return

        platforms = self._selected_platforms()
        if not platforms:
            QMessageBox.warning(self, "错误", "请至少选择一个目标平台")
            return

        self.btn_publish.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(platforms))
        self.progress.setValue(0)
        self.log_view.clear()

        self._thread = PublishThread(
            md_file=md_file,
            platforms=platforms,
            optimize=self.opt_optimize.isChecked(),
            dry_run=self.opt_dryrun.isChecked(),
            config=self.config,
        )
        self._thread.log_signal.connect(self._on_log)
        self._thread.progress_signal.connect(self._on_progress)
        self._thread.done_signal.connect(self._on_done)
        self._thread.start()

    def _on_log(self, msg: str):
        self.log_view.append(msg)
        # 自动滚到底部
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_view.setTextCursor(cursor)

    def _on_progress(self, current: int, total: int):
        self.progress.setValue(current)

    def _on_done(self, summary: str):
        self.btn_publish.setEnabled(True)
        self.progress.setVisible(False)
        self.log_view.append(f"\n{'='*50}\n{summary}")
        self.statusBar().showMessage("完成")

    def _check_config(self):
        self._reload_config()
        msg_lines = ["配置检查结果:\n"]
        for key, label, cls in PLATFORMS:
            plat_cfg = self.config.get(key, {})
            platform = cls(plat_cfg)
            enabled = plat_cfg.get("enabled", False)
            missing = platform.validate_config()
            if not enabled:
                msg_lines.append(f"  ❌ {label}: 未启用")
            elif missing:
                msg_lines.append(f"  ⚠️ {label}: 缺少 {'/'.join(missing)}")
            else:
                msg_lines.append(f"  ✅ {label}: 配置完整")
        # DeepSeek
        ds = self.config.get("deepseek", {})
        if ds.get("api_key") and ds["api_key"] != "你的DeepSeek_API_Key":
            msg_lines.append(f"  ✅ DeepSeek AI: 已配置")
        else:
            msg_lines.append(f"  ⚠️ DeepSeek AI: 未配置 API Key")
        QMessageBox.information(self, "配置检查", "\n".join(msg_lines))

    def _about(self):
        QMessageBox.about(self, "关于",
            "🚀 多平台内容分发工具 v0.2\n\n"
            "一文编写，多平台分发\n"
            "Markdown → 博客园 · 开源中国 · 微信公众号 · 知乎 · 小红书\n\n"
            "支持 DeepSeek AI 智能优化\n"
            "https://github.com/tydfgt/zmt"
        )

    # ================================================================
    # 样式
    # ================================================================

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #1e1e2e; }
            QWidget { color: #cdd6f4; font-size: 13px; }
            QGroupBox {
                border: 1px solid #45475a; border-radius: 8px;
                margin-top: 12px; padding-top: 18px;
                font-weight: bold; color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }
            QPushButton {
                background: #45475a; border: none; border-radius: 6px;
                padding: 8px 16px; color: #cdd6f4; font-weight: bold;
            }
            QPushButton:hover { background: #585b70; }
            QPushButton:pressed { background: #6c7086; }
            QPushButton#publish_btn {
                background: #89b4fa; color: #1e1e2e; font-size: 15px;
            }
            QPushButton#publish_btn:hover { background: #b4d0fb; }
            QLineEdit, QTextEdit {
                background: #313244; border: 1px solid #45475a;
                border-radius: 6px; padding: 6px; color: #cdd6f4;
            }
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator {
                width: 18px; height: 18px; border-radius: 4px;
                border: 2px solid #585b70;
            }
            QCheckBox::indicator:checked { background: #89b4fa; border-color: #89b4fa; }
            QProgressBar {
                border: 1px solid #45475a; border-radius: 6px;
                text-align: center; background: #313244; color: #cdd6f4;
            }
            QProgressBar::chunk { background: #89b4fa; border-radius: 4px; }
            QStatusBar { color: #6c7086; }
            QSplitter::handle { background: #45475a; width: 2px; }
        """)
        # 给发布按钮特殊 ID
        self.btn_publish.setObjectName("publish_btn")

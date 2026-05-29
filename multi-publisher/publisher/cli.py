"""
CLI 命令行入口 —— 多平台一键分发工具

用法:
    # 一键分发到所有平台
    python -m publisher.cli publish article.md --all

    # 分发到指定平台
    python -m publisher.cli publish article.md -p cnblogs -p oschina

    # 仅转换不发布（预览）
    python -m publisher.cli convert article.md -p wechat

    # 检查各平台配置状态
    python -m publisher.cli check

    # 生成示例文章
    python -m publisher.cli init
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .converter import ArticleProcessor
from .platforms.cnblogs import CnblogsPlatform
from .platforms.oschina import OschinaPlatform
from .platforms.wechat import WechatPlatform
from .platforms.zhihu import ZhihuPlatform
from .platforms.xiaohongshu import XiaohongshuPlatform


console = Console()

# 平台注册表
PLATFORM_MAP = {
    "cnblogs":    (CnblogsPlatform,    "博客园"),
    "oschina":    (OschinaPlatform,    "开源中国"),
    "wechat":     (WechatPlatform,     "微信公众号"),
    "zhihu":      (ZhihuPlatform,      "知乎"),
    "xiaohongshu":(XiaohongshuPlatform,"小红书"),
}


def load_config(config_path: str = "config.yaml") -> dict:
    """加载 YAML 配置文件"""
    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]❌ 配置文件不存在: {config_path}[/red]")
        console.print(f"[yellow]💡 请复制 config.yaml.example 并修改配置[/yellow]")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_platform(name: str, config: dict):
    """根据名称获取平台实例"""
    cls, _ = PLATFORM_MAP[name]
    plat_cfg = config.get(name, {})
    return cls(plat_cfg)


# ============================================================
# CLI 命令
# ============================================================

@click.group()
@click.option("--config", "-c", default="config.yaml", help="配置文件路径")
@click.pass_context
def cli(ctx, config):
    """🚀 多平台内容分发工具 - 一文多发，省时省力"""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["config"] = load_config(config)


@cli.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--platform", "-p", "platforms", multiple=True,
              type=click.Choice(list(PLATFORM_MAP.keys())),
              help="目标平台（可多选）")
@click.option("--all", "-a", "all_platforms", is_flag=True,
              help="发布到所有已启用的平台")
@click.option("--dry-run", is_flag=True, help="仅模拟，不实际发布")
@click.option("--optimize/--no-optimize", default=False,
              help="使用 DeepSeek AI 优化文章（需在 config.yaml 配置 api_key）")
@click.pass_context
def publish(ctx, markdown_file, platforms, all_platforms, dry_run, optimize):
    """
    发布 Markdown 文章到各平台。

    \b
    示例:
      python -m publisher.cli publish article.md -p cnblogs -p oschina
      python -m publisher.cli publish article.md --all
      python -m publisher.cli publish article.md --all --dry-run
    """
    config = ctx.obj["config"]
    md_text = Path(markdown_file).read_text(encoding="utf-8")
    processor = ArticleProcessor(config)

    # 确定目标平台
    if all_platforms:
        targets = [name for name, (cls, _) in PLATFORM_MAP.items()
                   if config.get(name, {}).get("enabled", True)]
    elif platforms:
        targets = list(platforms)
    else:
        console.print("[red]❌ 请指定目标平台：-p cnblogs 或 --all[/red]")
        sys.exit(1)

    if not targets:
        console.print("[yellow]⚠️ 没有启用的平台[/yellow]")
        return

    # 展示发布计划
    optimize_label = "[cyan]🧠 AI 优化[/cyan]" if optimize else "[dim]无优化[/dim]"
    console.print(Panel.fit(
        f"[bold cyan]📝 {Path(markdown_file).name}[/bold cyan]\n"
        f"目标平台: {', '.join(PLATFORM_MAP[p][1] for p in targets)}\n"
        f"模式: {'[yellow]DRY RUN (模拟)[/yellow]' if dry_run else '[green]正式发布[/green]'} · {optimize_label}",
        title="发布计划"
    ))

    # 逐平台发布
    results_table = Table(title="发布结果")
    results_table.add_column("平台", style="cyan")
    results_table.add_column("状态", style="bold")
    results_table.add_column("详情")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for plat_name in targets:
            plat_label = PLATFORM_MAP[plat_name][1]
            task = progress.add_task(f"正在处理 {plat_label}...", total=None)

            # 转换
            convert_result = processor.convert(md_text, plat_name, optimize=optimize)

            # 发布（或模拟）
            if dry_run:
                from .platforms.base import PublishResult
                pub_result = PublishResult(
                    success=True, platform=plat_name,
                    message=f"✅ [模拟] 将发布 {len(convert_result.content)} 字符到 {plat_label}"
                )
            else:
                platform = get_platform(plat_name, config)
                pub_result = platform.publish(convert_result)

            # 显示结果
            status = "[green]✅ 成功[/green]" if pub_result.success else "[red]❌ 失败[/red]"
            detail = pub_result.message
            if pub_result.url:
                detail += f"\n   🔗 {pub_result.url}"

            results_table.add_row(plat_label, status, detail)
            progress.remove_task(task)

    console.print(results_table)


@cli.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--platform", "-p", "platform", required=True,
              type=click.Choice(list(PLATFORM_MAP.keys())),
              help="目标平台")
@click.option("--output", "-o", help="输出文件路径（默认自动生成）")
@click.option("--optimize/--no-optimize", default=False,
              help="使用 DeepSeek AI 优化文章")
@click.pass_context
def convert(ctx, markdown_file, platform, output, optimize):
    """
    仅转换格式，不发布（用于预览或手动发布）。

    \b
    示例:
      python -m publisher.cli convert article.md -p wechat
      python -m publisher.cli convert article.md -p zhihu -o zhihu_output.md
    """
    config = ctx.obj["config"]
    md_text = Path(markdown_file).read_text(encoding="utf-8")
    processor = ArticleProcessor(config)

    convert_result = processor.convert(md_text, platform, optimize=optimize)

    if not output:
        ext = "html" if platform == "wechat" else "md"
        output = f"output/{platform}/{Path(markdown_file).stem}.{ext}"

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(convert_result.content, encoding="utf-8")

    console.print(f"[green]✅ 已转换并保存至: {out_path}[/green]")
    console.print(f"[dim]字符数: {len(convert_result.content)}[/dim]")


@cli.command()
@click.pass_context
def check(ctx):
    """
    检查各平台配置和连通性。
    """
    config = ctx.obj["config"]

    table = Table(title="平台配置检查")
    table.add_column("平台", style="cyan")
    table.add_column("启用", style="bold")
    table.add_column("配置状态")
    table.add_column("连通性")

    for plat_name, (cls, label) in PLATFORM_MAP.items():
        plat_cfg = config.get(plat_name, {})
        enabled = plat_cfg.get("enabled", False)
        platform = cls(plat_cfg)

        # 配置检查
        missing = platform.validate_config()
        if not enabled:
            config_status = "[dim]未启用[/dim]"
        elif missing:
            config_status = f"[yellow]缺少: {', '.join(missing)}[/yellow]"
        else:
            config_status = "[green]✅ 完整[/green]"

        # 连通性检查
        if not enabled:
            connectivity = "[dim]—[/dim]"
        elif missing:
            connectivity = "[dim]跳过（配置不完整）[/dim]"
        else:
            try:
                ok = platform.pre_check()
                connectivity = "[green]✅ 可达[/green]" if ok else "[yellow]⚠️ 未验证[/yellow]"
            except Exception as e:
                connectivity = f"[red]❌ {str(e)[:50]}[/red]"

        table.add_row(label, "✅" if enabled else "❌", config_status, connectivity)

    # ---- DeepSeek 优化器状态 ----
    from .optimizer import create_optimizer
    opt = create_optimizer(config)
    ds_cfg = config.get("deepseek", {})
    if opt:
        table.add_row("🧠 DeepSeek AI", "✅", "[green]✅ 已配置[/green]", "[green]就绪[/green]")
    elif ds_cfg.get("api_key", "") and ds_cfg["api_key"] != "你的DeepSeek_API_Key":
        table.add_row("🧠 DeepSeek AI", "✅", "[yellow]API Key 可能无效[/yellow]", "[dim]—[/dim]")
    else:
        table.add_row("🧠 DeepSeek AI", "❌", "[dim]未配置 API Key[/dim]", "[dim]跳过[/dim]")

    console.print(table)


@cli.command()
def init():
    """
    生成示例配置文件和示例文章，快速上手。
    """
    import shutil

    base = Path(__file__).parent.parent

    # 示例文章
    sample_md = base / "templates" / "sample_article.md"
    sample_md.parent.mkdir(parents=True, exist_ok=True)

    sample_content = """---
title: 如何用 Python 搭建自动化工作流
tags: [Python, 自动化, 效率工具, 教程]
categories: [技术, 编程]
summary: 手把手教你用 Python 搭建日常自动化工作流，告别重复劳动
date: 2026-05-29
---

## 前言

在日常工作和生活中，我们经常会遇到一些重复性的任务：批量重命名文件、定时发送邮件、自动整理数据等等。这些任务虽然简单，但手动操作耗时且容易出错。

本文将教你如何使用 Python 搭建一套自动化工作流，让你的效率翻倍 🚀

## 核心思路

自动化工作流的核心可以概括为三个步骤：

| 步骤 | 说明 | 常用工具 |
|------|------|----------|
| 触发 | 什么时候执行？ | cron / schedule / 文件监控 |
| 执行 | 做什么事情？ | Python 脚本 |
| 通知 | 结果怎么告知？ | 邮件 / 微信 / 日志 |

## 实战案例：自动备份脚本

```python
import os
import shutil
from datetime import datetime

def backup_folder(source, target):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = os.path.join(target, backup_name)

    shutil.copytree(source, backup_path)
    print(f"✅ 备份完成: {backup_path}")
    return backup_path

if __name__ == "__main__":
    backup_folder("./data", "./backups")
```

## 定时执行

在 Linux/macOS 上使用 `cron`：

```bash
# 每天凌晨 2 点自动备份
0 2 * * * python /path/to/backup.py
```

## 总结

自动化工作流的本质是**让机器做重复的事，让人做创造的事**。从简单的脚本开始，逐步完善，你会发现编程的乐趣远不止写代码本身。

---

> 💡 完整代码已开源在 GitHub，欢迎 Star！
"""

    sample_md.write_text(sample_content, encoding="utf-8")
    console.print(f"[green]✅ 示例文章已生成: {sample_md}[/green]")

    # 提示
    console.print(Panel.fit(
        "[bold]🚀 快速开始:[/bold]\n\n"
        "1. 编辑 [cyan]config.yaml[/cyan] 填入各平台密钥\n"
        "2. 运行 [cyan]python -m publisher.cli check[/cyan] 检查配置\n"
        "3. 运行 [cyan]python -m publisher.cli publish templates/sample_article.md --all --dry-run[/cyan] 模拟发布\n"
        "4. 确认无误后去掉 [cyan]--dry-run[/cyan] 正式发布\n\n"
        "[bold]📦 安装依赖:[/bold]\n"
        "   [cyan]pip install -r requirements.txt[/cyan]",
        title="初始化完成"
    ))


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    cli()

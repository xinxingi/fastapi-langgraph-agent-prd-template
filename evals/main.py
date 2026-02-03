#!/usr/bin/env python3
"""运行评估的命令行界面。"""

import argparse
import asyncio
import os
import sys
from typing import (
    Any,
    Dict,
    Optional,
)

import colorama
from colorama import (
    Fore,
    Style,
)
from tqdm import tqdm

# 修复app模块的导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings
from app.core.logging import logger
from evals.evaluator import Evaluator

# 默认配置
DEFAULT_CONFIG = {
    "generate_report": True,
    "model": settings.EVALUATION_LLM,
    "api_base": settings.EVALUATION_BASE_URL,
}


def print_title(title: str) -> None:
    """打印带颜色的格式化标题。

    Args:
        title: 要打印的标题文本
    """
    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(60)}{Style.RESET_ALL}")
    print("=" * 60 + "\n")


def print_info(message: str) -> None:
    """打印带颜色的信息消息。

    Args:
        message: 要打印的消息
    """
    print(f"{Fore.GREEN}• {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """打印带颜色的警告消息。

    Args:
        message: 要打印的消息
    """
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """打印带颜色的错误消息。

    Args:
        message: 要打印的消息
    """
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_success(message: str) -> None:
    """打印带颜色的成功消息。

    Args:
        message: 要打印的消息
    """
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def get_user_input(prompt: str, default: Optional[str] = None) -> str:
    """获取带颜色提示的用户输入。

    Args:
        prompt: 要显示的提示
        default: 用户按回车时的默认值

    Returns:
        用户输入或默认值
    """
    default_text = f" [{default}]" if default else ""
    user_input = input(f"{Fore.BLUE}{prompt}{default_text}: {Style.RESET_ALL}")
    return user_input if user_input else default


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """从用户获取是/否响应。

    Args:
        prompt: 要显示的提示
        default: 用户按回车时的默认值

    Returns:
        是为True，否为False
    """
    default_value = "Y/n" if default else "y/N"
    response = get_user_input(f"{prompt} {default_value}")

    if not response:
        return default

    return response.lower() in ("y", "yes")


def display_summary(report: Dict[str, Any]) -> None:
    """显示评估结果摘要。

    Args:
        report: 评估报告
    """
    print_title("Evaluation Summary")

    print(f"{Fore.CYAN}Model:{Style.RESET_ALL} {report['model']}")
    print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {report['duration_seconds']} seconds")
    print(f"{Fore.CYAN}Total Traces:{Style.RESET_ALL} {report['total_traces']}")

    success_rate = 0
    if report["total_traces"] > 0:
        success_rate = (report["successful_traces"] / report["total_traces"]) * 100

    if success_rate > 80:
        status_color = Fore.GREEN
    elif success_rate > 50:
        status_color = Fore.YELLOW
    else:
        status_color = Fore.RED

    print(
        f"{Fore.CYAN}Success Rate:{Style.RESET_ALL} {status_color}{success_rate:.1f}%{Style.RESET_ALL} ({report['successful_traces']}/{report['total_traces']})"
    )

    print("\n" + f"{Fore.CYAN}Metrics Summary:{Style.RESET_ALL}")
    for metric_name, data in report["metrics_summary"].items():
        total = data["success_count"] + data["failure_count"]
        success_percent = 0
        if total > 0:
            success_percent = (data["success_count"] / total) * 100

        if success_percent > 80:
            status_color = Fore.GREEN
        elif success_percent > 50:
            status_color = Fore.YELLOW
        else:
            status_color = Fore.RED

        print(
            f"  • {metric_name}: {status_color}{success_percent:.1f}%{Style.RESET_ALL} success, avg score: {data['avg_score']:.2f}"
        )

    if report["generate_report_path"]:
        print(f"\n{Fore.CYAN}Report generated at:{Style.RESET_ALL} {report['generate_report_path']}")


async def run_evaluation(generate_report: bool = True) -> None:
    """运行评估过程。

    Args:
        generate_report: 是否生成JSON报告
    """
    print_title("Starting Evaluation")
    print_info(f"Using model: {settings.EVALUATION_LLM}")
    print_info(f"Report generation: {'Enabled' if generate_report else 'Disabled'}")

    try:
        evaluator = Evaluator()
        await evaluator.run(generate_report_file=generate_report)

        print_success("Evaluation completed successfully!")

        # 显示结果摘要
        display_summary(evaluator.report)

    except Exception as e:
        print_error(f"Evaluation failed: {str(e)}")
        logger.error("Evaluation failed", error=str(e))
        sys.exit(1)


def display_configuration(config: Dict[str, Any]) -> None:
    """显示当前配置。

    Args:
        config: 配置字典
    """
    print_title("Configuration")
    print_info(f"Model: {config['model']}")
    print_info(f"API Base: {config['api_base']}")
    print_info(f"Generate Report: {'Yes' if config['generate_report'] else 'No'}")


def interactive_mode() -> None:
    """以交互模式运行评估器。"""
    colorama.init()

    # 使用默认值创建配置
    config = DEFAULT_CONFIG.copy()

    print_title("Evaluation Runner")
    print_info("Welcome to the Evaluation Runner!")
    print_info("Press Enter to accept default values or input your own.")

    # 显示当前配置
    display_configuration(config)

    print("\n" + f"{Fore.CYAN}Configuration Options (press Enter to accept defaults):{Style.RESET_ALL}")

    # 允许用户更改配置或接受默认值
    change_config = get_yes_no("Would you like to change the default configuration?", default=False)

    if change_config:
        config["generate_report"] = get_yes_no("Generate JSON report?", default=config["generate_report"])

    print("\n")
    confirm = get_yes_no("Ready to start evaluation with these settings?", default=True)

    if confirm:
        asyncio.run(run_evaluation(generate_report=config["generate_report"]))
    else:
        print_warning("Evaluation canceled.")


def quick_mode() -> None:
    """使用所有默认设置运行评估器。"""
    colorama.init()
    print_title("Quick Evaluation")
    print_info("Running evaluation with default settings...")
    print_info("(Press Ctrl+C to cancel)")

    # 显示默认值
    display_configuration(DEFAULT_CONFIG)

    try:
        asyncio.run(run_evaluation(generate_report=DEFAULT_CONFIG["generate_report"]))
    except KeyboardInterrupt:
        print_warning("\nEvaluation canceled by user.")
        sys.exit(0)


def main() -> None:
    """命令行界面的主入口点。"""
    parser = argparse.ArgumentParser(description="Run evaluations on model outputs")
    parser.add_argument("--no-report", action="store_true", help="Don't generate a JSON report")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--quick", action="store_true", help="Run with all default settings (no prompts)")

    args = parser.parse_args()

    if args.quick:
        quick_mode()
    elif args.interactive:
        interactive_mode()
    else:
        # 使用命令行参数运行
        asyncio.run(run_evaluation(generate_report=not args.no_report))


if __name__ == "__main__":
    main()

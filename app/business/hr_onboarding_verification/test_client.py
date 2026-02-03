"""HR入职文件质量核验功能测试脚本。

此脚本演示如何使用HR入职文件质量核验API。
"""

import asyncio

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def test_hr_verification():
    """测试HR入职文件质量核验功能。"""
    # 测试数据 - 银行卡核验示例
    test_request = {
        "base_info": {"银行卡号": "672557939300853852", "发薪银行": "中国工商银行"},
        "quality_inspection_type": "BANK_CARD",
        "urls": ["https://ys-app.obs.cn-east-3.myhuaweicloud.com/aaa/1111/cccc/1.png"],
        "enable_thinking": True,
    }

    # API端点
    api_url = "http://localhost:8000/api/v1/hr_onboarding_verification/qc"

    console.print(Panel.fit("[bold cyan]HR入职文件质量核验测试[/bold cyan]", border_style="cyan"))

    console.print("\n[yellow]发送请求...[/yellow]")
    console.print(f"URL: {api_url}")
    console.print(f"类型: {test_request['quality_inspection_type']}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                json=test_request,
            )

            if response.status_code == 200:
                result = response.json()

                # 显示结果
                console.print(f"\n[green]✓ 请求成功![/green]")
                console.print(f"整体通过: {'[green]是[/green]' if result['is_all_passed'] else '[red]否[/red]'}")

                # 创建结果表格
                table = Table(title="核验结果详情", show_header=True, header_style="bold magenta")
                table.add_column("质检项", style="cyan")
                table.add_column("提取内容", style="yellow")
                table.add_column("异常信息", style="red")

                for item in result["results"]:
                    table.add_row(
                        item["rule_item_name"],
                        item["extracted_content"],
                        item["abnormal_info"] or "[green]正常[/green]",
                    )

                console.print("\n")
                console.print(table)
            else:
                console.print(f"\n[red]✗ 请求失败![/red]")
                console.print(f"状态码: {response.status_code}")
                console.print(f"响应: {response.text}")

    except httpx.ConnectError:
        console.print("\n[red]✗ 连接失败![/red]")
        console.print("请确保FastAPI服务正在运行 (运行: uvicorn app.main:app --reload)")
    except Exception as e:
        console.print(f"\n[red]✗ 错误: {str(e)}[/red]")


async def test_medical_report():
    """测试体检报告核验功能。"""
    test_request = {
        "base_info": {"姓名": "吴全英", "体检日期": "2024-06-15"},
        "quality_inspection_type": "MEDICAL_REPORT",
        "urls": ["https://ys-app.obs.cn-east-3.myhuaweicloud.com/aaa/1111/cccc/check_wu_quan_ying.pdf"],
        "enable_thinking": False,
    }

    api_url = "http://localhost:8000/api/v1/hr_onboarding_verification/qc"

    console.print("\n" + "=" * 60)
    console.print(Panel.fit("[bold cyan]体检报告核验测试[/bold cyan]", border_style="cyan"))

    console.print("\n[yellow]发送请求...[/yellow]")
    console.print(f"类型: {test_request['quality_inspection_type']}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                json=test_request,
            )

            if response.status_code == 200:
                result = response.json()

                console.print(f"\n[green]✓ 请求成功![/green]")
                console.print(f"整体通过: {'[green]是[/green]' if result['is_all_passed'] else '[red]否[/red]'}")

                table = Table(title="核验结果详情", show_header=True, header_style="bold magenta")
                table.add_column("质检项", style="cyan")
                table.add_column("提取内容", style="yellow")
                table.add_column("异常信息", style="red")

                for item in result["results"]:
                    table.add_row(
                        item["rule_item_name"],
                        item["extracted_content"],
                        item["abnormal_info"] or "[green]正常[/green]",
                    )

                console.print("\n")
                console.print(table)
            else:
                console.print(f"\n[red]✗ 请求失败![/red]")
                console.print(f"状态码: {response.status_code}")
                console.print(f"响应: {response.text}")

    except Exception as e:
        console.print(f"\n[red]✗ 错误: {str(e)}[/red]")


if __name__ == "__main__":
    console.print("[bold]开始测试HR入职文件质量核验功能[/bold]\n")
    asyncio.run(test_hr_verification())
    asyncio.run(test_medical_report())
    console.print("\n[bold green]测试完成![/bold green]")

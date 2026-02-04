#!/usr/bin/env python3
"""
数据库迁移脚本：添加 last_used_at 字段到 API Key 表

使用方法：
    python migrate_add_last_used_at.py

说明：
    此脚本会自动检测表名（bs_bearer_tokens 或 bs_api_keys）
    并添加 last_used_at 字段（如果不存在的话）
"""

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings


def main():
    print("=== 数据库迁移：添加 last_used_at 字段 ===\n")

    # 创建数据库连接
    connection_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    engine = create_engine(connection_url)

    with engine.connect() as conn:
        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        target_table = None
        if "bs_api_keys" in tables:
            target_table = "bs_api_keys"
        elif "bs_bearer_tokens" in tables:
            target_table = "bs_bearer_tokens"
        else:
            print("❌ 错误：找不到 API Key 表（bs_api_keys 或 bs_bearer_tokens）")
            print("   请确保数据库已初始化")
            return

        print(f"✓ 找到表: {target_table}")

        # 检查 last_used_at 字段是否已存在
        columns = [col["name"] for col in inspector.get_columns(target_table)]

        if "last_used_at" in columns:
            print(f"✓ 字段 last_used_at 已经存在于表 {target_table}")
            print("  无需迁移")
            return

        # 添加字段
        print(f"\n正在添加 last_used_at 字段到表 {target_table}...")

        sql = text(f"ALTER TABLE {target_table} ADD COLUMN last_used_at TIMESTAMP NULL")
        conn.execute(sql)
        conn.commit()

        print("✓ 字段添加成功！")

        # 验证
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns(target_table)]

        if "last_used_at" in columns:
            print("\n✓ 验证成功：last_used_at 字段已添加")
            print(f"\n当前 {target_table} 表的所有字段:")
            for col in inspector.get_columns(target_table):
                print(f"  - {col['name']}: {col['type']} {'NULL' if col['nullable'] else 'NOT NULL'}")
        else:
            print("\n❌ 验证失败：字段未成功添加")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()

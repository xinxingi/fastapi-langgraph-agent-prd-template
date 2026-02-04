#!/usr/bin/env python3
"""
数据库迁移脚本：为 API Key 添加名称唯一性约束

使用方法：
    python migrate_add_unique_name_constraint.py

说明：
    此脚本会为 API Key 表添加复合唯一约束（user_id + name）
    确保同一用户下的 API Key 名称不会重复
"""

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings


def main():
    print("=== 数据库迁移：添加 API Key 名称唯一性约束 ===\n")

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

        # 检查约束是否已存在
        constraints = inspector.get_unique_constraints(target_table)
        constraint_exists = any(c["name"] == "uq_user_api_key_name" for c in constraints)

        if constraint_exists:
            print(f"✓ 唯一约束 uq_user_api_key_name 已经存在于表 {target_table}")
            print("  无需迁移")
            return

        # 检查是否有重复的名称
        print(f"\n检查是否存在重复的 API Key 名称...")

        check_sql = text(f"""
            SELECT user_id, name, COUNT(*) as count
            FROM {target_table}
            WHERE name IS NOT NULL
            GROUP BY user_id, name
            HAVING COUNT(*) > 1
        """)

        duplicates = conn.execute(check_sql).fetchall()

        if duplicates:
            print(f"\n⚠️  警告：发现 {len(duplicates)} 组重复的名称：")
            for dup in duplicates:
                print(f"   用户 {dup.user_id} 的名称 '{dup.name}' 重复了 {dup.count} 次")

            print("\n为了添加唯一约束，需要先修复这些重复名称。")
            print("正在自动修复（为重复项添加数字后缀）...\n")

            # 修复重复名称
            for dup in duplicates:
                user_id = dup.user_id
                name = dup.name

                # 获取所有重复的记录
                get_dups_sql = text(f"""
                    SELECT id, name
                    FROM {target_table}
                    WHERE user_id = :user_id AND name = :name
                    ORDER BY created_at
                """)

                records = conn.execute(get_dups_sql, {"user_id": user_id, "name": name}).fetchall()

                # 保留第一个，为其他的添加后缀
                for i, record in enumerate(records[1:], start=2):
                    new_name = f"{name} ({i})"
                    update_sql = text(f"""
                        UPDATE {target_table}
                        SET name = :new_name
                        WHERE id = :id
                    """)
                    conn.execute(update_sql, {"new_name": new_name, "id": record.id})
                    print(f"✓ 已将 API Key ID {record.id} 的名称从 '{name}' 改为 '{new_name}'")

            conn.commit()
            print("\n✓ 重复名称修复完成")
        else:
            print("✓ 没有发现重复的名称")

        # 添加唯一约束
        print(f"\n正在添加唯一约束到表 {target_table}...")

        sql = text(f"""
            ALTER TABLE {target_table}
            ADD CONSTRAINT uq_user_api_key_name UNIQUE (user_id, name)
        """)
        conn.execute(sql)
        conn.commit()

        print("✓ 唯一约束添加成功！")

        # 验证
        inspector = inspect(engine)
        constraints = inspector.get_unique_constraints(target_table)

        if any(c["name"] == "uq_user_api_key_name" for c in constraints):
            print("\n✓ 验证成功：唯一约束已添加")
            print(f"\n{target_table} 表的所有唯一约束:")
            for constraint in constraints:
                columns = ", ".join(constraint["column_names"])
                print(f"  - {constraint['name']}: ({columns})")
        else:
            print("\n❌ 验证失败：约束未成功添加")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback

        traceback.print_exc()

import argparse
import asyncio

from stockbot.config import get_settings


def check_config() -> None:
    settings = get_settings()
    print(
        "Configuration valid: "
        f"environment={settings.environment}, max_active_users={settings.max_active_users}, "
        f"telegram_admins={len(settings.telegram_admin_ids)}, bale_admins={len(settings.bale_admin_ids)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="stockbot")
    parser.add_argument("command", choices=("check-config", "tse-once"))
    args = parser.parse_args()
    if args.command == "check-config":
        check_config()
    else:
        from stockbot.services.tse_ingestion import run_once
        import asyncpg

        async def run() -> None:
            settings = get_settings()
            pool = await asyncpg.create_pool(str(settings.database_url), min_size=1, max_size=2)
            try:
                count = await run_once(pool, settings)
                print(f"TSE ingestion completed: {count} snapshots")
            finally:
                await pool.close()

        asyncio.run(run())

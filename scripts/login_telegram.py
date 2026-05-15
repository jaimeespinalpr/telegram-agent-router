import asyncio
import sys
from pathlib import Path

from telethon import TelegramClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.settings import get_settings


async def main() -> None:
    settings = get_settings()
    if settings.telegram_api_id is None or not settings.telegram_api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first.")

    session_path = Path(settings.telegram_session_path)
    session_path.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        settings.telegram_session_path,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.start()
    me = await client.get_me()
    print(f"Logged in as @{me.username or me.id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

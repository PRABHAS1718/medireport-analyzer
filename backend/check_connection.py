"""Diagnostic script to verify MongoDB connectivity.

Safely tests the active connection string from backend/.env without
exposing passwords or credentials in console logs.
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def main():
    uri = settings.MONGODB_URI
    # Safely extract host without credentials
    if "@" in uri:
        target_host = uri.split("@")[-1].split("?")[0]
    else:
        target_host = uri.split("://")[-1]

    print(f"[*] Testing connection to: {target_host}")
    print(f"[*] Target database: {settings.MONGODB_DB_NAME}")

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    try:
        response = await client.admin.command("ping")
        print("[+] SUCCESS: Connection to MongoDB successfully established!")
        print(f"[+] Server Ping Response: {response}")
    except Exception as exc:
        print("[-] FAILED: Could not connect to MongoDB.")
        print(f"[-] Reason: {type(exc).__name__} - {exc}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())

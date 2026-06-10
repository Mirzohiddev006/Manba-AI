#!/usr/bin/env python3
"""Birinchi superadmin yaratish: python scripts/create_admin.py email parol."""

import asyncio
import sys

sys.path.insert(0, "apps/api")
sys.path.insert(0, "packages/citation-core")


async def main() -> None:
    import pyotp
    from app.auth import pwd_context
    from app.db import SessionLocal
    from app.models import AdminUser

    email, password = sys.argv[1], sys.argv[2]
    secret = pyotp.random_base32()
    async with SessionLocal() as db:
        db.add(AdminUser(
            email=email, password_hash=pwd_context.hash(password),
            role="superadmin", totp_secret=secret,
        ))
        await db.commit()
    print(f"✅ Superadmin yaratildi: {email}")
    print(f"TOTP sozlash (authenticator ilovaga kiriting): {secret}")
    print(f"yoki URI: otpauth://totp/ManbaAI:{email}?secret={secret}&issuer=ManbaAI")


if __name__ == "__main__":
    asyncio.run(main())

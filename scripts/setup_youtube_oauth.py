#!/usr/bin/env python3
"""
One-Time YouTube OAuth Setup Script
Generates token.json with required scopes:
- youtube.upload
- youtube.readonly
"""

import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import settings

def main():
    print("=" * 60)
    print(" YouTube Data API v3 OAuth Setup Helper")
    print("=" * 60)

    client_secret_path = Path(settings.YOUTUBE_CLIENT_SECRET_FILE)
    token_path = Path(settings.YOUTUBE_TOKEN_FILE)

    if not client_secret_path.exists():
        print(f"\n[ERROR] Client secrets file not found: '{client_secret_path}'")
        print("Please download client_secret.json from your Google Cloud Console and place it in the project root.")
        sys.exit(1)

    print(f"\nUsing client secret: {client_secret_path}")
    print(f"Requested Scopes: {settings.YOUTUBE_SCOPES}")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret_path),
        scopes=settings.YOUTUBE_SCOPES
    )

    creds = flow.run_local_server(port=8080)

    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n[SUCCESS] OAuth token generated and saved to '{token_path}'!")
    print("\nFor GitHub Actions Deployment:")
    print("1. Open 'token.json' and copy its entire JSON content.")
    print("2. In GitHub Repo -> Settings -> Secrets and variables -> Actions, create a Secret named:")
    print("   YOUTUBE_TOKEN_DATA")
    print("3. Paste the JSON content as the Secret value.")
    print("=" * 60)

if __name__ == "__main__":
    main()

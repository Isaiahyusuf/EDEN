Eden Token Assistant is a Telegram-based launchpad assistant designed to help creators prepare, organize, and launch meme coin projects on pump.fun in a secure, transparent, and user-controlled way.

The bot simplifies the pre-launch process, automates Telegram community creation, and provides a guided pump.fun launch flow without ever requesting private keys, seed phrases, or wallet access.

⸻

OVERVIEW

Eden Token Assistant acts as a launch assistant rather than a token issuer. It helps users structure their project, create official communities, generate launch content, and safely complete token creation on pump.fun through manual wallet signing.

All blockchain interactions are performed directly by the user.

⸻

FEATURES

Project Setup
The bot collects essential project information including token name, symbol, description, logo, and social links. All inputs are validated and formatted to align with pump.fun standards.

Pump.fun Launch Assistant
Eden Token Assistant generates pump.fun-ready descriptions, metadata previews, and copy-paste launch content. It provides a guided “Launch on pump.fun” flow where the user completes token creation manually and signs transactions using their own wallet.

Automatic Community Creation
The bot automatically creates an official Telegram group and channel for the project. It configures welcome messages, pinned rules, project descriptions, and admin permissions. Optional anti-spam and captcha protections can be enabled.

Group and Channel Manager with Verification
Eden Token Assistant includes a built-in manager that verifies and authenticates project ownership at the Telegram level. The project creator is linked to the group and channel using their Telegram user ID. Only verified admins can manage settings, post official announcements, or trigger bot actions.

The manager prevents admin takeovers, impersonation, and unauthorized changes. Communities can be marked as “Verified by Eden Token Assistant” through pinned system messages.

Announcement Authentication
Only verified admins can post or pin official announcements. The bot can automatically reject or remove messages from unverified sources to prevent scams and fake admin activity.

User Protection
Optional join verification, captcha checks, and scam keyword filtering help reduce bot raids, phishing links, and malicious actors in project communities.

Launch Content Generator
The bot generates shill messages, announcement templates, meme captions, pinned posts, and basic roadmap or rules text to help creators launch and manage their community effectively.

Post-Launch Tools
Optional tools include quick access links to pump.fun and DexScreener, trending submission resources, and read-only tracking references for holders and volume.

⸻

SECURITY AND COMPLIANCE

Eden Token Assistant never requests private keys or seed phrases.
It does not connect to wallets or sign transactions.
It does not perform token creation on behalf of users.
All on-chain actions are completed manually by the user on pump.fun.

The bot performs only Telegram-level verification and community management. It does not provide financial advice or guarantee any outcomes.

⸻

HOW IT WORKS

The user starts Eden Token Assistant on Telegram.
They provide project details through guided prompts.
The bot validates inputs and generates launch assets.
An official Telegram group and channel are created automatically.
The creator completes admin verification.
The community is locked to verified admins.
The user clicks “Launch on pump.fun”.
The user completes token creation and wallet signing manually on pump.fun.

⸻

TECH STACK

Python
Aiogram for Telegram Bot API
Telethon for advanced Telegram actions
FastAPI for backend services
PostgreSQL for persistent storage
Redis for sessions, queues, and rate-limiting

⸻

INSTALLATION

Clone the repository and install dependencies.

git clone https://github.com/yourusername/eden-token-assistant.git
cd eden-token-assistant
pip install -r requirements.txt

Set environment variables.

BOT_TOKEN=your_telegram_bot_token
API_ID=telegram_api_id
API_HASH=telegram_api_hash
DATABASE_URL=postgresql://user:password@host/database

⸻

RUNNING THE BOT

python main.py

⸻

USE CASES

Meme coin creators
First-time pump.fun launchers
Community managers
Web3 agencies
Crypto influencers and launch teams

⸻

MONETIZATION IDEAS

Paid launch tiers
Custom branding for projects
Premium content generation
Post-launch analytics integrations
Hype and trending integrations

⸻

DISCLAIMER

Eden Token Assistant does not create tokens, does not guarantee profits, and does not provide financial or investment advice.

All blockchain actions are executed directly by users on pump.fun. Use responsibly.

⸻

LICENSE

MIT License

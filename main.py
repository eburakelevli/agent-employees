from config import DISCORD_BOT_TOKEN
from bot import AgentBot


def main():
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not set in .env")
        return

    bot = AgentBot()
    print("Starting Agent Employees bot...")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()

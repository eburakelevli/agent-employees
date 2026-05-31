import asyncio
import sys

from config import DISCORD_BOT_TOKEN, SLACK_BOT_TOKEN, SLACK_APP_TOKEN
from tools.memory import _using_pinecone


def _print_memory_status():
    if _using_pinecone():
        from config import PINECONE_INDEX_NAME, PINECONE_NAMESPACE
        print(f"Memory backend: Pinecone (index={PINECONE_INDEX_NAME}, namespace={PINECONE_NAMESPACE})")
    else:
        print("Memory backend: local (agent_memory.json)")


def main():
    use_slack = "--slack" in sys.argv or any(
        a.lower() == "slack" for a in sys.argv[1:]
    )

    if use_slack:
        if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
            print("Error: SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in .env")
            return
        _print_memory_status()
        from slack_bot import main as slack_main
        asyncio.run(slack_main())
    else:
        if not DISCORD_BOT_TOKEN:
            print("Error: DISCORD_BOT_TOKEN not set in .env")
            return
        _print_memory_status()
        from bot import AgentBot
        bot = AgentBot()
        print("Starting Agent Employees bot (Discord)...")
        bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()

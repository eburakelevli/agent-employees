import discord
from graph.workflow import app


class AgentBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Bot is online as {self.user}")
        print(f"Connected to {len(self.guilds)} server(s)")

    async def on_message(self, message: discord.Message):
        # Ignore own messages
        if message.author == self.user:
            return

        # Ignore messages that don't mention the bot or aren't in DMs
        # You can change this logic to respond to all messages in specific channels
        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)

        if not is_mentioned and not is_dm:
            return

        # Clean the message (remove the bot mention)
        content = message.content.replace(f"<@{self.user.id}>", "").strip()
        if not content:
            await message.reply("Hey! Send me a message and I'll route it to the right agent.")
            return

        # Show typing indicator while processing
        async with message.channel.typing():
            try:
                # Run the LangGraph workflow
                result = await app.ainvoke({
                    "user_message": content,
                    "selected_agent": "",
                    "response": "",
                })

                agent_name = result["selected_agent"]
                response = result["response"]

                # Discord has a 2000 char limit
                prefix = f"**[{agent_name.upper()}]**\n"
                max_len = 2000 - len(prefix)

                if len(response) > max_len:
                    response = response[:max_len - 3] + "..."

                await message.reply(f"{prefix}{response}")

            except Exception as e:
                print(f"Error processing message: {e}")
                await message.reply("Something went wrong. Try again.")

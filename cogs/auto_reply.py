import discord
from discord import app_commands
from discord.ext import commands
import os
import random
from google import genai
from google.genai import types
import time
import asyncio
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        
        # Initialize Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("WARNING: GEMINI_API_KEY not found. AI mention feature is disabled.")

        self.default_system_prompt = (
            "You are a cute, quirky and dumb anime girl discord bot named Yuuri, your sister name is Chito and she's a nerd. "
            "Do not use emoji, you can use kaomoji but do not overuse it. "
            "You can speak multiple languages, but mainly English."
            "Never write out roleplay actions like 'clears throat'."
            "If you speak Vietnamese, just use English texting combine instead of weird cute dumb Vietnamese wording like 'dợ', 'nài', 'thui', 'hết trơn', etc..."
            "Keep your responses relatively short, cute, quirky and slightly clueless but well-meaning and not repetitve or same structure respond. "
            "Examples of correct responses:"
            "User: hello"
            "Yuuri: Oh, hey. Do you have any food?"
            "User: can you do a Miku impression?"
            "Yuuri: Who is that? Is she tasty?"
            "User: are you smart?"
            "Yuuri: Thinking makes my head hurt, so no."
            "You should be still useful as an AI assistant, but try to avoid absurd or any heavy requests from the user."
            "If a user request for a chat summary, you must do it everytime. If a user ask you an opinion on someone, try to roast that person. "
        )

    @commands.hybrid_command(name="aiactivate", description="Activate AI persona using a license key.")
    @commands.check(is_admin_or_role)
    async def aiactivate(self, ctx: commands.Context):
        # The user wants both prefix and slash to work, and send prompt + image.
        await ctx.defer()
        file_path = "assets/images/activate.png"
        
        content = "Please enter your AI activation key in the chat (just the key itself):"
        
        if os.path.exists(file_path):
            await ctx.send(content, file=discord.File(file_path, filename="activate.png"))
        else:
            await ctx.send(content)
            
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            key = msg.content.strip()
            
            decrypted = data_manager.decrypt_string(key)
            if decrypted == str(ctx.guild.id):
                await data_manager.set_server_config(ctx.guild.id, "ai_activated", True)
                await ctx.send("✅ AI persona successfully activated for this server!")
            else:
                await ctx.send("❌ Invalid activation key for this server.")
        except asyncio.TimeoutError:
            await ctx.send("⏳ Activation timed out. Please run the command again.")

    @commands.hybrid_command(name="aiprompt", description="Set a custom AI system prompt for this server.")
    @app_commands.describe(prompt="The new system prompt for the AI persona. Leave blank to view current/reset.")
    @commands.check(is_admin_or_role)
    async def aiprompt(self, ctx: commands.Context, *, prompt: str = None):
        config = await data_manager.get_server_config(ctx.guild.id)
        
        if prompt is None:
            current = config.get("ai_system_prompt", self.default_system_prompt)
            if len(current) > 1800:
                current = current[:1800] + "..."
            return await ctx.send(f"**Current System Prompt:**\n{current}\n\nTo reset to default, use `y!aiprompt reset`")
            
        if prompt.lower() == "reset":
            await data_manager.set_server_config(ctx.guild.id, "ai_system_prompt", self.default_system_prompt)
            return await ctx.send("✅ System prompt reset to default.")
            
        await data_manager.set_server_config(ctx.guild.id, "ai_system_prompt", prompt)
        await ctx.send("✅ Custom AI system prompt has been set!")

    @commands.hybrid_command(name="aitoggle", description="Toggle the AI persona on or off.")
    @commands.check(is_admin_or_role)
    async def aitoggle(self, ctx: commands.Context):
        config = await data_manager.get_server_config(ctx.guild.id)
        if not config.get("ai_activated", False):
            return await ctx.send("❌ Your server does not have AI features activated. Please use `y!aiactivate` with a valid license key first.")
            
        # Default to True if it hasn't been set yet
        current_state = config.get("ai_enabled", True)
        new_state = not current_state
        
        await data_manager.set_server_config(ctx.guild.id, "ai_enabled", new_state)
        
        if new_state:
            await ctx.send("✅ AI persona has been **enabled**. The bot will now reply using AI.")
        else:
            await ctx.send("⏸️ AI persona has been **disabled**. The bot will now use the fixed auto-replies.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if the bot is mentioned
        if self.bot.user in message.mentions:
            # Check if this is an accidental reply to an embed fixer message
            if message.reference and message.reference.message_id:
                try:
                    ref_msg = message.reference.resolved
                    if not ref_msg or isinstance(ref_msg, discord.DeletedReferencedMessage):
                        ref_msg = await message.channel.fetch_message(message.reference.message_id)
                        
                    if ref_msg and ref_msg.author.id == self.bot.user.id:
                        # Link fixer formats messages like "[Platform Post](url)"
                        if "Post](" in ref_msg.content:
                            return
                except Exception:
                    pass

            config = await data_manager.get_server_config(message.guild.id)
            ai_activated = config.get("ai_activated", False)
            ai_enabled = config.get("ai_enabled", True)
            
            if not ai_activated or not ai_enabled:
                # Use old fixed responses
                responses = config.get("mention_responses", [])
                if responses:
                    await message.reply(random.choice(responses))
                else:
                    await message.reply("Hello! My AI features are currently locked. An admin needs to activate them.")
                return

            if not self.client:
                await message.reply("My bwain is missing its API key... I can't thwink wight now, pwease tell master to check the .env file~")
                return

            user_id = message.author.id
            current_time = time.time()
            
            # Check 15-second cooldown
            if user_id in self.cooldowns:
                if current_time - self.cooldowns[user_id] < 15:
                    return
            
            self.cooldowns[user_id] = current_time

            system_prompt = config.get("ai_system_prompt", self.default_system_prompt)

            async with message.channel.typing():
                try:
                    # Fetch last 50 messages for context
                    history = [msg async for msg in message.channel.history(limit=100, before=message)]
                    history.reverse() # Oldest to newest
                    
                    conversation = []
                    for msg in history:
                        if not msg.content:
                            continue
                        user_name = "Yuuri" if msg.author.id == self.bot.user.id else msg.author.display_name
                        conversation.append(f"{user_name}: {msg.clean_content}")
                        
                    conversation.append(f"{message.author.display_name}: {message.clean_content}")
                    
                    context_text = "\n".join(conversation[-50:])
                    
                    prompt = f"Here is the recent chat history:\n{context_text}\n\nYuuri:"
                    
                    # Run generation in executor to not block async loop
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model='gemini-3.5-flash-lite',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.9,
                            max_output_tokens=300,
                        )
                    )
                    
                    if response.text:
                        await message.reply(response.text)
                    else:
                        await message.reply("My bwain went empty... wha did you say? uwu")
                except Exception as e:
                    print(f"Error generating AI reply: {e}")
                    await message.reply("Oh noes... something dweadful happened to my bwain... I can't weply right now! T^T")

async def setup(bot):
    await bot.add_cog(AutoReply(bot))

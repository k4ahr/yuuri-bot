import discord
from discord import app_commands
from discord.ext import commands
import os
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
import asyncio
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

load_dotenv()

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        # Track message IDs that were auto-reply responses (both AI and fixed)
        # so we only continue the conversation when a user replies to an auto-reply message,
        # not to trigger/command/link-fixer messages.
        self.auto_reply_message_ids: set[int] = set()
        self.ai_message_ids = self.auto_reply_message_ids  # alias for backward compatibility
        self._MSG_ID_LIMIT = 5000  # cap to prevent unbounded memory growth
        self._AI_MSG_ID_LIMIT = self._MSG_ID_LIMIT
        
        # Initialize Gemini API
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
        print(f"DEBUG: GEMINI_API_KEY loaded, length={len(api_key)}, prefix={api_key[:4] if api_key else 'NONE'}")
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

        # Check if the bot is explicitly @mentioned in the message text
        # (not just from Discord's reply ping, which also adds to message.mentions)
        bot_mention_strings = [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]
        is_mentioned = any(m in message.content for m in bot_mention_strings)
        is_reply_to_auto_reply = False

        # Check if this is a reply to one of the bot's auto-reply messages
        if message.reference and message.reference.message_id:
            ref_id = message.reference.message_id
            if ref_id in self.auto_reply_message_ids:
                is_reply_to_auto_reply = True
            else:
                # Check resolved reference (e.g. after bot restart) if available
                ref_msg = message.reference.resolved
                if ref_msg and isinstance(ref_msg, discord.Message) and ref_msg.author.id == self.bot.user.id:
                    config = await data_manager.get_server_config(message.guild.id)
                    mention_responses = config.get("mention_responses", [])
                    locked_msg = "Hello! My AI features are currently locked. An admin needs to activate them."
                    if ref_msg.content in mention_responses or ref_msg.content == locked_msg:
                        is_reply_to_auto_reply = True
                        self._track_auto_reply_message(ref_id)

        if not is_mentioned and not is_reply_to_auto_reply:
            return

        config = await data_manager.get_server_config(message.guild.id)
        ai_activated = config.get("ai_activated", False)
        ai_enabled = config.get("ai_enabled", True)

        if not ai_activated or not ai_enabled:
            # Use old fixed responses
            responses = config.get("mention_responses", [])
            if responses:
                sent = await message.reply(random.choice(responses))
            else:
                sent = await message.reply("Hello! My AI features are currently locked. An admin needs to activate them.")
            self._track_auto_reply_message(sent.id)
            return

        if not self.client:
            sent = await message.reply("My bwain is missing its API key... I can't thwink wight now, pwease tell master to check the .env file~")
            self._track_auto_reply_message(sent.id)
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
                
                # Model fallback chain for resilience against 503 demand spikes
                primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
                fallback_models = [primary_model, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
                # Deduplicate while preserving order
                seen = set()
                models_to_try = []
                for m in fallback_models:
                    if m not in seen:
                        seen.add(m)
                        models_to_try.append(m)

                gen_config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.9,
                    max_output_tokens=300,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )

                response = None
                last_error = None
                for model_name in models_to_try:
                    try:
                        print(f"Trying model={model_name}...")
                        response = await asyncio.to_thread(
                            self.client.models.generate_content,
                            model=model_name,
                            contents=prompt,
                            config=gen_config,
                        )
                        break  # Success, stop trying
                    except Exception as model_err:
                        last_error = model_err
                        err_str = str(model_err)
                        if "503" in err_str or "UNAVAILABLE" in err_str or "504" in err_str or "DEADLINE_EXCEEDED" in err_str:
                            print(f"Model {model_name} unavailable, trying next fallback...")
                            continue
                        else:
                            raise  # Non-transient error, don't retry

                if response and response.text:
                    sent = await message.reply(response.text)
                    self._track_auto_reply_message(sent.id)
                elif response:
                    sent = await message.reply("My bwain went empty... wha did you say? uwu")
                    self._track_auto_reply_message(sent.id)
                else:
                    # All models failed
                    print(f"All models exhausted. Last error: {last_error}")
                    sent = await message.reply("All my bwain cells are overloaded right now... try again in a bit! (´;ω;`)")
                    self._track_auto_reply_message(sent.id)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error generating AI reply: {e}")
                sent = await message.reply("Oh noes... something dweadful happened to my bwain... I can't weply right now! T^T")
                self._track_auto_reply_message(sent.id)

    def _track_auto_reply_message(self, message_id: int):
        """Store an auto-reply message ID, evicting oldest entries if over the limit."""
        self.auto_reply_message_ids.add(message_id)
        # Evict oldest entries when the set grows too large
        if len(self.auto_reply_message_ids) > self._MSG_ID_LIMIT:
            # Message IDs are snowflakes (monotonically increasing), so
            # removing the smallest values drops the oldest messages.
            sorted_ids = sorted(self.auto_reply_message_ids)
            for old_id in sorted_ids[:len(sorted_ids) - self._MSG_ID_LIMIT]:
                self.auto_reply_message_ids.discard(old_id)

    def _track_ai_message(self, message_id: int):
        """Backward-compatible alias for _track_auto_reply_message."""
        self._track_auto_reply_message(message_id)

async def setup(bot):
    await bot.add_cog(AutoReply(bot))

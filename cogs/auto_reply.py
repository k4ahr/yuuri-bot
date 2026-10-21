import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import asyncio
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

load_dotenv()

# ---------------------------------------------------------------------------
# Valid Gemini model names. Override primary via GEMINI_MODEL env var.
# ---------------------------------------------------------------------------
_DEFAULT_MODEL = "gemini-2.0-flash"
_FALLBACK_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]


class AutoReply(commands.Cog):
    """Handles @mention / reply-chain AI responses powered by Gemini."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns: dict[int, float] = {}

        # Tracks message IDs sent by the bot as auto-replies so reply-chain
        # conversations are forwarded to AI instead of being ignored.
        self._auto_reply_ids: set[int] = set()
        self._AUTO_REPLY_ID_LIMIT = 5_000

        # Build ordered fallback model list, honouring any env override.
        primary = (os.getenv("GEMINI_MODEL") or _DEFAULT_MODEL).strip()
        seen: set[str] = set()
        self._models: list[str] = []
        for m in [primary, *_FALLBACK_MODELS]:
            if m not in seen:
                seen.add(m)
                self._models.append(m)

        # Initialise Gemini client.
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
        if api_key:
            self.client: genai.Client | None = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("[AutoReply] WARNING: GEMINI_API_KEY not set — AI replies disabled.")

        self.default_system_prompt = (
            "You are a cute, quirky and dumb anime girl discord bot named Yuuri. "
            "Your sister is Chito, who is a nerd. "
            "Do not use emoji; you may use kaomoji but sparingly. "
            "You can speak multiple languages but mainly English. "
            "Never write out roleplay actions like *clears throat*. "
            "If you speak Vietnamese, use normal English-style casual writing instead of "
            "baby-talk variants like 'dợ', 'nài', 'thui', 'hết trơn', etc. "
            "Keep responses short, cute, quirky, and slightly clueless but well-meaning. "
            "Vary your response structure — don't repeat yourself. "
            "You are still a useful AI assistant but avoid heavy or complex requests. "
            "If asked for a chat summary, always provide one. "
            "If asked your opinion on someone, lightly roast them. "
            "Examples:\n"
            "User: hello\nYuuri: Oh, hey. Do you have any food?\n"
            "User: can you do a Miku impression?\nYuuri: Who is that? Is she tasty?\n"
            "User: are you smart?\nYuuri: Thinking makes my head hurt, so no."
        )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    @commands.hybrid_command(name="aiactivate", description="Activate AI persona using a license key.")
    @commands.check(is_admin_or_role)
    async def aiactivate(self, ctx: commands.Context):
        await ctx.defer()
        file_path = "assets/images/activate.png"
        prompt_text = "Please enter your AI activation key in the chat (just the key itself):"

        if os.path.exists(file_path):
            await ctx.send(prompt_text, file=discord.File(file_path, filename="activate.png"))
        else:
            await ctx.send(prompt_text)

        def check(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60.0)
            key = msg.content.strip()
            decrypted = data_manager.decrypt_string(key)
            if decrypted == str(ctx.guild.id):
                await data_manager.set_server_config(ctx.guild.id, "ai_activated", True)
                await ctx.send("✅ AI persona successfully activated for this server!")
            else:
                await ctx.send("❌ Invalid activation key for this server.")
        except asyncio.TimeoutError:
            await ctx.send("⏳ Activation timed out. Please run the command again.")

    @commands.hybrid_command(name="aiprompt", description="View or set a custom AI system prompt for this server.")
    @app_commands.describe(prompt="New system prompt. Leave blank to view current. Use 'reset' to restore default.")
    @commands.check(is_admin_or_role)
    async def aiprompt(self, ctx: commands.Context, *, prompt: str = None):
        config = await data_manager.get_server_config(ctx.guild.id)

        if prompt is None:
            current = config.get("ai_system_prompt", self.default_system_prompt)
            display = current[:1800] + "..." if len(current) > 1800 else current
            return await ctx.send(
                f"**Current System Prompt:**\n{display}\n\n"
                "To reset to default, use `y!aiprompt reset`"
            )

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
            return await ctx.send(
                "❌ AI features are not activated for this server. "
                "Use `y!aiactivate` with a valid license key first."
            )

        new_state = not config.get("ai_enabled", True)
        await data_manager.set_server_config(ctx.guild.id, "ai_enabled", new_state)

        if new_state:
            await ctx.send("✅ AI persona **enabled** — the bot will now reply using AI.")
        else:
            await ctx.send("⏸️ AI persona **disabled** — the bot will use fixed auto-replies.")

    # ------------------------------------------------------------------
    # Listener
    # ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        is_mentioned = any(
            tag in message.content
            for tag in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>")
        )
        is_reply_to_bot = await self._is_reply_to_auto_reply(message)

        if not is_mentioned and not is_reply_to_bot:
            return

        config = await data_manager.get_server_config(message.guild.id)

        # --- AI not activated / disabled: use fixed responses ---
        if not config.get("ai_activated", False) or not config.get("ai_enabled", True):
            responses = config.get("mention_responses", [])
            text = (
                random.choice(responses)
                if responses
                else "Hello! My AI features are currently locked. An admin needs to activate them."
            )
            sent = await message.reply(text)
            self._track(sent.id)
            return

        # --- AI client missing ---
        if not self.client:
            sent = await message.reply(
                "My brain is missing its API key... I can't think right now, "
                "please tell master to check the .env file~"
            )
            self._track(sent.id)
            return

        # --- Cooldown (15 s per user) ---
        now = time.monotonic()
        if now - self.cooldowns.get(message.author.id, 0) < 15:
            return
        self.cooldowns[message.author.id] = now

        await self._generate_and_reply(message, config)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _is_reply_to_auto_reply(self, message: discord.Message) -> bool:
        """Return True if the message is a reply to one of the bot's tracked auto-reply messages."""
        if not (message.reference and message.reference.message_id):
            return False

        ref_id = message.reference.message_id
        if ref_id in self._auto_reply_ids:
            return True

        # Fallback: check resolved reference for messages not in our local set
        # (e.g. after a bot restart).
        ref_msg = message.reference.resolved
        if ref_msg and isinstance(ref_msg, discord.Message) and ref_msg.author.id == self.bot.user.id:
            config = await data_manager.get_server_config(message.guild.id)
            known_responses = config.get("mention_responses", [])
            locked_msg = "Hello! My AI features are currently locked. An admin needs to activate them."
            if ref_msg.content in known_responses or ref_msg.content == locked_msg:
                self._track(ref_id)
                return True

        return False

    async def _generate_and_reply(self, message: discord.Message, config: dict):
        """Call Gemini with chat history and send the reply."""
        system_prompt = config.get("ai_system_prompt", self.default_system_prompt)

        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.9,
            max_output_tokens=300,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        async with message.channel.typing():
            try:
                prompt = await self._build_prompt(message)
                response = await self._call_gemini(prompt, gen_config)

                reply_text = (
                    response.text.strip()
                    if response and response.text
                    else "My brain went empty... what did you say?"
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[AutoReply] Error generating AI reply: {e}")
                reply_text = "Oh no... something dreadful happened to my brain... I can't reply right now! T^T"

        sent = await message.reply(reply_text)
        self._track(sent.id)

    async def _build_prompt(self, message: discord.Message) -> str:
        """Construct the conversation-history prompt string."""
        history = [m async for m in message.channel.history(limit=100, before=message)]
        history.reverse()

        lines = []
        for msg in history:
            if not msg.content:
                continue
            name = "Yuuri" if msg.author.id == self.bot.user.id else msg.author.display_name
            lines.append(f"{name}: {msg.clean_content}")

        lines.append(f"{message.author.display_name}: {message.clean_content}")

        context = "\n".join(lines[-50:])
        return f"Here is the recent chat history:\n{context}\n\nYuuri:"

    async def _call_gemini(
        self,
        prompt: str,
        gen_config: types.GenerateContentConfig,
    ):
        """Try each model in the fallback list, returning the first successful response."""
        last_error: Exception | None = None

        for model_name in self._models:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model_name,
                    contents=prompt,
                    config=gen_config,
                )
                return response
            except Exception as err:
                last_error = err
                err_str = str(err)
                transient_codes = ("503", "UNAVAILABLE", "504", "DEADLINE_EXCEEDED")
                if any(code in err_str for code in transient_codes):
                    print(f"[AutoReply] Model '{model_name}' unavailable, trying next fallback...")
                    continue
                raise  # Non-transient error — propagate immediately

        print(f"[AutoReply] All models exhausted. Last error: {last_error}")
        return None

    def _track(self, message_id: int):
        """Record a bot auto-reply message ID, evicting oldest when at capacity."""
        self._auto_reply_ids.add(message_id)
        if len(self._auto_reply_ids) > self._AUTO_REPLY_ID_LIMIT:
            for old_id in sorted(self._auto_reply_ids)[: len(self._auto_reply_ids) - self._AUTO_REPLY_ID_LIMIT]:
                self._auto_reply_ids.discard(old_id)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReply(bot))

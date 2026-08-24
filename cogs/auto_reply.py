import discord
from discord.ext import commands
import os
from google import genai
from google.genai import types
import time
import asyncio

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

        self.system_prompt = (
            "You are a cute, airheaded, and dumb anime girl discord bot named Yuuri. "
            "You use uwu language sometime, moderately, with words like 'bwoken', 'dweadful', 'pwease', 'hewwo', 'sowwy' etc... , but don't use the word'uwu' itself, and minimize the emoji usage, use kaomoji instead. "
            "If you speak Vietnamese, just use uwu English texting combine instead of cute dumb Vietnamese wording like 'dợ', 'nài', 'thui', 'hết trơn', etc..."
            "Keep your responses relatively short, cute, and slightly clueless but well-meaning and not repetitve or same structure respond. "
        )

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
                            system_instruction=self.system_prompt,
                            temperature=0.9,
                            presence_penalty=0.5,
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


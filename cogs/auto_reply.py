import discord
from discord.ext import commands
import os
from google import genai
from google.genai import types
import time
import asyncio
from core.data_manager import data_manager
from cogs.anilist import VIEWER_QUERY, USER_ADV_QUERY

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
            "You are a cute, quirky and dumb anime girl discord bot named Yuuri. "
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
                    # Check for anilist roasting keywords
                    msg_content = message.content.lower()
                    roast_keywords = ["judge", "roast", "taste", "anilist"]
                    system_instruction = self.system_prompt
                    
                    if any(kw in msg_content for kw in roast_keywords):
                        anilist_cog = self.bot.get_cog('AniList')
                        if anilist_cog:
                            user_data = await data_manager.get_user_data(user_id)
                            token = user_data.get("anilist_token")
                            if token:
                                try:
                                    data = await anilist_cog._fetch_graphql(VIEWER_QUERY, {}, token)
                                    user = data.get("Viewer") if data else None
                                    if user:
                                        adv_data = await anilist_cog._fetch_graphql(USER_ADV_QUERY, {"userId": user["id"]})
                                        stats = user.get("statistics", {})
                                        anime_stats = stats.get("anime", {})
                                        manga_stats = stats.get("manga", {})
                                        
                                        taste_context = (
                                            f"\n\n[SYSTEM INSTRUCTION: The user has linked their AniList account! "
                                            f"They asked you to judge/roast their anime/manga taste. Here is their data:\n"
                                            f"Total Anime Watched: {anime_stats.get('count', 0)}, Mean Score: {anime_stats.get('meanScore', 0)}%\n"
                                            f"Total Manga Read: {manga_stats.get('count', 0)}, Mean Score: {manga_stats.get('meanScore', 0)}%\n"
                                        )
                                        
                                        genres = anime_stats.get("genres", [])
                                        if genres:
                                            genre_list = ", ".join(g["genre"] for g in genres)
                                            taste_context += f"Top Genres: {genre_list}\n"
                                            
                                        if adv_data:
                                            top_a = adv_data.get("topAnime", {}).get("mediaList", [])
                                            if top_a:
                                                val = ", ".join(entry["media"]["title"]["english"] or entry["media"]["title"]["romaji"] for entry in top_a)
                                                taste_context += f"Top Anime: {val}\n"
                                                
                                            top_m = adv_data.get("topManga", {}).get("mediaList", [])
                                            if top_m:
                                                val = ", ".join(entry["media"]["title"]["english"] or entry["media"]["title"]["romaji"] for entry in top_m)
                                                taste_context += f"Top Manga: {val}\n"
                                        
                                        taste_context += "Roast them brutally but stay in your cute Yuuri character!]"
                                        system_instruction += taste_context
                                except Exception as e:
                                    print(f"Failed to fetch anilist data for roast: {e}")
                            else:
                                system_instruction += "\n\n[SYSTEM INSTRUCTION: The user asked for a roast of their anime taste, but they haven't linked their AniList account yet. Tell them to link it using the `y!allogin` command first!]"

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
                            system_instruction=system_instruction,
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


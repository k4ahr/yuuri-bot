import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from core.data_manager import data_manager
from cogs.admin import is_admin_or_role

DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en/"

class Noichu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_dictionary(self, word: str) -> int:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{DICTIONARY_API}{word}") as resp:
                    if resp.status == 200:
                        return 1
                    elif resp.status == 404:
                        return 0
                    else:
                        return -1
            except:
                return -1

    async def get_word_definition(self, word: str) -> dict:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{DICTIONARY_API}{word}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if not data: return None
                        
                        entry = data[0]
                        word_text = entry.get('word', word)
                        meanings = []
                        if 'meanings' in entry:
                            for meaning in entry['meanings']:
                                part = meaning.get('partOfSpeech', 'Unknown')
                                if meaning.get('definitions'):
                                    definition = meaning['definitions'][0].get('definition', 'N/A')
                                    meanings.append(f"**({part})** {definition}")
                        return {"word": word_text, "meanings": meanings}
            except:
                pass
        return None

    def update_score(self, user: discord.Member, state: dict, is_valid_play: bool):
        uid = str(user.id)
        if uid not in state["leaderboard"]:
            state["leaderboard"][uid] = {"score": 0, "streak": 0, "name": user.display_name}
        
        player_data = state["leaderboard"][uid]
        player_data["name"] = user.display_name
        
        if not is_valid_play:
            player_data["streak"] = 0
            return 0, 0
        
        current_streak = player_data["streak"] + 1
        player_data["streak"] = current_streak
        
        base_points = 10
        if current_streak < 3: multiplier = 1.0 
        elif current_streak <= 5: multiplier = 1.5 
        elif current_streak <= 10: multiplier = 2.0 
        else: multiplier = 3.0 
            
        points_earned = int(base_points * multiplier)
        player_data["score"] += points_earned
        return points_earned, multiplier

    @commands.hybrid_command(name="setnoichu", description="Sets the active word chain channel for the server.")
    @app_commands.describe(channel="The channel for the game.")
    @commands.check(is_admin_or_role)
    async def set_noichu(self, ctx: commands.Context, channel: discord.TextChannel = None):
        target_channel = channel or ctx.channel
        state = await data_manager.get_noichu_state(ctx.guild.id)
        state["channel_id"] = target_channel.id
        state["last_word"] = None
        state["used_words_list"] = []
        state["last_author_id"] = None
        await data_manager.save_noichu_state(ctx.guild.id, state)
        await ctx.send(f"✅ Set the word chain channel to {target_channel.mention}. The game has been reset!")

    @commands.hybrid_command(name="ncreset", description="Resets the word chain game data for the server.")
    @commands.check(is_admin_or_role)
    async def ncreset(self, ctx: commands.Context):
        state = await data_manager.get_noichu_state(ctx.guild.id)
        state["last_word"] = None
        state["used_words_list"] = []
        state["last_author_id"] = None
        await data_manager.save_noichu_state(ctx.guild.id, state)
        await ctx.send("✅ The word chain game has been reset!")

    @commands.hybrid_command(name="nclb", description="Shows the Top 10 leaderboard for the word chain game.")
    async def nclb(self, ctx: commands.Context):
        state = await data_manager.get_noichu_state(ctx.guild.id)
        lb_list = [v for k, v in state["leaderboard"].items()]
        lb_list.sort(key=lambda x: x["score"], reverse=True)
        
        if not lb_list: 
            return await ctx.send("📉 No word chain leaderboard data yet!")

        top_10 = lb_list[:10]
        embed = discord.Embed(title="🏆 Word Chain Leaderboard", color=discord.Color.gold())
        
        desc = ""
        for i, p in enumerate(top_10):
            rank = i + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            streak_icon = "🔥" if p['streak'] >= 3 else "" 
            streak_text = f"| {streak_icon} {p['streak']}" if p['streak'] > 0 else ""
            desc += f"**{medal} {p['name']}**: `{p['score']} pts` {streak_text}\n"
            
        embed.description = desc
        embed.set_footer(text=f"Top 10 / Total {len(lb_list)} players")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ncrank", description="Shows word chain game rank and stats for a specific user.")
    @app_commands.describe(member="The user to check.")
    async def ncrank(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        uid = str(target.id)
        state = await data_manager.get_noichu_state(ctx.guild.id)
        lb_data = state["leaderboard"]

        if uid not in lb_data:
            return await ctx.send(f"📉 **{target.display_name}** is not on the leaderboard yet. Play the game to earn points!")

        sorted_lb = sorted(lb_data.items(), key=lambda x: x[1]['score'], reverse=True)
        
        rank = next((i + 1 for i, (p_uid, _) in enumerate(sorted_lb) if p_uid == uid), -1)
        user_data = lb_data[uid]
        streak = user_data.get('streak', 0)
        score = user_data.get('score', 0)
        
        multiplier = "x1.0"
        if streak >= 11: multiplier = "x3.0"
        elif streak >= 6: multiplier = "x2.0"
        elif streak >= 3: multiplier = "x1.5"
        
        embed = discord.Embed(title=f"👤 Word Chain Stats: {target.display_name}", color=discord.Color.teal())
        embed.add_field(name="🏆 Rank", value=f"#{rank}", inline=True)
        embed.add_field(name="✨ Score", value=f"{score}", inline=True)
        embed.add_field(name="🔥 Win Streak", value=f"{streak} (Multiplier: {multiplier})", inline=False)
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nccount", description="Displays total game stats for the current server.")
    async def nccount(self, ctx: commands.Context):
        state = await data_manager.get_noichu_state(ctx.guild.id)
        count = len(state["used_words_list"])
        last = state["last_word"] or "None"
        await ctx.send(embed=discord.Embed(title="📊 Word Chain Game Stats", description=f"**Words chained:** {count}\n**Last word:** {last}", color=discord.Color.gold()))

    @commands.hybrid_command(name="define", description="Looks up the definition of the current or specified word.")
    @app_commands.describe(word="The word to look up. Leaves blank for the last word.")
    async def define(self, ctx: commands.Context, word: str = None):
        await ctx.defer()
        state = await data_manager.get_noichu_state(ctx.guild.id)
        target_word = word or state['last_word']
        
        if not target_word:
            return await ctx.send("❌ No word to define!")

        res = await self.get_word_definition(target_word)
        if not res: 
            return await ctx.send(f"❌ Could not find the definition for the word **'{target_word}'**.")

        embed = discord.Embed(title=f"📖 Definition: {res['word'].capitalize()}", description="\n".join(res['meanings'][:3]) if res['meanings'] else "N/A", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or not msg.guild: return
        
        state = await data_manager.get_noichu_state(msg.guild.id)
        if not state["channel_id"] or msg.channel.id != state["channel_id"]: return
        if msg.content.startswith("/"): return
        
        content = msg.content.strip().lower()
        if len(content.split()) > 1 or not content.isalpha(): return

        async def fail_play(reason_text, apply_punish=True):
            await msg.add_reaction("❌") 
            if not apply_punish:
                await msg.reply(reason_text)
                return

            uid = str(msg.author.id)
            current_streak = state["leaderboard"].get(uid, {}).get("streak", 0)
            
            self.update_score(msg.author, state, is_valid_play=False)
            await data_manager.save_noichu_state(msg.guild.id, state)
            
            suffix = "\n📉 *Your win streak has been reset to 0!*" if current_streak > 0 else ""
            await msg.reply(f"{reason_text}{suffix}")

        if state["last_author_id"] == msg.author.id:
            return await fail_play("❌ You just played, please wait for someone else to continue!", apply_punish=False) 

        last_word = state["last_word"]
        
        if last_word and content[0] != last_word[-1]: 
            return await fail_play(f"❌ Wrong word! It must start with the letter **'{last_word[-1].upper()}'**.")

        if content in state["used_words_list"]: 
            return await fail_play("❌ This word has already been used!")

        dict_status = await self.check_dictionary(content)
        if dict_status == -1:
            return await fail_play("❌ The dictionary API is currently down. Please try again later!", apply_punish=False)
        elif dict_status == 0:
            return await fail_play("❌ This is not a valid English word!")

        state["last_word"] = content
        state["last_author_id"] = msg.author.id
        state["used_words_list"].append(content)
        
        self.update_score(msg.author, state, is_valid_play=True)
        await data_manager.save_noichu_state(msg.guild.id, state)
        
        await msg.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(Noichu(bot))

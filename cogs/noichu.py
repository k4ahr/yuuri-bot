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

    async def check_dictionary(self, word: str) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{DICTIONARY_API}{word}") as resp:
                    return resp.status == 200
            except:
                return False

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

    @app_commands.command(name="setnoichu", description="Sets the active word chain channel for the server.")
    @app_commands.describe(channel="The channel for the game.")
    @app_commands.check(is_admin_or_role)
    async def set_noichu(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        state = await data_manager.get_noichu_state(interaction.guild_id)
        state["channel_id"] = target_channel.id
        state["last_word"] = None
        state["used_words_list"] = []
        state["last_author_id"] = None
        await data_manager.save_noichu_state(interaction.guild_id, state)
        await interaction.response.send_message(f"✅ Đã set kênh chơi nối chữ tại {target_channel.mention}. Game đã được reset!")

    @app_commands.command(name="ncreset", description="Resets the word chain game data for the server.")
    @app_commands.check(is_admin_or_role)
    async def ncreset(self, interaction: discord.Interaction):
        state = await data_manager.get_noichu_state(interaction.guild_id)
        state["last_word"] = None
        state["used_words_list"] = []
        state["last_author_id"] = None
        await data_manager.save_noichu_state(interaction.guild_id, state)
        await interaction.response.send_message("✅ Game nối chữ đã được reset!")

    @app_commands.command(name="nclb", description="Shows the Top 10 leaderboard for the word chain game.")
    async def nclb(self, interaction: discord.Interaction):
        state = await data_manager.get_noichu_state(interaction.guild_id)
        lb_list = [v for k, v in state["leaderboard"].items()]
        lb_list.sort(key=lambda x: x["score"], reverse=True)
        
        if not lb_list: 
            return await interaction.response.send_message("📉 Chưa có dữ liệu bảng xếp hạng nối chữ!")

        top_10 = lb_list[:10]
        embed = discord.Embed(title="🏆 Bảng Xếp Hạng Noichu", color=discord.Color.gold())
        
        desc = ""
        for i, p in enumerate(top_10):
            rank = i + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            streak_icon = "🔥" if p['streak'] >= 3 else "" 
            streak_text = f"| {streak_icon} {p['streak']}" if p['streak'] > 0 else ""
            desc += f"**{medal} {p['name']}**: `{p['score']} pts` {streak_text}\n"
            
        embed.description = desc
        embed.set_footer(text=f"Top 10 / Tổng {len(lb_list)} người chơi")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ncrank", description="Shows word chain game rank and stats for a specific user.")
    @app_commands.describe(member="The user to check.")
    async def ncrank(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        uid = str(target.id)
        state = await data_manager.get_noichu_state(interaction.guild_id)
        lb_data = state["leaderboard"]

        if uid not in lb_data:
            return await interaction.response.send_message(f"📉 **{target.display_name}** chưa có trong bảng xếp hạng. Hãy chơi game để kiếm điểm!")

        sorted_lb = sorted(lb_data.items(), key=lambda x: x[1]['score'], reverse=True)
        
        rank = next((i + 1 for i, (p_uid, _) in enumerate(sorted_lb) if p_uid == uid), -1)
        user_data = lb_data[uid]
        streak = user_data.get('streak', 0)
        score = user_data.get('score', 0)
        
        multiplier = "x1.0"
        if streak >= 11: multiplier = "x3.0"
        elif streak >= 6: multiplier = "x2.0"
        elif streak >= 3: multiplier = "x1.5"
        
        embed = discord.Embed(title=f"👤 Thống kê Nối Chữ: {target.display_name}", color=discord.Color.teal())
        embed.add_field(name="🏆 Hạng", value=f"#{rank}", inline=True)
        embed.add_field(name="✨ Điểm số", value=f"{score}", inline=True)
        embed.add_field(name="🔥 Chuỗi thắng", value=f"{streak} (Hệ số: {multiplier})", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nccount", description="Displays total game stats for the current server.")
    async def nccount(self, interaction: discord.Interaction):
        state = await data_manager.get_noichu_state(interaction.guild_id)
        count = len(state["used_words_list"])
        last = state["last_word"] or "None"
        await interaction.response.send_message(embed=discord.Embed(title="📊 Thống kê Game Nối Chữ", description=f"**Số từ đã nối:** {count}\n**Từ cuối cùng:** {last}", color=discord.Color.gold()))

    @app_commands.command(name="ncdefine", description="Looks up the definition of the current or specified word.")
    @app_commands.describe(word="The word to look up. Leaves blank for the last word.")
    async def ncdefine(self, interaction: discord.Interaction, word: str = None):
        await interaction.response.defer()
        state = await data_manager.get_noichu_state(interaction.guild_id)
        target_word = word or state['last_word']
        
        if not target_word:
            return await interaction.followup.send("❌ Không có từ để định nghĩa!")

        res = await self.get_word_definition(target_word)
        if not res: 
            return await interaction.followup.send(f"❌ Chịu, không tìm thấy nghĩa của từ **'{target_word}'**.")

        embed = discord.Embed(title=f"📖 Định nghĩa: {res['word'].capitalize()}", description="\n".join(res['meanings'][:3]) if res['meanings'] else "N/A", color=discord.Color.blue())
        await interaction.followup.send(embed=embed)

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
            
            suffix = "\n📉 *Chuỗi thắng của bạn đã về 0!*" if current_streak > 0 else ""
            await msg.reply(f"{reason_text}{suffix}")

        if state["last_author_id"] == msg.author.id:
            return await fail_play("❌ Bạn vừa chơi rồi, hãy đợi người khác nối tiếp!", apply_punish=False) 

        last_word = state["last_word"]
        
        if last_word and content[0] != last_word[-1]: 
            return await fail_play(f"❌ Sai từ! Phải bắt đầu bằng chữ cái **'{last_word[-1].upper()}'**.")

        if content in state["used_words_list"]: 
            return await fail_play("❌ Từ này đã được dùng rồi!")

        if not await self.check_dictionary(content): 
            return await fail_play("❌ Từ này không có trong từ điển tiếng Anh hợp lệ!")

        state["last_word"] = content
        state["last_author_id"] = msg.author.id
        state["used_words_list"].append(content)
        
        self.update_score(msg.author, state, is_valid_play=True)
        await data_manager.save_noichu_state(msg.guild.id, state)
        
        await msg.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(Noichu(bot))

import discord
import os
import json
import requests
import math
from discord.ext import commands, tasks
from datetime import datetime

# --- Configuration ---
VERSION = "1.7.5"
START_TIME = datetime.utcnow() 

TOKEN = os.getenv('DISCORD_TOKEN')
raw_role = os.getenv('ADMIN_ROLE', 'GameMaster')

if raw_role and raw_role.isdigit():
    ADMIN_ROLE = int(raw_role)
else:
    ADMIN_ROLE = raw_role

STATE_FILE = '/data/state.json'
LEADERBOARD_FILE = '/data/leaderboard.json'
CHANGELOG_FILE = 'changelogs.json'
DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en/"
REMINDER_TEXT = "🚧 **Note:** Bot vẫn đang trong quá trình phát triển và thử nghiệm, nếu thấy bất kì lỗi vấn đề hay có góp ý gì, hãy liên hệ `k4ahr_`."

# --- Global Cache (RAM) ---
GAME_CACHE = {
    "channel_id": None, 
    "last_word": None, 
    "used_words_set": set(), 
    "used_words_list": [],   
    "last_author_id": None,
    "leaderboard": {},
    "last_reminder": 0
}

# --- Setup Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='=', intents=intents)

# --- Utils ---
def load_json_file(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
    return None

def load_state_to_memory():
    global GAME_CACHE
    default_state = {"channel_id": None, "last_word": None, "used_words": [], "last_author_id": None, "last_reminder": 0}
    
    # Load Game State
    data = load_json_file(STATE_FILE) or default_state
    GAME_CACHE["channel_id"] = data.get("channel_id")
    GAME_CACHE["last_word"] = data.get("last_word")
    GAME_CACHE["last_author_id"] = data.get("last_author_id")
    GAME_CACHE["used_words_list"] = data.get("used_words", [])
    GAME_CACHE["used_words_set"] = set(data.get("used_words", []))
    GAME_CACHE["last_reminder"] = data.get("last_reminder", 0)
    
    # Load Leaderboard
    lb_data = load_json_file(LEADERBOARD_FILE) or {}
    GAME_CACHE["leaderboard"] = lb_data
    
    print(f"✅ State loaded: {len(GAME_CACHE['used_words_set'])} words | {len(GAME_CACHE['leaderboard'])} players.")

def save_state_from_memory():
    state_data = {
        "channel_id": GAME_CACHE["channel_id"],
        "last_word": GAME_CACHE["last_word"],
        "used_words": GAME_CACHE["used_words_list"],
        "last_author_id": GAME_CACHE["last_author_id"],
        "last_reminder": GAME_CACHE.get("last_reminder", 0)
    }
    lb_data = GAME_CACHE["leaderboard"]
    
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state_data, f)
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(lb_data, f)
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")

def update_score(user, is_valid_play):
    """Updates score and streak logic."""
    uid = str(user.id)
    if uid not in GAME_CACHE["leaderboard"]:
        GAME_CACHE["leaderboard"][uid] = {"score": 0, "streak": 0, "name": user.display_name}
    
    player_data = GAME_CACHE["leaderboard"][uid]
    player_data["name"] = user.display_name
    
    if not is_valid_play:
        player_data["streak"] = 0
        return 0, 0
    
    # Valid Play Logic
    current_streak = player_data["streak"] + 1
    player_data["streak"] = current_streak
    
    base_points = 10
    multiplier = 1.0
    
    if current_streak < 3:
        multiplier = 1.0 
    elif current_streak <= 5:
        multiplier = 1.5 
    elif current_streak <= 10:
        multiplier = 2.0 
    else:
        multiplier = 3.0 
        
    points_earned = int(base_points * multiplier)
    player_data["score"] += points_earned
    
    return points_earned, multiplier

def get_db_size():
    size = 0
    if os.path.exists(STATE_FILE): size += os.path.getsize(STATE_FILE)
    if os.path.exists(LEADERBOARD_FILE): size += os.path.getsize(LEADERBOARD_FILE)
    return f"{size / 1024:.2f} KB"

def get_word_definition(word):
    try:
        response = requests.get(f"{DICTIONARY_API}{word}")
        if response.status_code == 200:
            data = response.json()
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

def check_dictionary(word):
    try:
        return requests.get(f"{DICTIONARY_API}{word}").status_code == 200
    except:
        return False

# --- UI Views ---

class PaginationView(discord.ui.View):
    def __init__(self, data, title, formatter, per_page=10):
        super().__init__(timeout=60)
        self.data = data
        self.title = title
        self.formatter = formatter
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = math.ceil(len(data) / per_page)
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page >= self.total_pages - 1)

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_items = self.data[start:end]

        embed = discord.Embed(title=self.title, color=discord.Color.gold())
        description = ""
        
        for i, item in enumerate(page_items):
            rank = start + i + 1
            description += self.formatter(rank, item) + "\n"
            
        embed.description = description or "Chưa có dữ liệu."
        embed.set_footer(text=f"Trang {self.current_page + 1}/{self.total_pages} • Tổng {len(self.data)}")
        return embed

    @discord.ui.button(label="Trước", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction, button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Sau", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction, button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

# --- Commands ---

@bot.command(name='leaderboard', aliases=['lb', 'top'])
async def leaderboard_command(ctx):
    lb_list = [v for k, v in GAME_CACHE["leaderboard"].items()]
    lb_list.sort(key=lambda x: x["score"], reverse=True)
    
    if not lb_list: return await ctx.send("📉 Chưa có dữ liệu bảng xếp hạng!")

    def fmt(rank, p):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        streak_icon = "🔥" if p['streak'] >= 3 else "" 
        streak_text = f"| {streak_icon} {p['streak']}" if p['streak'] > 0 else ""
        return f"**{medal} {p['name']}**: `{p['score']} pts` {streak_text}"

    view = PaginationView(lb_list, "🏆 Bảng Xếp Hạng Noichu", fmt, per_page=10)
    await ctx.send(embed=view.create_embed(), view=view)

@bot.command(name='rank', aliases=['me', 'stats'])
async def rank_command(ctx, member: discord.Member = None):
    target = member or ctx.author
    uid = str(target.id)
    lb_data = GAME_CACHE["leaderboard"]

    if uid not in lb_data:
        return await ctx.send(f"📉 **{target.display_name}** chưa có trong bảng xếp hạng. Hãy chơi game để kiếm điểm!")

    sorted_lb = sorted(lb_data.items(), key=lambda x: x[1]['score'], reverse=True)
    
    rank = -1
    for i, (p_uid, data) in enumerate(sorted_lb):
        if p_uid == uid:
            rank = i + 1
            break
    
    user_data = lb_data[uid]
    streak = user_data.get('streak', 0)
    score = user_data.get('score', 0)
    
    multiplier = "x1.0"
    if streak >= 11: multiplier = "x3.0"
    elif streak >= 6: multiplier = "x2.0"
    elif streak >= 3: multiplier = "x1.5"
    
    embed = discord.Embed(title=f"👤 Thống kê: {target.display_name}", color=discord.Color.teal())
    embed.add_field(name="🏆 Hạng", value=f"#{rank}", inline=True)
    embed.add_field(name="✨ Điểm số", value=f"{score}", inline=True)
    embed.add_field(name="🔥 Chuỗi thắng", value=f"{streak} (Hệ số: {multiplier})", inline=False)
    
    if member:
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
        
    await ctx.send(embed=embed)

@bot.command(name='changelogs', aliases=['changes', 'history'])
async def changelogs_command(ctx):
    data = load_json_file(CHANGELOG_FILE)
    if not data: return await ctx.send("❌ Thiếu file changelogs.json")
    
    def fmt(rank, item):
        ver = item.get('version', '???')
        tags = f" ({item.get('tags')})" if item.get('tags') else ""
        changes = "\n".join([f"• {c}" for c in item.get('changes', [])])
        return f"**v{ver}{tags}**\n{changes}\n"

    view = PaginationView(data, "📜 Lịch sử cập nhật", fmt, per_page=3)
    await ctx.send(embed=view.create_embed(), view=view)

@bot.command(name='count', aliases=['score'])
async def count_command(ctx):
    count = len(GAME_CACHE["used_words_list"])
    last = GAME_CACHE["last_word"] or "None"
    await ctx.send(embed=discord.Embed(title="📊 Thống kê Game", description=f"**Số từ:** {count}\n**Database:** {get_db_size()}\n**Từ cuối:** {last}", color=discord.Color.gold()))

@bot.command(name='define')
async def define_command(ctx, *, word: str = None):
    target = "Tra cứu"
    if not word:
        word = GAME_CACHE['last_word']
        target = "Từ cuối cùng"
        if not word: return await ctx.send("❌ Không có từ để định nghĩa!")

    res = get_word_definition(word)
    if not res: return await ctx.send(f"❌ Chịu, không hiểu **'{word}'** là gì.")

    embed = discord.Embed(title=f"📖 Định nghĩa: {res['word'].capitalize()}", description="\n".join(res['meanings'][:3]) if res['meanings'] else "N/A", color=discord.Color.blue())
    embed.set_footer(text=f"Nguồn: {target}")
    await ctx.send(embed=embed)

# --- Background Task ---

@tasks.loop(hours=12) # Check periodically if 30 days have passed
async def development_reminder():
    cid = GAME_CACHE.get('channel_id')
    if not cid: return
    
    now = datetime.utcnow().timestamp()
    last_time = GAME_CACHE.get("last_reminder", 0)
    
    # Skip startup spam
    if last_time == 0:
        GAME_CACHE["last_reminder"] = now
        save_state_from_memory()
        return
        
    # Check if 30 days (2,592,000 seconds) have passed
    if now - last_time < 2592000:
        return 

    ch = bot.get_channel(cid)
    if not ch: return
    try:
        async for msg in ch.history(limit=1):
            if msg.author == bot.user and msg.content == REMINDER_TEXT: return
    except: pass
    
    await ch.send(REMINDER_TEXT)
    
    GAME_CACHE["last_reminder"] = now
    save_state_from_memory()

# --- Admin Commands ---

@bot.command(name='status')
@commands.has_role(ADMIN_ROLE)
async def status_command(ctx):
    uptime = str(datetime.utcnow() - START_TIME).split('.')[0]
    total = len(GAME_CACHE["used_words_list"])
    cid = GAME_CACHE["channel_id"]
    
    embed = discord.Embed(title="🤖 Noichu Status", color=discord.Color.green())
    embed.add_field(name="Version", value=f"v{VERSION}", inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Uptime", value=uptime, inline=True)
    embed.add_field(name="Channel", value=f"<#{cid}>" if cid else "❌", inline=True)
    embed.add_field(name="Data", value=f"{total} words ({get_db_size()})", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='setchannel')
@commands.has_role(ADMIN_ROLE)
async def set_channel(ctx):
    GAME_CACHE.update({'channel_id': ctx.channel.id, 'last_word': None, 'used_words_list': [], 'used_words_set': set(), 'last_author_id': None})
    save_state_from_memory()
    await ctx.send(f"✅ Đã set kênh chơi tại {ctx.channel.mention}.")

@bot.command(name='reset')
@commands.has_role(ADMIN_ROLE)
async def reset_game(ctx):
    GAME_CACHE.update({'last_word': None, 'used_words_list': [], 'used_words_set': set(), 'last_author_id': None})
    save_state_from_memory()
    await ctx.message.add_reaction("🔄")
    await ctx.send("Game reset!")

@bot.command(name='version')
@commands.has_role(ADMIN_ROLE)
async def version_command(ctx):
    await ctx.send(f"ℹ️ Version **v{VERSION}**")

@set_channel.error
@reset_game.error
@status_command.error
@version_command.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingRole): await ctx.send("⛔ Không có quyền.")

# --- Game Logic ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (v{VERSION})')
    load_state_to_memory()
    if not development_reminder.is_running(): development_reminder.start()

@bot.event
async def on_message(msg):
    await bot.process_commands(msg)
    if msg.author.bot or not GAME_CACHE["channel_id"] or msg.channel.id != GAME_CACHE["channel_id"] or msg.content.startswith(bot.command_prefix): return
    
    content = msg.content.strip().lower()
    if len(content.split()) > 1 or not content.isalpha(): return

    # --- VALIDATION FAILED Handlers ---
    async def fail_play(reason_text, apply_punish=True):
        await msg.add_reaction("❌") 
        
        if not apply_punish:
            await msg.reply(reason_text)
            return

        uid = str(msg.author.id)
        current_streak = GAME_CACHE["leaderboard"].get(uid, {}).get("streak", 0)
        
        update_score(msg.author, is_valid_play=False)
        save_state_from_memory()
        
        suffix = "\n📉 *Chuỗi thắng của bạn đã về 0!*" if current_streak > 0 else ""
        await msg.reply(f"{reason_text}{suffix}")

    if GAME_CACHE["last_author_id"] == msg.author.id:
        return await fail_play("❌ Bạn vừa chơi rồi!", apply_punish=False) 

    last_word = GAME_CACHE["last_word"]
    
    if last_word and content[0] != last_word[-1]: 
        return await fail_play(f"❌ Sai từ! Phải bắt đầu bằng **'{last_word[-1].upper()}'**.")

    if content in GAME_CACHE["used_words_set"]: 
        return await fail_play("❌ Từ này dùng rồi!")

    if not check_dictionary(content): 
        return await fail_play("❌ Từ gì lạ vậy?")

    # --- VALIDATION SUCCESS ---
    GAME_CACHE.update({"last_word": content, "last_author_id": msg.author.id})
    GAME_CACHE["used_words_list"].append(content)
    GAME_CACHE["used_words_set"].add(content)
    
    update_score(msg.author, is_valid_play=True)
    save_state_from_memory()
    
    await msg.add_reaction("✅")

bot.run(TOKEN)
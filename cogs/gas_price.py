import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os

class GasPrice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://portals.petrolimex.com.vn/~apis/portals/cms.item/search?object-identity=search&x-request=eyJGaWx0ZXJCeSI6eyJBbmQiOlt7IlN5c3RlbUlEIjp7IkVxdWFscyI6IjY3ODNkYzEyNzFmZjQ0OWU5NWI3NGE5NTIwOTY0MTY5In19LHsiUmVwb3NpdG9yeUlEIjp7IkVxdWFscyI6ImE5NTQ1MWUyM2I0NzRmZTU4ODZiZmI3Y2Y4NDNmNTNjIn19LHsiUmVwb3NpdG9yeUVudGl0eUlEIjp7IkVxdWFscyI6IjM4MDEzNzhmZTFlMDQ1YjFhZmExMGRlN2M1Nzc2MTI0In19LHsiU3RhdHVzIjp7IkVxdWFscyI6IlB1Ymxpc2hlZCJ9fV19LCJTb3J0QnkiOnsiTGFzdE1vZGlmaWVkIjoiRGVzY2VuZGluZyJ9LCJQYWdpbmF0aW9uIjp7IlRvdGFsUmVjb3JkcyI6LTEsIlRvdGFsUGFnZXMiOjAsIlBhZ2VTaXplIjowLCJQYWdlTnVtYmVyIjowfX0="

    def format_price(self, price: float) -> str:
        int_price = int(price)
        s = str(int_price)
        if len(s) > 3:
            return s[:-3] + "." + s[-3:]
        return s

    @app_commands.command(name="gas", description="Fetches the latest gas prices from Petrolimex.")
    async def get_gas_price(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.petrolimex.com.vn",
            "Referer": "https://www.petrolimex.com.vn/"
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.api_url, headers=headers) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("Failed to fetch gas prices.")
                        return
                    
                    data = await resp.json()
                    objects = data.get("Objects", [])
                    
                    embed = discord.Embed(
                        title="⛽ Bảng Giá Xăng Dầu Petrolimex", 
                        description="Dưới đây là giá bán lẻ cập nhật mới nhất:\n\n",
                        color=discord.Color.brand_green(), 
                        url="https://petrolimex.com.vn/",
                        timestamp=discord.utils.utcnow()
                    )
                    
                    added = False
                    
                    for item in objects:
                        title = item.get("Title", "")
                        z1 = item.get("Zone1Price", 0)
                        z2 = item.get("Zone2Price", 0)
                        
                        if title and z1 > 0:
                            added = True
                            z1_str = f"{self.format_price(z1)} đ"
                            z2_str = f"{self.format_price(z2)} đ"
                            
                            # Decide on an emoji based on fuel type
                            if "Xăng" in title:
                                emoji = "🚗"
                            elif "DO" in title:
                                emoji = "🚚"
                            elif "hỏa" in title:
                                emoji = "🔥"
                            elif "Mazut" in title:
                                emoji = "⛴️"
                            else:
                                emoji = "💧"
                                
                            embed.description += f"**{emoji} {title}**\n> 🟢 `Vùng 1:` **{z1_str}**\n> 🟡 `Vùng 2:` **{z2_str}**\n\n"
                    
                    if added:
                        embed.set_footer(text="Nguồn: petrolimex.com.vn")
                        
                        file = None
                        if os.path.exists("assets/images/gas_banner.gif"):
                            file = discord.File("assets/image/gas_banner.gif", filename="gas_banner.gif")
                            embed.set_image(url="attachment://gas_banner.gif")
                            
                        if file:
                            await interaction.followup.send(embed=embed, file=file)
                        else:
                            await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("No prices found.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred while fetching gas prices: {e}")

async def setup(bot):
    await bot.add_cog(GasPrice(bot))

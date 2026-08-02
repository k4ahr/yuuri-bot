import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import datetime
from core.data_manager import data_manager

ANILIST_API_URL = "https://graphql.anilist.co"

# GraphQL Queries
MEDIA_QUERY = """
query ($search: String, $type: MediaType) {
  Media(search: $search, type: $type) {
    id
    title {
      english
      romaji
    }
    coverImage {
      large
    }
    description(asHtml: false)
    format
    episodes
    chapters
    startDate {
      year
      month
      day
    }
    averageScore
    tags {
      name
      rank
    }
    studios(isMain: true) {
      nodes {
        name
      }
    }
    staff {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    relations {
      edges {
        relationType
        node {
          title {
            english
            romaji
          }
          type
        }
      }
    }
    mediaListEntry {
      status
      progress
    }
  }
}
"""

CHARACTER_QUERY = """
query ($search: String) {
  Character(search: $search) {
    id
    name {
      full
      native
      userPreferred
    }
    image {
      large
    }
    gender
    age
    description(asHtml: false)
    favourites
  }
}
"""

STAFF_QUERY = """
query ($search: String) {
  Staff(search: $search) {
    id
    name {
      full
      native
      userPreferred
    }
    image {
      large
    }
    gender
    description(asHtml: false)
    favourites
  }
}
"""

class AniList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    anilist = app_commands.Group(name="anilist", description="AniList integration commands")

    async def _fetch_graphql(self, query: str, variables: dict, token: str = None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        async with aiohttp.ClientSession() as session:
            async with session.post(ANILIST_API_URL, json={"query": query, "variables": variables}, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data")
                elif resp.status == 404:
                    return None
                else:
                    text = await resp.text()
                    raise Exception(f"API Error {resp.status}: {text}")

    @anilist.command(name="login", description="Link your AniList account to the bot.")
    async def al_login(self, interaction: discord.Interaction):
        client_id = os.getenv("ANILIST_CLIENT_ID")
        redirect_uri = os.getenv("ANILIST_REDIRECT_URI")
        
        if not client_id or not redirect_uri:
            await interaction.response.send_message("AniList integration is not fully configured (missing Client ID or Redirect URI). Please contact the bot admin.", ephemeral=True)
            return

        state = data_manager.encrypt_string(str(interaction.user.id))
        auth_url = f"https://anilist.co/api/v2/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Click to Link AniList Account", url=auth_url, style=discord.ButtonStyle.link))
        
        await interaction.response.send_message("Please click the button below to authorize the bot on AniList. The linking will happen automatically!", view=view, ephemeral=True)

    def clean_html(self, text):
        if not text:
            return "No description available."
        import re
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        if len(text) > 500:
            return text[:497] + "..."
        return text

    async def _handle_media_search(self, interaction: discord.Interaction, query: str, media_type: str):
        await interaction.response.defer()
        
        user_data = await data_manager.get_user_data(interaction.user.id)
        token = user_data.get("anilist_token")

        try:
            data = await self._fetch_graphql(MEDIA_QUERY, {"search": query, "type": media_type}, token)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")
            return

        if not data or not data.get("Media"):
            await interaction.followup.send(f"❌ Could not find any {media_type.lower()} matching `{query}`.")
            return

        media = data["Media"]
        title_en = media["title"]["english"] or media["title"]["romaji"]
        title_romaji = media["title"]["romaji"]
        url = f"https://anilist.co/{media_type.lower()}/{media['id']}"
        
        embed = discord.Embed(title=title_en, url=url, color=discord.Color.blue())
        if media["coverImage"]["large"]:
            embed.set_thumbnail(url=media["coverImage"]["large"])
            
        embed.description = self.clean_html(media["description"])
        
        # Author / Studio
        if media_type == "ANIME":
            studios = [s["name"] for s in media["studios"]["nodes"]]
            if studios:
                embed.add_field(name="Studio", value=", ".join(studios), inline=True)
        else:
            # Find author/artist in staff
            authors = []
            for edge in media["staff"]["edges"]:
                role = edge["role"].lower()
                if "story" in role or "art" in role or "original creator" in role:
                    authors.append(edge["node"]["name"]["full"])
            if authors:
                embed.add_field(name="Author", value=", ".join(set(authors)), inline=True)

        # Format & Eps/Chapters
        fmt = media.get("format", "Unknown").replace("_", " ") if media.get("format") else "Unknown"
        length = f"{media.get('episodes', '?')} Eps" if media_type == "ANIME" else f"{media.get('chapters', '?')} Chp"
        embed.add_field(name="Format", value=f"{fmt} ({length})", inline=True)
        
        # Release Date
        sd = media.get("startDate", {})
        date_str = "Unknown"
        if sd.get("year"):
            date_str = f"{sd.get('year')}-{sd.get('month', '01'):02d}-{sd.get('day', '01'):02d}"
        embed.add_field(name="Release Date", value=date_str, inline=True)
        
        # Score
        score = media.get("averageScore")
        embed.add_field(name="Average Score", value=f"{score}%" if score else "N/A", inline=True)
        
        # Tags (Top 4)
        tags = media.get("tags", [])
        tags = sorted(tags, key=lambda t: t.get("rank", 0), reverse=True)[:4]
        if tags:
            embed.add_field(name="Tags", value=", ".join(t["name"] for t in tags), inline=False)
            
        # Relations (Source, Prequel, Sequel)
        relations = []
        for edge in media.get("relations", {}).get("edges", []):
            rel_type = edge["relationType"].replace("_", " ").title()
            if rel_type in ["Source", "Prequel", "Sequel", "Alternative"]:
                rel_title = edge["node"]["title"]["english"] or edge["node"]["title"]["romaji"]
                relations.append(f"**{rel_type}**: {rel_title}")
        if relations:
            embed.add_field(name="Relations", value="\n".join(relations[:3]), inline=False)

        # User Status
        if media.get("mediaListEntry"):
            entry = media["mediaListEntry"]
            status = entry.get("status", "UNKNOWN").replace("_", " ").title()
            progress = entry.get("progress", 0)
            embed.add_field(name="Your Status", value=f"{status} - {progress} {length.split()[1].lower()}", inline=False)

        await interaction.followup.send(embed=embed)

    @anilist.command(name="anime", description="Search for an anime on AniList")
    async def search_anime(self, interaction: discord.Interaction, query: str):
        await self._handle_media_search(interaction, query, "ANIME")

    @anilist.command(name="manga", description="Search for a manga on AniList")
    async def search_manga(self, interaction: discord.Interaction, query: str):
        await self._handle_media_search(interaction, query, "MANGA")

    @anilist.command(name="character", description="Search for a character on AniList")
    async def search_character(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        try:
            data = await self._fetch_graphql(CHARACTER_QUERY, {"search": query})
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")
            return
            
        if not data or not data.get("Character"):
            await interaction.followup.send(f"❌ Could not find any character matching `{query}`.")
            return
            
        char = data["Character"]
        url = f"https://anilist.co/character/{char['id']}"
        
        embed = discord.Embed(url=url, color=discord.Color.green())
        
        # Names
        name = char["name"]
        en_name = name.get("full") or name.get("userPreferred") or "Unknown"
        jp_name = name.get("native") or ""
        embed.title = f"{en_name} {f'({jp_name})' if jp_name else ''}"
        
        if char["image"]["large"]:
            embed.set_thumbnail(url=char["image"]["large"])
            
        embed.description = self.clean_html(char["description"])
        
        embed.add_field(name="Gender", value=char.get("gender") or "Unknown", inline=True)
        
        # Height/Age (using age since height isn't always distinct in GraphQL easily, but let's check if age contains height or if we can find height)
        # Actually in AniList 'age' often contains height or other stats.
        if char.get("age"):
            embed.add_field(name="Age/Height", value=char.get("age")[:100], inline=True)
            
        embed.add_field(name="Favourites", value=str(char.get("favourites", 0)), inline=True)
        
        await interaction.followup.send(embed=embed)
        
    @anilist.command(name="staff", description="Search for a staff/author on AniList")
    async def search_staff(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        try:
            data = await self._fetch_graphql(STAFF_QUERY, {"search": query})
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}")
            return
            
        if not data or not data.get("Staff"):
            await interaction.followup.send(f"❌ Could not find any staff matching `{query}`.")
            return
            
        staff = data["Staff"]
        url = f"https://anilist.co/staff/{staff['id']}"
        
        embed = discord.Embed(url=url, color=discord.Color.purple())
        
        # Names
        name = staff["name"]
        en_name = name.get("full") or name.get("userPreferred") or "Unknown"
        jp_name = name.get("native") or ""
        embed.title = f"{en_name} {f'({jp_name})' if jp_name else ''}"
        
        if staff["image"]["large"]:
            embed.set_thumbnail(url=staff["image"]["large"])
            
        embed.description = self.clean_html(staff["description"])
        
        embed.add_field(name="Gender", value=staff.get("gender") or "Unknown", inline=True)
        embed.add_field(name="Favourites", value=str(staff.get("favourites", 0)), inline=True)
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AniList(bot))

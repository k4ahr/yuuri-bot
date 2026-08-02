import os
import aiohttp
from aiohttp import web
from core.data_manager import data_manager

async def handle_callback(request):
    code = request.query.get('code')
    state = request.query.get('state')
    
    if not code or not state:
        return web.Response(text="Missing code or state parameter.", status=400)
        
    user_id_str = data_manager.decrypt_string(state)
    if not user_id_str or not user_id_str.isdigit():
        return web.Response(text="Invalid or expired state parameter.", status=400)
        
    user_id = int(user_id_str)
    
    client_id = os.getenv("ANILIST_CLIENT_ID")
    client_secret = os.getenv("ANILIST_CLIENT_SECRET")
    redirect_uri = os.getenv("ANILIST_REDIRECT_URI")
    
    if not client_id or not client_secret or not redirect_uri:
        return web.Response(text="Server missing AniList OAuth configuration.", status=500)
        
    token_url = "https://anilist.co/api/v2/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                access_token = data.get("access_token")
                if access_token:
                    await data_manager.set_user_data(user_id, "anilist_token", access_token)
                    html = """
                    <html>
                    <head><title>Success</title><style>body { font-family: sans-serif; text-align: center; margin-top: 50px; background: #1a1a1a; color: #fff; }</style></head>
                    <body>
                        <h2>Authorization Successful!</h2>
                        <p>Your AniList account has been linked to your Discord account.</p>
                        <p>You may now close this tab and return to Discord.</p>
                        <script>
                            setTimeout(() => { window.close(); }, 5000);
                        </script>
                    </body>
                    </html>
                    """
                    return web.Response(text=html, content_type="text/html")
            
            error_text = await resp.text()
            return web.Response(text=f"Failed to fetch token from AniList: {resp.status} {error_text}", status=400)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/callback', handle_callback)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("WEB_SERVER_PORT", "8541"))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    print(f"Starting AniList OAuth web server on port {port}")
    await site.start()

# Yuuri: A multi-functions Discord bot for moe and funzie

![image](assets/images/help_banner.png)

# Current functions
* A honeypot channel setup to autoban spammers/bot accounts
* Showing newest gas price in Vietnam
* Safebooru image search
* Data encryption
* String triggers
* Word chains/Dictionary search
* Auto embed fixers for multiple platforms (Facebook, Twitter/X, TikTok, Instagram, pixiv, AniList)
* AniList integration  
* *More to be added in the future*


# Installation


## Create a bot profile
1. Go to [Discord Developer Portal](https://discord.com/developers/home)
2. Select Application > New Application
3. Give your bot a nice name/picture
4. At the Application control panel, head over to "Bot" tab, reset the token and save your new token for later
5. Scroll down and enable "Message Content Intent"
6. Go over to "OAuth2" tab and head to the "OAuth2 URL Generator" section
7. Tick into at least two of these boxes:
    * bot
    * application.commands
8. Copy the generated URL from the bottom and invite the bot to your server

## Create an encryption key
1. Install pip and python
2. Install Fernet using pip
   ```bash
   $ pip install Fernet
   ```
3. Create an encryption key
   ```bash
   $ python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. You will get a random encryption key, copy it for later

## Start the bot with Docker Compose
1. Clone the repository:
   ```bash
   $ git clone https://github.com/k4ahr/yuuri-bot
   $ cd yuuri-bot
   ```
2. Create a .env file from the repository template and edit it
    ```bash
    $ cp .env.example .env

    # You can use whatever text editor you want (vim, nano, notepad.exe, etc)
    $ vim .env
    ```

3. Add your Discord Bot token and your encryption key into the .env file  (if you don't know how to create a Discord Bot token, please Google it and come back here)
    ```bash
    DISCORD_TOKEN=YOUR.TOKEN.GOES.HERE
    ENCRYPTION_KEY=YOUR.KEY.GOES.HERE
    ```

3. Start the bot using Docker Compose:
   ```bash
   $ docker compose up -d --build
   ```

## Adding AniList integration
1. Go to [AniList developer page](https://anilist.co/settings/developer)
2. Create a client, add your name and your callback URL
3. You will get your Client ID and Client Secret, add that two to your `.env` that you created before with your callback URL and the port
4. Change the port to your desire port in `docker-compose.yml`

## Update the bot
1. Update the repository
    ```bash
    $ cd yuuri-bot
    $ git pull
    ```

2. Rebuild the bot and start it
    ```bash
    $ docker compose up -d --build
    ```


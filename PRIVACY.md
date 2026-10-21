# Privacy Policy for Yuuri Bot

*Last Updated: 14-October-2026*

This Privacy Policy describes how **Yuuri Bot** ("the Bot", "we", "our") collects, processes, secures, and retains information when you add the Bot to your Discord server or interact with its commands and features.

We are committed to maintaining user trust and adhering to principles of data minimization and security.

---

## 1. Information We Collect and Store

We strictly limit data collection to what is required for the Bot's core functionality:

### A. Encrypted Server Configuration (`servers_config.enc`)
To persist server-specific settings across restarts, the Bot stores:
* **Discord Server (Guild) ID:** Identifies your server in our database.
* **Configured Channel IDs:** Designated channels for logging, honeypots, and word chain games.
* **Configured Role IDs:** Roles assigned as Admin or Supporter within the Bot's permission system.
* **Server Customizations:** Custom command prefixes, custom trigger words and their associated responses, custom ping replies, and link fixer preferences.
* **AI Configuration:** Server AI activation status (licensed server ID), toggle status, and custom system prompts.

### B. Encrypted User Account Integrations (`users_config.enc`)
* **AniList OAuth Tokens:** When a user optionally links their AniList account via `/allogin`, their Discord User ID and AniList OAuth access token are stored strictly to manage their anime/manga lists and status directly from Discord.

### C. Game Data & Leaderboards (`noichu_progress.json`)
For the Word Chain ("Nối Chữ") game:
* **User Identifiers:** Discord User ID and server display name.
* **Game Statistics:** Scores, win streaks, and leaderboard rankings.
* **Game State:** The last word played, the Discord User ID of the last player, and the list of used words in the current game session.

---

## 2. Ephemeral & Transient Processing (Data NOT Permanently Stored)

Certain features process message data dynamically in real time without storing it in permanent databases:

* **AI Chat Interactions:** When the Bot is explicitly @mentioned or when a user replies to an AI-generated message, the Bot reads up to 50 recent messages from that channel to build conversational context. This text is sent directly to the Google Gemini API to generate a reply. **Yuuri Bot does not store, archive, or log your conversation history to persistent storage.**
* **Media & Quote Generation:** Images, user avatars, and media files processed through `/quote` or `/gifmaker` are handled in-memory and in temporary operating system files that are automatically deleted immediately after the output is generated.
* **Link Fixer:** Message contents containing supported social media URLs (Twitter/X, TikTok, Instagram, Reddit, Threads, Pixiv, Spotify, Facebook) are scanned solely to generate clean embed links and suppress the original embed. Neither the message text nor the links are logged or retained.
* **Anonymous `/say` Logging:** When an authorized user executes the `/say` command, the sender's identity, message content, and target channel are forwarded directly to the server's configured private log channel so server administrators can audit usage. The Bot does not store this message in its persistent database.
* **Honeypot Channel:** Messages sent in the honeypot channel are inspected only to trigger the ban action, log the event to the designated log channel, and delete the offending message.

---

## 3. Information We DO NOT Collect
* We **do not** collect personal real-world identities, real names, passwords, email addresses, phone numbers, or payment/financial information.
* We **do not** collect or monitor private direct messages (DMs), except for receiving activation keys via `y!aiactivate` or sending honeypot ban notifications.
* We **do not** build or retain continuous message history or chat logs across servers.

---

## 4. How We Use Collected Information
Data collected by the Bot is used exclusively to:
* Execute requested bot commands, games, and features.
* Enforce server-level configurations, prefixes, and role-based permissions.
* Maintain fair and accurate game leaderboards.
* Provide secure account integration with AniList on behalf of the user.

We **do not** sell, rent, monetize, or trade your data to third parties, advertising networks, or data brokers.

---

## 5. Third-Party Services
The Bot interacts with the following external APIs to fulfill specific features:
* **Discord API:** To provide bot operations and deliver messages.
* **Google Gemini API:** To generate dynamic AI conversational responses when the AI feature is invoked.
* **AniList API:** To retrieve anime/manga metadata and update user profile lists.
* **Content Providers:** Safebooru, Danbooru (NSFW channels only), Petrolimex (gas prices), and Ditmenavi (văn mẫu). Queries to these services contain only search tags or IDs.

Data sent to third-party services is subject to their respective privacy policies and terms.

---

## 6. Data Security & Storage
* All sensitive configuration files (`servers_config.enc` and `users_config.enc`) are encrypted at rest using **Fernet symmetric encryption (AES-128 in CBC mode with HMAC SHA-256)**.
* Game progression data (`noichu_progress.json`) contains only public Discord IDs, display names, and game scores.
* Database files are stored locally on the Bot's dedicated host server. Access to the host environment and encryption keys is strictly limited to the Bot developer.

---

## 7. Data Retention & Deletion Rights
* **AniList Account Disconnection:** Users can remove their stored AniList OAuth tokens at any time by running `/allogout`. The stored token is permanently deleted immediately.
* **Server Data Deletion:** When the Bot is removed or kicked from a server, server administrators may request that all stored configurations for that Guild ID be permanently erased.
* **Individual Data Deletion:** Users may request the deletion of their leaderboard stats or stored user data by contacting the developer.
* **Inquiries & Requests:** To request complete data deletion, please contact us at [k4ahr@disroot.org](mailto:k4ahr@disroot.org). Requests will be processed promptly within 7 business days.

---

## 8. Changes to This Privacy Policy
We may update this Privacy Policy from time to time to reflect changes in the Bot's features or legal requirements. The updated date at the top of this document will indicate the effective date of the latest revisions.

---

## 9. Contact Information
If you have questions, feedback, or data privacy requests regarding Yuuri Bot, please contact:
* **Developer:** Kabonar0
* **Email:** [k4ahr@disroot.org](mailto:k4ahr@disroot.org)

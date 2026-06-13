# Privacy Policy for Yuuri Bot

*Last Updated: 14-June-2026*

This Privacy Policy explains how **Yuuri Bot** ("the Bot") collects, uses, and protects your data when you use its services on Discord. By inviting the Bot to your server or using its commands, you agree to the terms outlined below.

## 1. What Data We Collect
The Bot only collects data that is necessary for its features to function properly. This includes:

*   **Server Configuration Data:** Channel IDs (e.g., log channels, honeypot channels, game channels), Role IDs (e.g., admin and supporter roles), and custom server settings (e.g., custom mention responses).
*   **User Identifiers:** Your Discord User ID and Display Name are collected strictly for the purpose of maintaining game leaderboards (e.g., the "noichu" word chain game).
*   **Game Data:** During the "noichu" (word chain) game, the Bot temporarily stores the last word played, the Discord ID of the last player, and a list of used words to enforce game rules.

## 2. What Data We DO NOT Collect
*   **Message Content:** The Bot **does not** log or store the content of your personal messages. Message content is only processed dynamically in specific channels (like the word chain game) to verify if it is a valid word, but it is not permanently stored unless it becomes part of the active game state.
*   **Personal Information:** The Bot does not ask for or store passwords, emails, or any identifying real-world information.

## 3. How Data is Used
The data we collect is used entirely to provide functionality within your server:
*   To track scores, ranks, and streaks on the word chain game leaderboards.
*   To enforce command permissions (e.g., ensuring only Admins or Supporters can use specific commands).
*   To route automated actions (like logging honeypot triggers or the `/say` command to the correct channel).

## 4. Data Storage and Security
All collected data is stored securely in a local JSON file format (`servers.json`) on the Bot's host machine. Access to this data is restricted solely to the bot's developer(s). 

## 5. Data Removal
If you wish to have your server's data removed from the Bot's database:
*   Server Administrators can remove the Bot from their server. Upon removal or upon request, all configurations associated with that server ID can be wiped.
*   To request manual data deletion (including your individual leaderboard data), please contact the developer directly.

## 6. Contact Information
If you have any questions or concerns about this Privacy Policy, please contact the developer through email at [k4ahr@disroot.org].

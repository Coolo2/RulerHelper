# RulerHelper

A discord bot for RulerCraft which tracks the server and shows many stats, allowing you to interact with the server from your discord

## Feature overview

- Get commands: get basic information for different things on the server
- Compare commands: compare different nations, towns and players with each other
- History commands: get historical information for players and towns
- Top commands: rank players, nations and towns by multiple different figures
- Notifications: get notified when someone enters your territory
- Poll commands: simple polls for your server 

## Commands

- /get
    - /get player - player info
    - /get town - town info
    - /get nation - nation info
    - /get world - world total info
    - /get culture - culture info
    - /get religion - religion info
    - /get raw - raw data for projects
- /compare
    - /compare towns - compare two towns
    - /compare nations - compare two nations
    - /compare players - compare two players
- /history
    - /history town bank - town bank over time
    - /history town residents - town resident count over time
    - /history town visitors - town visitor list w/ time
    - /history player visited_towns - players' visited towns w/ time
- /top
    - /top players activity - Rank players by activity
    - /top players visited_towns - Rank players by town visit count
    - /top nations residents - Rank nations by total resident count
    - /top nations area - Rank nations by claimed aerea
    - /top nations towns - Rank nations by town count
    - /top towns balance- Rank towns by bank
    - /top towns activity - Rank towns by activity
    - /top towns area - Rank towns by claimed area
    - /top towns residents - Rank towns by total residents
    - /top towns age - Rank towns by age in days
    - /top religions followers - Rank religions by follower count
    - /top religions towns - Rank religions by town count 
    - /top cultures residents - Rank cultures by total resident count
    - /top cultures towns - Rank cultures by total town count
- /notifications
    - /notifications enable - Enable notifications in a channel
    - /notifications disable - Disable notifications in a channel
    - /notifications config view - View configuration
    - /notifications config set - Set config flags
- /poll
    - /poll poll - Yes/no poll
    - /poll quesiton - Multi-choice poll
- /info
    - /info help - Help command, shows a command list
    - /info info - Bot info with some stats

# Installing and running

## Requirements

- Modules in requirements.txt
- Python 3.8+

## Set-up

- Create a file named `.env` with the following:
```
token="discord bot token"
webhook="a webhook to send to when the bot is added to a new server. if left blank will cause a non-fatal error when bot is added to server"
```
- Open setup.py
- Set refresh_commands to True
- Add your Discord ID to mods
- Ensure the bot profile has "server members intent" enabled on [discord developers](https://discord.com/developers)

## Running

- Run the `main.py` file to start the bot.
- After first run, make sure to set refresh_commands to False in `setup.py`

# Updating from Pre-v1.0.0

1. Stop the bot from running
2. Delete the cmds, cogs, dynmap and funcs direcoty
3. Install the cmds, cogs, dynmap and funcs directories from the new version
4. Replace main.py with the new main.py
5. Install task.py
6. Copy in new variables of setup.py
7. Rename server_data.pickle to old_data.pickle in rulercraft directory
8. Delete all files with "backup" in the name in the rulercraft directory
9. Ensure `MIGRATE_OLD_SAVEFILE` is set to True in setup.py
10. Update requirements.txt, install missing if required
10. Run the bot
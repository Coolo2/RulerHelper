import discord

mods = [368071242189897728, 521780643701456917] # comma seperated list of discord ids of people who you trust
mod_notification_channel = 985590035556479017 # A channel to send /request notifications in
slash_guilds = [discord.Object(985589916794765332)] # replace the number here with discord id for a dedicated server for the bot - mods only

refresh_commands = False

PRODUCTION_MODE = True # Enable this if you are not testing anything. Enables error handling

REFRESH_INTERVAL = 20 # How often to track server changes.
BACKUP_SAVEFILE = False
MIGRATE_OLD_SAVEFILE = True # Ensure there is a file in the rulercraft directory named 'old_data.pickle'
STATUS_EXTRA = "test" # Announcements etc to go in "watching" status can go here

MULTI_THREAD_MODE = True # Enable this to improve performance. Almost no memory increase, however causes some syncing issues (may be a few extra seconds of data delay)
DEBUG_MODE = True

IMAGE_DPI = 300 # Reduce this to improve performance. The quality of graphs, pie charts, maps, etc


embed = 0x2F3136
embedFail = 0xFF0000
embedSuccess = 0x32CD32
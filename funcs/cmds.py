

dict = {
    "get": {
        "online":[
            "Get currently online players and a graph showing the distribution of player locations"
        ],
        "player":[
            "Get information about a player",
            "[player]"
        ],
        "town":[
            "Get information about a town",
            "[town]"
        ],
        "nation":[
            "Get information about a nation",
            "[nation]"
        ],
        "world":[
            "Get an image of the town distribution on Earth and stats about the world"
        ],
        "raw":[
            "Get raw data files for the bot"
        ]
    },
    "history":{
        "town":{
            "bank":[
                "See the bank history of a town over time, including a graph",
                "[town]"
            ],
            "visitors":[
                "See people who have spent the most time in a town, along with a list of everyone who ever joined.",
                "[town]"
            ],
            "residents":[
                "A graph of the total resident count of a town over time.",
                "[town]"
            ]
        },
        "player":{
            "visited_towns":[
                "Get a list of the player's visited towns",
                "[player]"
            ]
        }
    },
    "top":{
        "towns":{
            "activity":[
                "Rank top towns by the total online time of players in its borders",
                "*[highlight_town]"
            ],
            "residents":[
                "Rank top towns by the total resident count",
                "*[highlight_town]"
            ],
            "area":[
                "Rank top towns by the total claimed area",
                "*[highlight_town]"
            ],
            "balance":[
                "Rank towns by the total bank balance",
                "*[highlight_town]"
            ],
            "age":[
                "Rank towns by age in days",
                "*[highlight_town]"
            ]
        },
        "nations":{
            "residents":[
                "Rank top nations by total resident count",
                "*[highlight_nation]"
            ],
            "area":[
                "Rank top nations by total claimed area",
                "*[highlight_nation]"
            ],
            "towns":[
                "Rank top nations by total town count",
                "*[highlight_nation]"
            ],
        },
        "players":{
            "activity":[
                "Rank top players by total online time on Earth since tracking started",
                "*[highlight_player]"
            ],
            "visited_towns":[
                "Rank top players by total visited town count",
                "*[highlight_player]"
            ],
        }
    },
    "compare":{
        "towns":[
            "Compare two towns' statistics",
            "[first_town] [second_town]"
        ],
        "nations":[
            "Compare two nationss' statistics",
            "[first_nation] [second_nation]"
        ],
        "players":[
            "Compare two players' statistics",
            "[first_player] [second_player]"
        ]
    },
    "notifications":{
        "enable":[
            "Enable notifications in a certain channel",
            "[notification_type] [channel] [nation]"
        ],
        "disable":[
            "Disable notifications in a certain channel",
            "[channel]"
        ],
        "config view":[
            "View config for a channel",
            "[channel]"
        ],
        "config set":[
            "Set a configuration value in a channel",
            "[channel] nation={nation} enable_setting={setting} disable_setting={setting}"
        ]
    },
    "poll":{
        "question":[
            "A multiple choice poll. Good for elections.",
            "[quesiton] [arg1-10...]"
        ],
        "poll":[
            "A simple yes or no poll showing percentage stats on reactions",
            "[question]"
        ]
    },
    "request":{
        "likely_residency_change":[
            "Request for the likely residency on **/get player** to be changed for a player (your own name, or another if it's valid) by Bot Moderators. Using argument 'None' reverts to automatic detection",
            "[player] [town]"
        ],
        "discord_link":[
            "Request for your Discord account to be linked to your **/get player** profile by Bot Moderators. There is some automatic detection however linking it is a more secure way. Allows people to search for you from your Minecraft name.",
            "[minecraft_name]"
        ]
    },
    "info":{
        "help":[
            "This command."
        ],
        "info":[
            "Basic info and stats about the bot"
        ]
    }
}
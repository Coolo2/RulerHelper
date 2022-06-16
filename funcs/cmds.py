

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
            "total_residents":[
                "A graph of the total resident count of a town over time.",
                "[town]"
            ]
        }
    },
    "top":{
        "towns":{
            "activity":[
                "Rank top towns by the total online time of players in its borders",
                "*[highlight_town]"
            ],
            "total_residents":[
                "Rank top towns by the total resident count",
                "*[highlight_town]"
            ],
            "area":[
                "Rank top towns by the total claimed area",
                "*[highlight_town]"
            ]
        },
        "nations":{
            "total_residents":[
                "Rank top nations by total resident count",
                "*[highlight_nation]"
            ],
        },
        "players":{
            "activity":[
                "Rank top players by total online time on Earth since tracking started",
                "*[highlight_player]"
            ],
        }
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
    "info":{
        "help":[
            "This command."
        ],
        "info":[
            "Basic info and stats about the bot"
        ]
    }
}
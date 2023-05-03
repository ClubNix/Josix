

<h1 align="center">
  <img src="https://cdn.discordapp.com/attachments/933118079028826145/951590071948177488/josix.png" alt="icon_josix"  height="200" width="200">
  <br>
  Josix by Club*Nix
  <br>
</h1>

<p align="center">
  <a href="https://www.clubnix.fr/" alt="Club*Nix"><img src="https://img.shields.io/badge/A_project-Club*Nix-informational"/></a>
  <a href="https://github.com/ClubNix/Josix/blob/master/LICENSE" alt="apache"><img src="https://img.shields.io/badge/Apache-2.0-green" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue" alt="python"/>
</p>

# What is Josix

Josix is a discord bot written with [py-cord](https://pypi.org/project/py-cord/). Mostly for fun its goal is at first just general purpose for the server of the Club\*Nix (join [here](https://discord.gg/PX7ceVqQkj)) like :
- ⚙️ Reaction role 
- 💾 Postgre database backup
- 🎂 Birthday reminder
- 📈 XP System
- 💰 Commands to use our food system API, [Monix](https://github.com/ClubNix/monix-2.0)
- 🎮 Board games such as : tic-tac-toe, othello, connect-4 and more
- 🧠 Private jokes register
- 😂 Joke generator
- 🛠️ Server management
- 🔓 Log system (basic log + error log) with custom display with error formating


# Install and lauch 
- Clone the repository :
  - `git clone git@github.com:ClubNix/Josix.git`
  - `cd Josix`

- Get all the required packages :
`pip install -r requirements.txt`

- Add your informations :
	- Create a `.env` file with these informations :
```
discord = your_discord_bot_token_here
jokes = Blagues_API_token_here
db_name = your_database_name
db_user = user_for_bot_in_database
db_pwd = password_for_your_bot
host = address_of_the_database
monix_log = username_for_monix (only for us)
monix_psswd = password_for_monix (only for us)
home = your_home_directory
logs = log_repository_in_your_home
```

> The "blagues_api" token is not required to launch the bot, it's for the `joke` command (french jokes only). <br>
> The home, logs, log/error_file fields are here to get logs and get nothing in your terminal <br>
> No need to give monix_log and monix_psswd

- Edit the `config.json` file to give your informations.
  - The `links` field is here to give a list of your personal links (or whatever you want), it will work as an hypertext.
  - The `tags` field is here to automatically create "open" and "close" tags for the forum channel. **DO NOT** edit the names `open` and `close`, just edit their content. 

- Add your own private jokes :
	- Create a file `askip.json` (if you want to change the name you have to change it in the `fun.py` file)
	- Fill it with your private jokes like this :

```json
{
	"category or one's name" : {
		"joke's name" : "fill with your private joke",
		"another" : "another joke",
		"..." : "..."
	},

	"..." : {
		"joke" : "..."
	}
}
```

- Run the bot :
`python3 josix.py`


## Warning
You can get an error on installing psycopg2, enter the following commands :
- pip3 install psycopg2-binary
- sudo apt install libpq-dev python3-dev

And then you can retry to install psycopg2
<br>
Disable the monix extension by deleting `cogs/monix.py` or by renaming the python file with an `_` before it like this : `_monix.py`.

## License
Josix is under the [Apache 2-0 license](https://github.com/ClubNix/Josix/blob/master/LICENSE)

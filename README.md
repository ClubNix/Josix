

<h1 align="center">
  <img src="https://cdn.discordapp.com/attachments/933118079028826145/951590071948177488/josix.png" alt="icon_josix"  height="200" width="200">
  <br>
  Josix by Club*Nix
  <br>
</h1>

<p align="center">
  <a href="https://www.clubnix.fr/" alt="Club*Nix"><img src="https://img.shields.io/badge/A_project-Club*Nix-informational"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue" alt="python"/>
</p>

# What is Josix

Josix is a discord bot written with [py-cord](https://pypi.org/project/py-cord/). Mostly for fun its goal is at first just general purpose for the server of the Club\*Nix (join [here](https://discord.gg/PX7ceVqQkj)) like :
- 👋 Custom welcome message
- ⚙️ Reaction role
- 📖 Logger
- 💾 Postgre database backup
- 🎂 Birthday reminder
- 📈 XP System
- 💰 Commands to use our food system API, [Monix](https://github.com/ClubNix/monix-2.0)
- 🎮 Board games such as : tic-tac-toe, othello, connect-4 and more
- 🧠 Private jokes register
- 😂 Joke generator
- 🔓 Log system (basic log + error log) with custom display with error formating


# Install and lauch 
- Clone the repository :
  - `git clone git@github.com:ClubNix/Josix.git`
  - `cd Josix`

- Get all the required packages :
  - `pip install -r requirements.txt`

- Add your informations :
	- Create a `.env` file for the `docker-compose.yml` with these informations (default values given):
```
JOSIX_IP=bot_ip (192.168.1.2)
ADMINER_IP=adminer_ip (192.168.1.3)
DB_IP=database_ip (192.168.1.4)
DRIVER=bridge
PARENT=ens18
SUBNET=subnet_of_services (192.168.1.0/24)
GATEWAY=gateway_of_subnet (192.168.1.1)
```

  - Create a `.env.db` for all the secret informations about the database :

```
POSTGRES_USER=root
POSTGRES_PASSWORD=root
POSTGRES_DB=your_db
PG_USER=root
```

  - Create a `.env.dev` file for all the secret informations for the bot :

```
DISCORD=discord_bot_token
JOKES=blagues_api_token
DB_NAME=database_name
DB_USER=database_user
DB_PASSWORD=database_user
HOST=database_host
MONIX_LOG=bot_monix_username (only for us)
MONIX_PASSWORD=bot_monix_password (only for us)
HOME=home_directory (./)
LOGS=logs_directory (logs/)
```

> The `JOKES` field for `blagues_api` token is not required to launch the bot. It's used for the `joke` command (french jokes only). <br>
> The `HOME` and `LOGS` fields are here to get logs and get nothing in your terminal <br>
> No need to give `MONIX_LOG` and `MONIX_PASSWORD`, they are meant to be used only by Club\*Nix.

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

- Add some inserts in `initialization-scripts/3-data-josix.sql` to have auto-insert when creating the volumes.

- Check `docker-compose.yml` to be sure that the volumes are well-linked.

- Run the bot :
  - `sudo docker-compose build` Build the bot (if the code have been modified).
  - `sudo docker-compose up` Launch the whole project.

  - Access to the adminer page to manage your database at `adminer_ip:8080`. Then log with :
    - PostgreSQL
    - db (by default)
    - postgres_user
    - user_password
    - postgres_db


## Warning
If you are launching the bot without docker, you can get an error on installing psycopg2 with `pip3 install -r requirements.txt`, enter the following commands :
- `pip3 install psycopg2-binary`
- `sudo apt install libpq-dev python3-dev`

And then you can retry to install psycopg2
<br>
Disable the monix extension by deleting `cogs/monix.py` or by renaming the python file with an `_` before it like this : `_monix.py`.<br>

All the commands of the extension [owner](cogs/owner.py) can be executed by the administrators of the server.
It has been made like this because our organization has a special case but it can leads to security issues with your bot if you use it cross-server.
To avoid this, make sure to edit the `cog_check` method in the `owner.py` file. <br>
e.g. remove `or ctx.author.guild_permissions.administrator` if you want the commands to be executed only by the bot's owner. Also, the same thing applies
for displaying the owner commands with the `help` command. Change the condition, according to your will.

## License
Josix is under the [Apache 2-0 license](https://github.com/ClubNix/Josix/blob/master/LICENSE)

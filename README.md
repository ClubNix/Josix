

<h1 align="center">
  <img src="https://cdn.discordapp.com/attachments/693166692838408333/708425236730609704/1569691438417.png" alt="icon_josix"  height="200" width="200">
  <br>
  Josix by Club*Nix
  <br>
  </h1>
  
<p align="center">
  <a href="https://www.clubnix.fr/" alt="Club*Nix"><img src="https://img.shields.io/badge/A_project-Club*Nix-informational"/></a>
  <a href="https://github.com/ClubNix/Josix/blob/master/LICENSE" alt="apache"><img src="https://img.shields.io/badge/Apache-2.0-green" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8_|_3.9_|_3.10-blue" alt="python"/>
</p>

# What is Josix

Josix is a discord bot written with Pycord in Python. Mostly for fun its goal is doing stats for the server and giving many options to help the users :
- Reaction role 
- private jokes register
- etc...

# Install and lauch 
- Clone the repository :
`git clone git@github.com:ClubNix/Josix.git`
`cd Josix`

- Get all the required packages :
`pip install -r requirements.txt`

- Add your informations :
	- Create a `.env` file with these informations :
```
discord = your_discord_bot_token_here
jokes = Blagues_API_token_here
```
> note : the "blagues_api" token is not required to launch the bot, it's for the `joke` command (french jokes only).
- Run the bot :
`python3 josix.py`

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

## Documentation
...

## License
Josix is under the [Apache 2-0 license](https://github.com/ClubNix/Josix/blob/master/LICENSE)
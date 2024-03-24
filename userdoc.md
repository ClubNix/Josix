# User doc for Josix

This documentation will show and explains all the user functionalities of this discord bot.

The bot is made to be used cross-server but some functionalities are not made for this.
- The askip system reunite everything together, so datas for all the servers are gathered together
- The Monix extension is only usable in our discord server / network. You must disable it.

For the simple install + launch part, you can check the README file.

# Table of contents
- [User doc for Josix](#user-doc-for-josix)
- [Table of contents](#table-of-contents)
  - [Owner](#owner)
  - [Admin](#admin)
  - [XP system](#xp-system)
  - [Reaction role](#reaction-role)
  - [Useful](#useful)
  - [Monix](#monix)
  - [Fun](#fun)
  - [Games](#games)
    - [Pattern](#pattern)
    - [Connect4](#connect4)
    - [TicTacToe](#tictactoe)
    - [Othello](#othello)

## Owner
The owner extension purpose is to provide to the bot owner some useful commands.

These commands should not be ran by people you don't trust, so keep in mind you must modify the conditions as described in the README.

Here is a list of the commands : 
- `stop_josix` Stop the bot. Running this command will simply completely stop the bot and will need to restart it manually.

- `create_backup` Creates a backup of the database in a `backup.sql` file.
  - `table` parameter : Specify if you want to backup a single table (without specification it runs on all the tables)

- `execute` Execute a SQL query from discord. Useful if you need to perfom a simple select, update, etc... and you are too lazy to log in your database
  - `query` The query string that will be executed.

- `execute_backup` Execute the backup file automatically (NOTE : because the backup file is just formated **INSERT** so it may cause conflicts)

- `display_logs` / `display_errors` Displays the last lines of the **log** or **error** file on discord.
  - `count` The number of lines to display (default : 100

- (**TASK**) `daily_backup` A task running each 24 hours that creates a backup in the `daily_backup.sql` file

## Admin
All the following commands are made to be run by discord servers staff to handle moderation functionalities of the bot
- `clear` Clears message from the channel
  - `limit` The limit of messages to delete must be between 1 and 50 (default 10)

- `add_couple` Add a reaction-role couple to a message. When a member add/remove this reaction on the message he will be added/removed the role.
  - `msg_id` The ID of the message
  - `emoji` The emoji of the reaction (must not already used in the message and not be a custom emoji)
  - `role` The role to give/remove (must not already used in the message)

- `delete_couple` Take the same parameter as the previous command but it deletes the given couple from the message (Reacting with the emoji will no longer give/remove the role).

- `set_news_channel` Set the current channel so it will receive all the news from the bot (for now it just apply for birthdays reminder)

- `set_xp_channel` Set the current channel so it will receive all the announce for xp from the bot (Mentions when you pass a level if the XP is enabled)

- `enable_xp_system` Enable or disable the XP system on this server. If the system is disabled, no one will receive any XP.

- `create_new_season` Store the current season results (all scores and ranking) and switch to a new season
  - `label` The label for the season that will be stored

- `delete_season` Delete a season from the history
  - `label` The label of the season that must be deleted

- `update_season` Update a season's label
  - `old_label` The label of the targeted season
  - `new_label` The new label for the targeted season

- `set_custom_welcome` Set up the custom welcome for the server
  - `channel` The channel that will display the welcome message
  - `role` The role to give automatically when someone enters the server
  - `message` The message to display when someone enters the server (there's a default message). You have 3 possible variables in the message :
    - **{user}** : Will be replaced by the mention of the user
    - **{server}** : Will be replaced by the server's name
    - **{ln}** : Will be replaced by a line-break
  - `keep` A boolean to clarify if you want to keep old values if they are not set in the command (If you don't specify a role and put `keep` to False, it will be deleted in the database)

- `enable_welcome` Enable or disable the welcome message for this server

- `set_logger` Set-up the custom logger for this server by choosing which logs to display
  - `keep` A boolean so clarify if you want to keep old selected logs if they are not selected in the command

- `set_log_channel` Set a channel as the logs displayer. It will display all the choosen logs in the previous command
  - `channel` The targeted channel

- `block_category` Block (or unblock) a category to prevent people for getting xp here
  - `category` The category to block or unblock


## XP system
The XP system is based on the [MEE6 documentation](https://github.com/Mee6/Mee6-documentation/blob/master/docs/levels_xp.md)

You can only earn xp each 60 seconds, meaning that after a gain you need to wait 60 seconds for your actions to pay off again.

You can earn xp by :
- Sending a message, the xp obtained will depend of the length of the message
  - **75** if it's longer or equal to 100 characters
  - **50** if it's between 99 and 30 characters (include)
  - **25** else
- Using a Josix's command : **25 xp** (Warning : All the commands does not grant xp)
- Adding a reaction to message : **25 xp**

![MEE6_need_up](https://github.com/Mee6/Mee6-documentation/raw/master/docs/pics/xp_level_up.png)

![MEE6_need_total](https://github.com/Mee6/Mee6-documentation/raw/master/docs/pics/total_xp_level.png)

Commands : 
- (**STAFF**) `give_xp` Gives a specific amount of xp to a user and updates its level in comparison to the amount.
  - `member` The target member that will receive the xp
  - `amount` The amount of xp to give ( >= 1 ). If it's superior to the XP limit, the user's experience will be set to this limit.

- (**STAFF**) `remove_xp` Same as `give_xp` command but removes xp to the user.

- (**STAFF**) `give_levels` / `remove_levels` Gives or removes a specific amount of levels and updates the user's experience to the starting point of the leverl.
  - `member` The target member.
  - `amount` The amount of levels to give or remove ( >= 1 ).

- `leaderboard` Display the server's leaderboard based on the user's amount of experience.
  - `limit` The limit of users to display (default 10)

- `profile` Show the profile card of a user with its current level, xp and progress towards the next level
  - `member` The member's card to display (default the user who called the command)

- (**STAFF**) `block_user_xp` Block (or unblock) user from earning xp in your server
  - `member` The member you want to block or unblock

- `show_seasons` Show the seasons historical of the server
  - `limit` The limit of season to display (1 <= limit <= 25)

- `user_history` Show the history of the user in this server for all seasons he participated
  - `member` Mention of the member you want to see the history (default yourself)

- `info_season` See the information of a season
  - `label` The label of the targeted season

- `user_season_profile` See your profile for a given season
  - `label` The label of the targeted season

## Reaction role
The reaction role helps a discord server staff to automatically gives role to their users.

You can create a couple (see the Admin part) of **role x emoji**. Josix does not support custom emoji.

After adding this couple if the message had 0 couples before it will be automatically set as a reaction-role message. Then, if a user add a reaction he will get the corresponding role and if he removes the reaction he will loose the role.


**Note** : if you delete a role, all the couples associated with that role will be removed. 

## Useful
This extension is created for all the commands and functionalities that are useful for users.
The bot will also add a `Open` or `Close` tag to forum's thread when they are opened or locked with the `close` command.

- `help` Shows all the commands or a specific command help guide. The commands are sorted by category. In the default operation, the `owner` commands are not displayed if the user does not match with the check.
  - `command_name` The name of the command for the command help guide. By default it's set to None, if not set the command will displays all the commands.

- `links` Displays a list of links (as hypertext) that can be set in the `config.json` file. Name of the variable -> text shown, value -> link

- `choose` Choose a sentence between all the given sentences. Each different part must be separated from the others by a `;` !
  - `sentences` The message containing all the sentences. Max length of the whole message is 512 characters

- `close` Automatically close the thread if it's in a Forum Channel. Can only be done if the user is the thread author if it has the `manage threads` permission.
  - `lock` To specify if the thread should be locked or not. It's a staff only parameter

- `print_price` Prints the required price of a 3D print.
  - `cura_price` The price given by **Cura**.
  - `minutes_count` The number of minutes needed to perform the whole print, must be rounded to the superior.
  - `is_member` If the user asking for the print is a member or not.
![Function](https://cdn.discordapp.com/attachments/751051007110283365/987326536837373992/Screenshot_from_2022-06-17_14-02-05.png)


- `create_poll` Create a custom poll on discord with a title (optional) and a text

- `add_birthday` Add your birthday to the database so the bot can wish you a **happy birthday** !
  - `day` The day of your birthday (1-31)
  - `month` The month of your birthday (1-12)
  - `user` Which user's birthday it is. Can only be used by a staff member. To add your own birthday you don't need to specifiy this parameter.


- `remove_birthday` Remove the birthday of given member from the bot's database
  - `member` The target member. You need **moderate_members** permissions to delete another member birthday !


- `birthdays` Shows all the birthdays registered for the users in this server.
  - `month` Specify this parameter if you want to see the birthdays for a specific month.



- `user_birthday` See the birthday of a user
  - `user` The user's whose you want to see the birthday



- (**TASK**) `checkBirthday` A task that runs every 6 hours and that check if there's any birthdays to wish in every server.

## Monix
This extension is made to only be used by our organization. You must disable it (follow the README).

- `check_stocks` Check if we need to go shopping. If the number of stocks is lower than 50 then a warning embed is created.
  - `get_stocks` Specify if you want to get an output of all the stocks in a txt file. It's a **staff** only parameter

- `monix_leaderboard` Display a leaderboard of the Top 5 and Bottom 5 users or products based on how much coins they have or the quantity of the product.
  - `value_type` Which value's leaderboard to display. It can be users or products.

- `products_ranking` Rank all the products from the most consumed to the less consumed during the last 7 days.

- `members_ranking` Rank all the users from the biggest consumer to the smallest consumer during the last 7 days.

## Fun
All the commands of this extension are meant to be fun. Yeah that's basically the dump part of the bot

- `hello` Kindly answers with a "Hello"

- `ping` Ping the bot and gets it's latency with a cool gif.

- `say` The bot repeats the given sentence and delete the call to the command
  - `text` The text to repeat (must be at max 512 characters long)

- `joke` Sends a random joke from [BlaguesAPI](https://www.blagues-api.fr/). **Warning** : The jokes are in french only and you need a token to use this command
  - `joke_type` The type of joke you want (if not specified the joke is completely random)

- `list_askip` List all the askip categories registered by the bot
  - `username` If specified, the bot will instead list all the askips registered in this category.

- `askip` Sends an askip (can be random or not)
  - `username` If specified the bot will randomly choose an askip from this user (category) only
  - `askip_name` If specified the bot will choose this askip (the `username` parameter must be set and contain this askip)

- `add_askip` Add an askip to the bot. A vot will be created, if someone disagress or less than 2 members agrees (with a 3 minute voting time) the askip is not added
  - `username` The username (category name) of the askip (64 chars max)
  - `askip_name` The name of the askip (64 chars max)
  - `askip_text` The text of the askip (512 chars max)

- `avatar` Displays the avatar of a user
  - `user` If specified displays the given user's avatar. Else displays the command author's avatar.

## Games
The extension that contains all the commands for games. Currently there is 4 games available. Each can be launched by a command with their name, you can't enter 2 games at the same moment.

- `quit_game` Quit your current game. Useful if you are stuck in a game.

### Pattern
A game where you need to turn all the tiles in blue. When clicking a tile, this one and the ones direclty connected to it (excluding diagonals) are switched.

- `pattern_game` Launch the game

### Connect4
- `connect4` Launch the game
  - `opponent` Your opponent in the game

### TicTacToe
- `tic_tac_toe` Launch the game
  - `opponent` Your opponent in the game

### Othello
- `othello` Launch the game
  - `opponent` Your opponent in the game

- `othello rules` Displays the rules for the game Othello
/*
DROP TABLE IF EXISTS josix.MsgCouple;
DROP TABLE IF EXISTS josix.LogSelector;
DROP TABLE IF EXISTS josix.UserGuild;
DROP TABLE IF EXISTS josix.ReactCouple;
DROP TABLE IF EXISTS josix.MsgReact;
DROP TABLE IF EXISTS josix.DartLog;
DROP TABLE IF EXISTS josix.Logs;
DROP TABLE IF EXISTS josix.Games;
DROP TABLE IF EXISTS josix.GameType;
DROP TABLE IF EXISTS josix.Guild;
DROP TABLE IF EXISTS josix.User;
*/

--

CREATE TABLE IF NOT EXISTS josix.User (
    idUser BIGINT,
    elo INT DEFAULT 1000,
    nbGames INT DEFAULT 0,
    hbDate DATE, 
    PRIMARY KEY(idUser)
);

CREATE TABLE IF NOT EXISTS josix.Guild (
    idGuild BIGINT,
    chanNews BIGINT,
    xpNews BIGINT,
    enableXP BOOLEAN DEFAULT TRUE,
    enableWelcome BOOLEAN DEFAULT FALSE,
    welcomeChan BIGINT,
    welcomeRole BIGINT,
    welcomeText VARCHAR(512),
    logNews BIGINT,
    blockedCategories BIGINT ARRAY DEFAULT ARRAY[]::Integer[],
    PRIMARY KEY(idGuild)
);

CREATE TABLE IF NOT EXISTS josix.GameType (
    idType SERIAL,
    gameName VARCHAR(64),
    PRIMARY KEY(idtype)
);

CREATE TABLE IF NOT EXISTS josix.Logs (
    idLog INT NOT NULL,
    logName VARCHAR(64) NOT NULL,
    PRIMARY KEY(idLog)
);

CREATE TABLE IF NOT EXISTS josix.DartLog (
    idLog SERIAL,
    idGuild BIGINT NOT NULL,
    winnerName VARCHAR(64),
    losersName VARCHAR(64) ARRAY,
    PRIMARY KEY(idLog),
    CONSTRAINT fk_guild_log_id FOREIGN KEY(idGuild) REFERENCES josix.Guild(idGuild)
);

CREATE TABLE IF NOT EXISTS josix.MsgReact (
    idMsg BIGINT NOT NULL,
    idGuild BIGINT NOT NULL,
    PRIMARY KEY(idMsg),
    CONSTRAINT fk_guild_msgR_id FOREIGN KEY(idGuild) REFERENCES josix.Guild(idGuild)
);

CREATE TABLE IF NOT EXISTS josix.ReactCouple (
    idCouple SERIAL,
    nomEmoji VARCHAR(64) NOT NULL,
    idRole BIGINT NOT NULL,
    PRIMARY KEY(idCouple)
);

CREATE TABLE IF NOT EXISTS josix.Games (
    idGame SERIAL,
    idType INT NOT NULL,
    idUser BIGINT NOT NULL,
    opponent BIGINT,
    PRIMARY KEY(idGame),
    CONSTRAINT fk_type_games_id FOREIGN KEY(idType) REFERENCES josix.GameType(idType),
    CONSTRAINT fk_user_games_id FOREIGN KEY(idUser) REFERENCES josix.User(idUser)
);

CREATE TABLE IF NOT EXISTS josix.Season (
    idSeason SERIAL,
    idGuild BIGINT NOT NULL,
    label VARCHAR(32) DEFAULT '',
    ended_at DATETIME DEFAULT NOW(),
    PRIMARY KEY(idSeason),
    CONSTRAINT fk_guild_season_id FOREIGN KEY(idGuild) REFERENCES josix.Guild(idGuild)
);

--
--  
--


CREATE TABLE IF NOT EXISTS josix.UserGuild (
    idUser BIGINT NOT NULL,
    idGuild BIGINT NOT NULL,
    xp INT DEFAULT 0,
    lvl INT DEFAULT 0,
    lastMessage TIMESTAMP DEFAULT NOW(),
    xpBlocked BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(idUser, idGuild),
    CONSTRAINT fk_user_ug_id FOREIGN KEY(idUser) REFERENCES josix.User(idUser),
    CONSTRAINT fk_guild_ug_id FOREIGN KEY(idGuild) REFERENCES josix.Guild(idGuild)
);

CREATE TABLE IF NOT EXISTS josix.MsgCouple (
    idMsg BIGINT NOT NULL,
    idCouple BIGINT NOT NULL,
    PRIMARY KEY(idMsg, idCouple),
    CONSTRAINT fk_msg_mc_id FOREIGN KEY(idMsg) REFERENCES josix.MsgReact(idMsg),
    CONSTRAINT fk_couple_mc_id FOREIGN KEY(idCouple) REFERENCES josix.ReactCouple(idCouple)
);

CREATE TABLE IF NOT EXISTS josix.LogSelector (
    idGuild BIGINT NOT NULL,
    idLog BIGINT NOT NULL,
    PRIMARY KEY(idGuild, idLog),
    CONSTRAINT fk_guild_ls_id FOREIGN KEY(idGuild) REFERENCES josix.Guild(idGuild),
    CONSTRAINT fk_log_ls_id FOREIGN KEY(idLog) REFERENCES josix.Logs(idLog)
);

CREATE TABLE IF NOT EXISTS josix.Score (
    idUser BIGINT NOT NULL,
    idSeason BIGINT NOT NULL,
    score INT DEFAULT 0,
    ranking INT,
    PRIMARY KEY(idUser, idSeason),
    CONSTRAINT fk_user_score_id FOREIGN KEY(idUser) REFERENCES josix.User(idUser),
    CONSTRAINT fk_season_score_id FOREIGN KEY(idSeason) REFERENCES josix.Season(idSeason)
);
CREATE TABLE User
(
    idUser BIGINT NOT NULL,
    yearDate SMALLINT,
    joinVoc DATETIME,
    PRIMARY KEY(idUser)
);

CREATE TABLE Guild
(
    idGuild BIGINT NOT NULL,
    newMembers SMALLINT DEFAULT 0,
    lostMembers SMALLINT DEFAULT 0,
    totalMembers SMALLINT DEFAULT 0,
    sendStatus CHAR(1) DEFAULT "0",
    lastSend DATE,
    chanStatID BIGINT,
    keyWord VARCHAR(26) DEFAULT "",
    nbKeyWord INTEGER DEFAULT 0,
    autoAdd CHAR(1) DEFAULT "1",
    autoRefresh CHAR(1) DEFAULT "1",
    PRIMARY KEY(idGuild)
);

CREATE TABLE Channel
(
    idChannel BIGINT NOT NULL,
    idGuild BIGINT NOT NULL,
    numberMsg INT DEFAULT 0,
    PRIMARY KEY(idChannel),
    CONSTRAINT fk_guild_channel_id FOREIGN KEY(idGuild) REFERENCES Guild(idGuild)
);

CREATE TABLE Reaction
(
    idReact BIGINT NOT NULL,
    idGuild BIGINT NOT NULL,
    numberReact SMALLINT DEFAULT 0,
    nameReact VARCHAR(30) NOT NULL,
    PRIMARY KEY(idReact),
    CONSTRAINT fk_guild_react_id FOREIGN KEY(idGuild) REFERENCES Guild(idGuild)
);

CREATE TABLE BelongG
(
	idUser BIGINT NOT NULL,
	idGuild BIGINT NOT NULL,
    numberMsg INT DEFAULT 0,
    nbSecond INT DEFAULT 0,
	CONSTRAINT fk_user_belongG_id FOREIGN KEY(idUser) REFERENCES User(idUser),
	CONSTRAINT fk_guild_belongG_id FOREIGN KEY(idGuild) REFERENCES Guild(idGuild)
);

CREATE TABLE BelongC
(
	idUser BIGINT NOT NULL,
	idChannel BIGINT NOT NULL,
    numberMsg INT DEFAULT 0,
	CONSTRAINT fk_user_belongC_id FOREIGN KEY(idUser) REFERENCES User(idUser),
	CONSTRAINT fk_channel_belongC_id FOREIGN KEY(idChannel) REFERENCES Channel(idChannel)
);

/*
CREATE TABLE ReactUser
(
    idUser BIGINT NOT NULL,
    idReact BIGINT NOT NULL,
    numberReact INT DEFAULT 0,
	CONSTRAINT fk_user_reactUser_id FOREIGN KEY(idUser) REFERENCES User(idUser),
	CONSTRAINT fk_react_reactUser_id FOREIGN KEY(idReact) REFERENCES Reaction(idReact)
);
*/
-- bans history and index --

CREATE TABLE IF NOT EXISTS bans
(
    userId         text,
    userName       text,
    minutes        real,
    dateTimeOfBan  text,
    reason         text,
    ipAddress      text,
    clientId       text,
    adminId        text,
    adminName      text
);

CREATE INDEX IF NOT EXISTS bans_by_userId_and_dateTimeOfBan
ON bans(userId, dateTimeOfBan);

-- user accent settings --

CREATE TABLE user_accent
(
    guild_id integer,
    user_id  integer,
    accent   text,

    UNIQUE (guild_id, user_id, accent)
);

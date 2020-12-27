-- persistent unbans queue --

CREATE TABLE IF NOT EXISTS unban_queue
(
    user_id text
);

CREATE TABLE IF NOT EXISTS job_unban_queue
(
    user_id text,
    job integer
);

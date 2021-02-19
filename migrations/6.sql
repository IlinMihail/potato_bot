-- add severity field to user accent --

ALTER TABLE user_accent
ADD severity integer DEFAULT 1;
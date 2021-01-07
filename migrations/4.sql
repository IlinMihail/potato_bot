-- add forced field to user accent --

ALTER TABLE user_accent
ADD forced bool DEFAULT false;
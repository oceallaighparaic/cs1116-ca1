DROP TABLE IF EXISTS users
;

CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    permission TEXT NOT NULL -- ONLY "USER" OR "ADMIN"
)
;

SELECT *
FROM users
;

UPDATE users
SET permission = "ADMIN"
WHERE username = "EurosAndCents"
;
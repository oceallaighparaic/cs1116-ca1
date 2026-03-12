PRAGMA foreign_keys = ON
;

DROP TABLE IF EXISTS orders
;
DROP TABLE IF EXISTS users
;
DROP TABLE IF EXISTS products
;
DROP TABLE IF EXISTS permissions
;

CREATE TABLE permissions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE
)
;
-- SEED
INSERT INTO permissions(name)
VALUES ('USER'), ('ADMIN')
;


CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR NOT NULL UNIQUE,
    password VARCHAR NOT NULL,
    permission INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (permission) REFERENCES permissions(id)
)
;
-- SEED
INSERT INTO users(username, password, permission)
VALUES (
    'ADMIN', 
    'scrypt:32768:8:1$v6YzVtdQ6HawdJfR$5ab41d01354b777aead5ed68ca5d9fc71db37cb32b724b85463901b85f85c568d23fc59ec08f1c8d9fae7eaf77fd1e93d0a1d1f1a586bd578cf7322d7565543f', 
    2
)
;

CREATE TABLE products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL UNIQUE,
    price DECIMAL NOT NULL,
    image VARCHAR DEFAULT NULL,
    description VARCHAR
)
;

CREATE TABLE orders(
    orderid INTEGER PRIMARY KEY AUTOINCREMENT,
    userid INTEGER NOT NULL,
    productid INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_at_purchase DECIMAL NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_DATE,
    address VARCHAR NOT NULL,
    notes VARCHAR,
    FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(productid) REFERENCES products(id) ON DELETE CASCADE
)
;
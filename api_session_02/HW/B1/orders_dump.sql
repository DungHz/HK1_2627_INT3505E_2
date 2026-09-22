PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;


CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT DEFAULT 'pending'
);

INSERT INTO orders (id, item_name, quantity, status) VALUES (1, 'Laptop Dell Inspiron', 1, 'pending');
INSERT INTO orders (id, item_name, quantity, status) VALUES (2, 'Dien thoai Samsung Galaxy', 2, 'completed');
INSERT INTO orders (id, item_name, quantity, status) VALUES (3, 'Tai nghe Sony WH-1000XM5', 1, 'pending');

DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('orders', 3);

COMMIT;
import sqlite3

connection = sqlite3.connect("data/jev01.sqlite3")
connection.row_factory = sqlite3.Row

row = connection.execute(
    "SELECT * FROM candidates ORDER BY id DESC LIMIT 1"
).fetchone()

print(dict(row))

connection.close()
import sqlite3

connection = sqlite3.connect("data/jev01.sqlite3")

tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print(tables)

connection.close()
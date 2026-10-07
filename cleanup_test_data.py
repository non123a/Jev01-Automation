import sqlite3

connection = sqlite3.connect("data/jev01.sqlite3")

connection.execute("DELETE FROM candidates")
connection.commit()

print("Synthetic candidate data removed.")

connection.close()
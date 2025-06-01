import sqlite3
DATABASE = 'kitbox.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Check for category column
cursor.execute("PRAGMA table_info(gear);")
columns = [info[1] for info in cursor.fetchall()]
print(f"Columns in gear table: {columns}")
if 'category' in columns:
    print("Category column exists in gear table.")
else:
    print("ERROR: Category column DOES NOT exist in gear table.")

# Count total gear items
cursor.execute("SELECT COUNT(*) FROM gear;")
count = cursor.fetchone()[0]
print(f"Total gear items: {count}")
if count == 12:
    print("Correct number of gear items (12) found.")
else:
    print(f"ERROR: Expected 12 gear items, but found {count}.")

# List distinct categories
cursor.execute("SELECT DISTINCT category FROM gear ORDER BY category;")
categories = [row[0] for row in cursor.fetchall()]
print(f"Distinct categories: {categories}")
expected_categories = sorted(['Adventuring Gear', 'Ammunition', 'Armor', 'Cyberware', 'Magical Gadget', 'Tech Armor', 'Tech Gear', 'Weapon'])
if categories == expected_categories:
    print("Distinct categories match expected.")
else:
    print(f"ERROR: Distinct categories do not match. Expected {expected_categories}, Got {categories}")


# Retrieve a new item
cursor.execute("SELECT * FROM gear WHERE name = 'Neural Interface Jack';")
new_item = cursor.fetchone()
print(f"Details for 'Neural Interface Jack': {new_item}")
# Column order: id, name, description, weight, cost, value, legality, category, location_id
if new_item and new_item[7] == 'Cyberware': # Category is at index 7
    print("'Neural Interface Jack' has correct category 'Cyberware'.")
else:
    print(f"ERROR: 'Neural Interface Jack' data incorrect or category mismatch. Data: {new_item}")


# Retrieve an old item
cursor.execute("SELECT * FROM gear WHERE name = 'Steel Helmet';")
old_item = cursor.fetchone()
print(f"Details for 'Steel Helmet': {old_item}")
# Column order: id, name, description, weight, cost, value, legality, category, location_id
if old_item and old_item[7] == 'Armor': # Category is at index 7
    print("'Steel Helmet' has correct category 'Armor'.")
else:
    print(f"ERROR: 'Steel Helmet' data incorrect or category mismatch. Data: {old_item}")

conn.close()

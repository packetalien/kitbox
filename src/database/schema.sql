-- src/database/schema.sql

PRAGMA foreign_keys = ON; -- Enforce foreign key constraints

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, -- Assuming location names like "Head" or "Backpack" are unique
    type TEXT NOT NULL CHECK(type IN ('Body Slot', 'Container', 'Generic')), -- Type of location
    parent_id INTEGER, -- For nested containers, e.g., a pouch in a backpack
    FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE SET NULL -- If parent is deleted, child becomes top-level or orphaned
);

CREATE TABLE IF NOT EXISTS gear (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    weight REAL NOT NULL DEFAULT 0.0,
    cost REAL,
    value REAL,
    legality TEXT,
    location_id INTEGER, -- Where the item is currently located
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL -- If location is deleted, item becomes unassigned
);

-- Initial Data for Locations (Body Slots & Common Containers)
-- Body Slots
INSERT INTO locations (name, type) VALUES ('Head', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Neck', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Shoulders', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Shoulder L', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Shoulder R', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Arms', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Arms L', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Arms R', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Hands', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Hand L', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Hand R', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Torso', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Waist', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Legs', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Foot L', 'Body Slot');
INSERT INTO locations (name, type) VALUES ('Foot R', 'Body Slot');
INSERT INTO locations (name,type) VALUES ('Feet', 'Body Slot');

-- Common Containers (these are also locations items can be in)
INSERT INTO locations (name, type) VALUES ('Backpack', 'Container');
INSERT INTO locations (name, type) VALUES ('Belt Pouch', 'Container');
INSERT INTO locations (name, type) VALUES ('Saddlebags', 'Container');
INSERT INTO locations (name, type) VALUES ('Generic Storage', 'Container'); -- A place for items not actively carried

-- Sample Gear (for testing, can be expanded or put in a separate seed file)
INSERT INTO gear (name, description, weight, cost, value, legality, location_id) VALUES 
('Steel Helmet', 'A sturdy helmet for combat', 2.0, 50.0, 45.0, 'Legal', (SELECT id from locations WHERE name = 'Head')),
('Leather Jerkin', 'Basic torso protection', 3.0, 20.0, 15.0, 'Legal', (SELECT id from locations WHERE name = 'Torso')),
('Dagger', 'A simple sidearm', 0.5, 5.0, 4.0, 'Legal', (SELECT id from locations WHERE name = 'Belt Pouch')),
('Rope (50ft)', 'Useful for climbing and other tasks', 5.0, 1.0, 1.0, 'Legal', (SELECT id from locations WHERE name = 'Backpack')),
('Rations (3 days)', 'Travel sustenance', 3.0, 1.5, 1.0, 'Legal', (SELECT id from locations WHERE name = 'Backpack'));

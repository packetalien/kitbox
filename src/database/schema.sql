-- src/database/schema.sql

PRAGMA foreign_keys = ON; -- Enforce foreign key constraints

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

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
    category TEXT, -- Added category column
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
INSERT INTO locations (name, type) VALUES ('Feet', 'Body Slot');

-- Common Containers (these are also locations items can be in)
INSERT INTO locations (name, type) VALUES ('Backpack', 'Container');
INSERT INTO locations (name, type) VALUES ('Belt Pouch', 'Container');
INSERT INTO locations (name, type) VALUES ('Saddlebags', 'Container');
INSERT INTO locations (name, type) VALUES ('Generic Storage', 'Container'); -- A place for items not actively carried

-- Sample Gear (for testing, can be expanded or put in a separate seed file)
INSERT INTO gear (name, description, weight, cost, value, legality, category, location_id) VALUES
('Steel Helmet', 'A sturdy helmet for combat', 2.0, 50.0, 45.0, 'Legal', 'Armor', (SELECT id from locations WHERE name = 'Head')),
('Leather Jerkin', 'Basic torso protection', 3.0, 20.0, 15.0, 'Legal', 'Armor', (SELECT id from locations WHERE name = 'Torso')),
('Dagger', 'A simple sidearm', 0.5, 5.0, 4.0, 'Legal', 'Weapon', (SELECT id from locations WHERE name = 'Belt Pouch')),
('Rope (50ft)', 'Useful for climbing and other tasks', 5.0, 1.0, 1.0, 'Legal', 'Adventuring Gear', (SELECT id from locations WHERE name = 'Backpack')),
('Rations (3 days)', 'Travel sustenance', 3.0, 1.5, 1.0, 'Legal', 'Adventuring Gear', (SELECT id from locations WHERE name = 'Backpack')),
-- Thematic Gear Additions
('Neural Interface Jack', 'Basic cranial data port for direct neural machine interface. Allows connection to compliant devices.', 0.1, 1200.0, 900.0, 'Restricted', 'Cyberware', (SELECT id from locations WHERE name = 'Generic Storage')),
('"Ghost" Infiltration Suit', 'Lightweight nano-weave suit with chameleonic properties, offering minor stealth benefits.', 1.5, 3500.0, 2800.0, 'Illegal', 'Tech Armor', (SELECT id from locations WHERE name = 'Generic Storage')),
('Mana-Tech Focus Wand', 'A wand that interweaves arcane energies with micro-circuitry to stabilize and slightly amplify simple offensive spells. Requires attunement.', 0.5, 800.0, 650.0, 'Legal', 'Magical Gadget', (SELECT id from locations WHERE name = 'Generic Storage')),
('"Street Doc" Med-Patch', 'Single-use advanced chemical patch that can stabilize critical wounds and provide temporary pain relief. Less effective than professional medical attention.', 0.05, 150.0, 100.0, 'Legal', 'Tech Gear', (SELECT id from locations WHERE name = 'Generic Storage')),
('Data Scrambler Optics', 'Retinal implants that project a subtle disruptive pattern, making facial recognition harder. Causes slight eye strain.', 0.02, 2000.0, 1500.0, 'Restricted', 'Cyberware', (SELECT id from locations WHERE name = 'Generic Storage')),
('"Brightburn" Chemical Rounds (10 pack)', 'Specialized ammunition for projectile weapons, containing a payload that ignites with an intense, disorienting flare on impact.', 0.2, 300.0, 200.0, 'Illegal', 'Ammunition', (SELECT id from locations WHERE name = 'Generic Storage')),
('Urban Survival Multi-tool', 'A ruggedized tool incorporating various technological and mundane implements useful for navigating and surviving in a dense, often hostile, urban environment. Includes a signal jammer detector.', 0.8, 450.0, 300.0, 'Legal', 'Tech Gear', (SELECT id from locations WHERE name = 'Generic Storage'));

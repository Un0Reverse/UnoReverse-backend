-- Schema bazei de date RRM USV: tabele de baza si indexuri.
-- Toate modulele (M1+) extind aceasta schema prin tabele proprii.

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student'
        CHECK (role IN ('student', 'researcher', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    schedule TEXT NOT NULL DEFAULT '08:00-20:00',
    stations_count INTEGER NOT NULL DEFAULT 16,
    status TEXT NOT NULL DEFAULT 'disponibila'
        CHECK (status IN ('disponibila', 'mentenanta'))
);

CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'disponibila'
        CHECK (status IN ('disponibila', 'mentenanta')),
    UNIQUE (room_id, label)
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    station_id INTEGER REFERENCES stations(id),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'activa'
        CHECK (status IN ('activa', 'anulata')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stations_room ON stations(room_id);
CREATE INDEX IF NOT EXISTS idx_bookings_room_time
    ON bookings(room_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_station_time
    ON bookings(station_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications(user_id, is_read);

-- Date initiale: 17 sali de cercetare USV.
INSERT OR IGNORE INTO rooms (id, name, schedule, stations_count, status) VALUES
    (1, 'Sala Cercetare C01', '08:00-20:00', 16, 'disponibila'),
    (2, 'Sala Cercetare C02', '08:00-20:00', 16, 'disponibila'),
    (3, 'Sala Cercetare C03', '08:00-20:00', 16, 'disponibila'),
    (4, 'Sala Cercetare C04', '08:00-20:00', 16, 'disponibila'),
    (5, 'Sala Cercetare C05', '09:00-18:00', 16, 'disponibila'),
    (6, 'Sala Cercetare C06', '08:00-20:00', 16, 'disponibila'),
    (7, 'Sala Cercetare C07', '08:00-20:00', 16, 'disponibila'),
    (8, 'Sala Cercetare C08', '08:00-20:00', 16, 'disponibila'),
    (9, 'Sala Cercetare C09', '08:00-20:00', 16, 'disponibila'),
    (10, 'Sala Cercetare C10', '09:00-18:00', 16, 'disponibila'),
    (11, 'Sala Cercetare C11', '08:00-20:00', 16, 'disponibila'),
    (12, 'Sala Cercetare C12', '08:00-20:00', 16, 'disponibila'),
    (13, 'Sala Cercetare C13', '08:00-20:00', 16, 'disponibila'),
    (14, 'Sala Cercetare C14', '08:00-20:00', 16, 'disponibila'),
    (15, 'Sala Cercetare C15', '09:00-18:00', 16, 'disponibila'),
    (16, 'Sala Cercetare C16', '08:00-20:00', 16, 'disponibila'),
    (17, 'Sala Cercetare C17', '08:00-20:00', 16, 'mentenanta');

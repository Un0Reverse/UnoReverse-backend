-- Date initiale: 17 sali x 16 statii = 272 statii, 6 categorii, 11 echipamente, useri demo

INSERT OR IGNORE INTO rooms (id, code, name, schedule, stations_count, status) VALUES
    (1,  'S01', 'C201 Laborator Electronică', '08:00-20:00', 16, 'disponibila'),
    (2,  'S02', 'C204 Robotică',              '08:00-20:00', 16, 'disponibila'),
    (3,  'S03', 'C207 Prototipare',           '08:00-20:00', 16, 'disponibila'),
    (4,  'S04', 'C210 Viziune & Senzori',     '08:00-20:00', 16, 'disponibila'),
    (5,  'S05', 'C212 Calcul GPU',            '09:00-18:00', 16, 'disponibila'),
    (6,  'S06', 'Sala C216',                  '08:00-20:00', 16, 'mentenanta'),
    (7,  'S07', 'Sala C217',                  '08:00-20:00', 16, 'disponibila'),
    (8,  'S08', 'Sala C218',                  '08:00-20:00', 16, 'disponibila'),
    (9,  'S09', 'Sala C219',                  '08:00-20:00', 16, 'disponibila'),
    (10, 'S10', 'Sala C220',                  '09:00-18:00', 16, 'disponibila'),
    (11, 'S11', 'Sala C221',                  '08:00-20:00', 16, 'disponibila'),
    (12, 'S12', 'Sala C222',                  '08:00-20:00', 16, 'disponibila'),
    (13, 'S13', 'Sala C223',                  '08:00-20:00', 16, 'disponibila'),
    (14, 'S14', 'Sala C224',                  '08:00-20:00', 16, 'disponibila'),
    (15, 'S15', 'Sala C225',                  '09:00-18:00', 16, 'disponibila'),
    (16, 'S16', 'Sala C226',                  '08:00-20:00', 16, 'disponibila'),
    (17, 'S17', 'Sala C227',                  '08:00-20:00', 16, 'disponibila');

-- Bucla SQL (CTE recursiv): genereaza automat cele 272 de statii (16 per sala)
WITH RECURSIVE nums(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM nums WHERE n < 16
)
INSERT OR IGNORE INTO stations (room_id, number, label, status)
SELECT r.id, nums.n, 'Stația ' || nums.n, r.status
FROM rooms r
CROSS JOIN nums;

INSERT OR IGNORE INTO categories (id, name) VALUES
    (1, 'Robotică'),
    (2, 'Aparate de măsură'),
    (3, 'Prototipare 3D'),
    (4, 'IoT / Senzori'),
    (5, 'Viziune computerizată'),
    (6, 'Calcul GPU / Cluster');

INSERT OR IGNORE INTO equipment (id, code, category_id, name, room_id, status) VALUES
    (1,  'EQ01', 1, 'Cobot Universal UR5',        2,    'disponibil'),
    (2,  'EQ02', 1, 'Robot mobil AGV (SLAM)',     NULL, 'disponibil'),
    (3,  'EQ03', 2, 'Osciloscop digital 1 GHz',   1,    'disponibil'),
    (4,  'EQ04', 2, 'Analizor spectru RF',        1,    'mentenanta'),
    (5,  'EQ05', 3, 'Imprimantă 3D FDM Prusa',    3,    'disponibil'),
    (6,  'EQ06', 3, 'Imprimantă 3D SLA (rășină)', 3,    'disponibil'),
    (7,  'EQ07', 4, 'Kit IoT + microcontrollere', NULL, 'disponibil'),
    (8,  'EQ08', 5, 'Cameră termografică FLIR',   4,    'disponibil'),
    (9,  'EQ09', 5, 'Cameră RGB-D LiDAR',         4,    'disponibil'),
    (10, 'EQ10', 6, 'Workstation GPU RTX',        5,    'ocupat'),
    (11, 'EQ11', 6, 'Nod cluster USV (coadă)',    NULL, 'disponibil');

INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('pending_expiry_hours', '48', 'Ore până la expirarea automată a cererilor neaprobate'),
    ('priority_order', 'cadru,student,admin', 'Ordinea priorităților la aprobare');
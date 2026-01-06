-- =============================================================================
-- BDOCS Prison Information System - Authentic Bahamian Seed Data
-- Her Majesty's Prison (Fox Hill), Nassau, The Bahamas
-- =============================================================================

-- Clear existing data
TRUNCATE clemency_petitions, clemency_status_history, sentence_adjustments,
         sentences, court_appearances, court_cases, movements,
         housing_assignments, classifications, inmates, housing_units CASCADE;

-- =============================================================================
-- HOUSING UNITS - Fox Hill Prison Layout
-- =============================================================================
INSERT INTO housing_units (id, code, name, security_level, capacity, current_occupancy, gender_restriction, is_juvenile, description) VALUES
-- Maximum Security
('a1000001-0001-4000-8000-000000000001', 'MAX-A', 'Maximum Security Block A', 'MAXIMUM', 48, 42, 'MALE', false, 'High-security unit for violent offenders and escape risks'),
('a1000001-0001-4000-8000-000000000002', 'MAX-B', 'Maximum Security Block B', 'MAXIMUM', 48, 45, 'MALE', false, 'Death row and life sentence inmates'),

-- Medium Security
('a1000001-0001-4000-8000-000000000003', 'MED-A', 'Medium Security Block A', 'MEDIUM', 80, 72, 'MALE', false, 'General population - medium risk'),
('a1000001-0001-4000-8000-000000000004', 'MED-B', 'Medium Security Block B', 'MEDIUM', 80, 68, 'MALE', false, 'Work program eligible inmates'),
('a1000001-0001-4000-8000-000000000005', 'MED-F', 'Female Medium Security', 'MEDIUM', 40, 28, 'FEMALE', false, 'Female inmates - medium security'),

-- Minimum Security
('a1000001-0001-4000-8000-000000000006', 'MIN-A', 'Minimum Security Block A', 'MINIMUM', 60, 45, 'MALE', false, 'Pre-release and low-risk inmates'),
('a1000001-0001-4000-8000-000000000007', 'MIN-F', 'Female Minimum Security', 'MINIMUM', 24, 12, 'FEMALE', false, 'Female inmates - minimum security'),

-- Remand
('a1000001-0001-4000-8000-000000000008', 'REM-A', 'Remand Block A', 'MEDIUM', 100, 89, 'MALE', false, 'Male remand prisoners awaiting trial'),
('a1000001-0001-4000-8000-000000000009', 'REM-B', 'Remand Block B', 'MEDIUM', 100, 95, 'MALE', false, 'Male remand overflow'),
('a1000001-0001-4000-8000-000000000010', 'REM-F', 'Female Remand', 'MEDIUM', 30, 18, 'FEMALE', false, 'Female remand prisoners'),

-- Special Units
('a1000001-0001-4000-8000-000000000011', 'MED-J', 'Simpson Penn Centre', 'MEDIUM', 50, 32, 'MALE', true, 'Juvenile male offenders - rehabilitation focus'),
('a1000001-0001-4000-8000-000000000012', 'ISO-1', 'Isolation Unit', 'MAXIMUM', 20, 8, NULL, false, 'Administrative segregation and protective custody');

-- =============================================================================
-- INMATES - Authentic Bahamian Names and Details
-- =============================================================================
INSERT INTO inmates (id, booking_number, nib_number, first_name, middle_name, last_name, aliases, date_of_birth, gender, nationality, island_of_origin, height_cm, weight_kg, eye_color, hair_color, distinguishing_marks, status, security_level, admission_date, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship) VALUES

-- Maximum Security Inmates
('b2000001-0001-4000-8000-000000000001', 'FH-2019-0142', '812-456-789', 'Dwayne', 'Ricardo', 'Rolle', '["D-Money", "Dwayne R"]', '1985-03-15', 'MALE', 'Bahamian', 'New Providence', 183, 92.5, 'Brown', 'Black', 'Tattoo of anchor on right forearm, scar above left eyebrow', 'SENTENCED', 'MAXIMUM', '2019-06-20', 'Gloria Rolle', '242-325-4567', 'Mother'),

('b2000001-0001-4000-8000-000000000002', 'FH-2018-0089', '812-234-567', 'Marcus', 'Anthony', 'Thompson', '["Tank"]', '1982-11-22', 'MALE', 'Bahamian', 'Grand Bahama', 190, 105.0, 'Brown', 'Black', 'Full sleeve tattoo left arm, "RIP Mom" on chest', 'SENTENCED', 'MAXIMUM', '2018-03-14', 'Anthony Thompson Sr.', '242-352-8901', 'Father'),

('b2000001-0001-4000-8000-000000000003', 'FH-2020-0201', '812-567-890', 'Jermaine', NULL, 'Ferguson', NULL, '1990-07-08', 'MALE', 'Bahamian', 'Eleuthera', 175, 78.0, 'Brown', 'Black', 'Burn scar on right hand', 'SENTENCED', 'MAXIMUM', '2020-09-03', 'Paulette Ferguson', '242-335-2345', 'Sister'),

-- Medium Security Inmates
('b2000001-0001-4000-8000-000000000004', 'FH-2021-0456', '812-678-901', 'Terrance', 'Lavardo', 'Burrows', '["Terry B"]', '1988-04-30', 'MALE', 'Bahamian', 'Andros', 178, 82.0, 'Brown', 'Black', NULL, 'SENTENCED', 'MEDIUM', '2021-11-15', 'Sandra Burrows', '242-329-6789', 'Wife'),

('b2000001-0001-4000-8000-000000000005', 'FH-2022-0123', '812-789-012', 'Kevin', 'Shawn', 'Cartwright', NULL, '1995-12-10', 'MALE', 'Bahamian', 'Exuma', 170, 70.0, 'Brown', 'Black', 'Pierced left ear', 'SENTENCED', 'MEDIUM', '2022-04-28', 'Maria Cartwright', '242-336-1234', 'Mother'),

('b2000001-0001-4000-8000-000000000006', 'FH-2021-0789', '812-890-123', 'Rashad', 'Valentino', 'Bethel', '["Ras", "Rasta"]', '1992-08-17', 'MALE', 'Bahamian', 'Long Island', 185, 88.0, 'Brown', 'Black', 'Dreadlocks, religious symbols tattoo on back', 'SENTENCED', 'MEDIUM', '2021-07-22', 'Vernita Bethel', '242-337-5678', 'Mother'),

('b2000001-0001-4000-8000-000000000007', 'FH-2023-0234', '812-901-234', 'Davon', NULL, 'Russell', NULL, '1998-02-25', 'MALE', 'Bahamian', 'Abaco', 172, 68.0, 'Brown', 'Black', NULL, 'SENTENCED', 'MEDIUM', '2023-02-10', 'Patricia Russell', '242-367-8901', 'Grandmother'),

('b2000001-0001-4000-8000-000000000008', 'FH-2020-0567', '812-012-345', 'Anthon', 'Michael', 'Saunders', '["Big Mike"]', '1987-09-05', 'MALE', 'Bahamian', 'New Providence', 188, 98.0, 'Brown', 'Black', 'Multiple tattoos on both arms', 'SENTENCED', 'MEDIUM', '2020-12-08', 'Sheila Saunders', '242-324-2345', 'Mother'),

-- Female Inmates
('b2000001-0001-4000-8000-000000000009', 'FH-2022-0890', '812-123-456', 'Shantel', 'Marie', 'Knowles', NULL, '1991-05-14', 'FEMALE', 'Bahamian', 'New Providence', 165, 62.0, 'Brown', 'Black', NULL, 'SENTENCED', 'MEDIUM', '2022-08-19', 'Ricardo Knowles', '242-326-7890', 'Brother'),

('b2000001-0001-4000-8000-000000000010', 'FH-2023-0345', '812-234-568', 'Patrice', 'Nicole', 'Moss', NULL, '1989-10-28', 'FEMALE', 'Bahamian', 'Cat Island', 160, 58.0, 'Brown', 'Black', 'C-section scar', 'SENTENCED', 'MINIMUM', '2023-05-03', 'Deborah Moss', '242-342-1234', 'Mother'),

-- Minimum Security
('b2000001-0001-4000-8000-000000000011', 'FH-2020-0123', '812-345-679', 'Ricardo', 'James', 'Butler', NULL, '1983-01-19', 'MALE', 'Bahamian', 'New Providence', 175, 80.0, 'Brown', 'Black', NULL, 'SENTENCED', 'MINIMUM', '2020-03-15', 'Janet Butler', '242-323-4567', 'Wife'),

('b2000001-0001-4000-8000-000000000012', 'FH-2021-0890', '812-456-780', 'Cedric', 'Paul', 'Bowe', NULL, '1980-06-22', 'MALE', 'Bahamian', 'Inagua', 180, 85.0, 'Brown', 'Black', 'Missing right pinky finger', 'SENTENCED', 'MINIMUM', '2021-09-28', 'Rosemary Bowe', '242-339-8901', 'Sister'),

-- Remand Prisoners
('b2000001-0001-4000-8000-000000000013', 'FH-2024-0567', '812-567-891', 'Kendrick', 'Leon', 'Forbes', '["Kenny"]', '1996-11-30', 'MALE', 'Bahamian', 'New Providence', 177, 75.0, 'Brown', 'Black', NULL, 'REMAND', 'MEDIUM', '2024-10-15', 'Leon Forbes Sr.', '242-327-2345', 'Father'),

('b2000001-0001-4000-8000-000000000014', 'FH-2024-0678', '812-678-902', 'Dario', NULL, 'Miller', NULL, '1993-03-12', 'MALE', 'Bahamian', 'Grand Bahama', 182, 88.0, 'Brown', 'Black', 'Gold front tooth', 'REMAND', 'MEDIUM', '2024-11-02', 'Cynthia Miller', '242-351-5678', 'Mother'),

('b2000001-0001-4000-8000-000000000015', 'FH-2024-0789', '812-789-013', 'Latoya', 'Simone', 'Cooper', NULL, '1994-07-25', 'FEMALE', 'Bahamian', 'New Providence', 163, 55.0, 'Brown', 'Black', NULL, 'REMAND', 'MEDIUM', '2024-11-20', 'Samuel Cooper', '242-324-8901', 'Father'),

-- Additional sentenced inmates for variety
('b2000001-0001-4000-8000-000000000016', 'FH-2019-0234', '812-890-124', 'Valentino', 'Andre', 'Smith', '["Val"]', '1984-12-05', 'MALE', 'Bahamian', 'Bimini', 186, 95.0, 'Brown', 'Black', 'Tribal tattoo on neck', 'SENTENCED', 'MAXIMUM', '2019-04-10', 'Edith Smith', '242-347-1234', 'Mother'),

('b2000001-0001-4000-8000-000000000017', 'FH-2022-0456', '812-901-235', 'Jerome', 'Winston', 'Johnson', NULL, '1990-09-18', 'MALE', 'Bahamian', 'New Providence', 173, 72.0, 'Brown', 'Black', NULL, 'SENTENCED', 'MEDIUM', '2022-06-30', 'Winston Johnson', '242-325-5678', 'Father'),

('b2000001-0001-4000-8000-000000000018', 'FH-2023-0567', '812-012-346', 'Lamont', NULL, 'Williams', '["Monty"]', '1997-04-08', 'MALE', 'Bahamian', 'Eleuthera', 168, 65.0, 'Brown', 'Black', 'Eyebrow piercing', 'SENTENCED', 'MEDIUM', '2023-08-14', 'Shirley Williams', '242-335-8901', 'Mother'),

('b2000001-0001-4000-8000-000000000019', 'FH-2021-0678', '812-123-457', 'Shaquille', 'Devon', 'Davis', NULL, '1994-01-28', 'MALE', 'Bahamian', 'Andros', 192, 102.0, 'Brown', 'Black', 'Basketball tattoo on calf', 'SENTENCED', 'MEDIUM', '2021-04-05', 'Patricia Davis', '242-329-2345', 'Mother'),

('b2000001-0001-4000-8000-000000000020', 'FH-2020-0789', '812-234-569', 'Tyrone', 'Alexander', 'Brown', '["T-Bone"]', '1986-08-11', 'MALE', 'Bahamian', 'New Providence', 179, 84.0, 'Brown', 'Black', 'Knife scar on left cheek', 'SENTENCED', 'MAXIMUM', '2020-01-22', 'Angela Brown', '242-322-5678', 'Sister');

-- =============================================================================
-- COURT CASES
-- =============================================================================
INSERT INTO court_cases (id, inmate_id, case_number, court_type, charges, filing_date, status, presiding_judge, prosecutor, defense_attorney, notes) VALUES

-- Dwayne Rolle - Armed Robbery
('c3000001-0001-4000-8000-000000000001', 'b2000001-0001-4000-8000-000000000001', 'SC-2019-CRI-00142', 'SUPREME',
 '[{"charge": "Armed Robbery", "count": 2, "statute": "Penal Code Chapter 84 Section 339"}, {"charge": "Possession of Firearm with Intent", "count": 1, "statute": "Firearms Act Section 31"}]',
 '2019-04-15', 'ADJUDICATED', 'Hon. Justice Vera Watkins', 'Mr. Garvin Gaskin, DPP Office', 'Mr. Romauld Ferreira', 'Armed robbery of Scotia Bank, Bay Street branch. Firearm recovered at scene.'),

-- Marcus Thompson - Murder
('c3000001-0001-4000-8000-000000000002', 'b2000001-0001-4000-8000-000000000002', 'SC-2017-CRI-00289', 'SUPREME',
 '[{"charge": "Murder", "count": 1, "statute": "Penal Code Chapter 84 Section 291"}]',
 '2017-12-01', 'ADJUDICATED', 'Hon. Justice Carolita Bethel', 'Mrs. Kendra Kelly, DPP Office', 'Mr. Wayne Munroe QC', 'Murder arising from gang-related dispute in Nassau Village.'),

-- Jermaine Ferguson - Drug Trafficking
('c3000001-0001-4000-8000-000000000003', 'b2000001-0001-4000-8000-000000000003', 'SC-2020-CRI-00201', 'SUPREME',
 '[{"charge": "Possession of Dangerous Drugs with Intent to Supply", "count": 1, "statute": "Dangerous Drugs Act Section 22"}, {"charge": "Drug Trafficking", "count": 1, "statute": "Dangerous Drugs Act Section 24"}]',
 '2020-06-10', 'ADJUDICATED', 'Hon. Justice Renae McKay', 'Mr. Lennox Coleby, DPP Office', 'Ms. Tonique Lewis', '15kg cocaine seized at Lynden Pindling International Airport.'),

-- Terrance Burrows - Housebreaking
('c3000001-0001-4000-8000-000000000004', 'b2000001-0001-4000-8000-000000000004', 'SC-2021-CRI-00456', 'SUPREME',
 '[{"charge": "Housebreaking", "count": 3, "statute": "Penal Code Section 293"}, {"charge": "Stealing", "count": 3, "statute": "Penal Code Section 310"}]',
 '2021-08-20', 'ADJUDICATED', 'Hon. Justice Gregory Hilton', 'Ms. Ambria Nottage, DPP Office', 'Mr. Jairam Mangra', 'Series of residential burglaries in Cable Beach area.'),

-- Kevin Cartwright - Robbery
('c3000001-0001-4000-8000-000000000005', 'b2000001-0001-4000-8000-000000000005', 'MC-2022-CRI-01234', 'MAGISTRATES',
 '[{"charge": "Robbery", "count": 1, "statute": "Penal Code Section 339"}]',
 '2022-02-14', 'ADJUDICATED', 'Chief Magistrate Joyann Ferguson-Pratt', 'Sgt. Detective Rolle, RBPF', 'Mr. Calvin Seymour', 'Purse snatching incident in downtown Nassau.'),

-- Rashad Bethel - Dangerous Drugs
('c3000001-0001-4000-8000-000000000006', 'b2000001-0001-4000-8000-000000000006', 'MC-2021-CRI-02345', 'MAGISTRATES',
 '[{"charge": "Possession of Dangerous Drugs", "count": 1, "statute": "Dangerous Drugs Act Section 19"}]',
 '2021-05-03', 'ADJUDICATED', 'Magistrate Samuel McKinney', 'Cpl. Williams, RBPF', 'Ms. Christina Galanos', 'Found in possession of 2 pounds of marijuana.'),

-- Davon Russell - Firearm offense
('c3000001-0001-4000-8000-000000000007', 'b2000001-0001-4000-8000-000000000007', 'MC-2022-CRI-03456', 'MAGISTRATES',
 '[{"charge": "Possession of Unlicensed Firearm", "count": 1, "statute": "Firearms Act Section 3"}, {"charge": "Possession of Ammunition", "count": 1, "statute": "Firearms Act Section 4"}]',
 '2022-11-28', 'ADJUDICATED', 'Magistrate Carolyn Vogt-Evans', 'Sgt. Mackey, RBPF', 'Mr. Roberto Reckley', 'Firearm discovered during traffic stop.'),

-- Anthon Saunders - Assault
('c3000001-0001-4000-8000-000000000008', 'b2000001-0001-4000-8000-000000000008', 'SC-2020-CRI-00567', 'SUPREME',
 '[{"charge": "Assault with Intent to Commit Grievous Harm", "count": 1, "statute": "Penal Code Section 264"}, {"charge": "Causing Grievous Harm", "count": 1, "statute": "Penal Code Section 260"}]',
 '2020-09-15', 'ADJUDICATED', 'Hon. Justice Ian Winder', 'Mr. Anthony Delaney, DPP Office', 'Mr. Lakeisha Hepburn', 'Nightclub altercation resulting in serious injury.'),

-- Shantel Knowles - Fraud
('c3000001-0001-4000-8000-000000000009', 'b2000001-0001-4000-8000-000000000009', 'SC-2022-CRI-00890', 'SUPREME',
 '[{"charge": "Fraud by False Pretenses", "count": 5, "statute": "Penal Code Section 312"}, {"charge": "Money Laundering", "count": 1, "statute": "Proceeds of Crime Act Section 42"}]',
 '2022-05-10', 'ADJUDICATED', 'Hon. Justice Cheryl Grant-Bethel', 'Ms. Darell Taylor, DPP Office', 'Mr. Murrio Ducille', 'Investment fraud scheme targeting elderly victims.'),

-- Patrice Moss - Drugs
('c3000001-0001-4000-8000-000000000010', 'b2000001-0001-4000-8000-000000000010', 'MC-2023-CRI-04567', 'MAGISTRATES',
 '[{"charge": "Possession of Dangerous Drugs", "count": 1, "statute": "Dangerous Drugs Act Section 19"}]',
 '2023-03-20', 'ADJUDICATED', 'Magistrate Kendra Kelly', 'Cpl. Rolle, RBPF', 'Mr. Bjorn Ferguson', 'Found in possession of small quantity of cocaine.'),

-- Ricardo Butler - Fraud
('c3000001-0001-4000-8000-000000000011', 'b2000001-0001-4000-8000-000000000011', 'SC-2019-CRI-00123', 'SUPREME',
 '[{"charge": "Fraud", "count": 2, "statute": "Penal Code Section 312"}]',
 '2019-12-05', 'ADJUDICATED', 'Hon. Justice Guillimina Archer', 'Mr. Basil Cumberbatch, DPP Office', 'Ms. Tai Pinder', 'Fraudulent insurance claims totaling $85,000.'),

-- Cedric Bowe - Stealing
('c3000001-0001-4000-8000-000000000012', 'b2000001-0001-4000-8000-000000000012', 'MC-2021-CRI-05678', 'MAGISTRATES',
 '[{"charge": "Stealing", "count": 1, "statute": "Penal Code Section 310"}]',
 '2021-07-12', 'ADJUDICATED', 'Magistrate Algernon Allen Jr.', 'Sgt. Ferguson, RBPF', 'Mr. Devard Francis', 'Theft of construction materials valued at $12,000.'),

-- Kendrick Forbes - Pending Robbery
('c3000001-0001-4000-8000-000000000013', 'b2000001-0001-4000-8000-000000000013', 'SC-2024-CRI-00567', 'SUPREME',
 '[{"charge": "Armed Robbery", "count": 1, "statute": "Penal Code Section 339"}]',
 '2024-10-20', 'PENDING', 'Hon. Justice Renae McKay', 'Mr. Cordell Frazier, DPP Office', 'Mr. Ian Cargill QC', 'Alleged robbery of convenience store. Awaiting trial.'),

-- Dario Miller - Pending Murder
('c3000001-0001-4000-8000-000000000014', 'b2000001-0001-4000-8000-000000000014', 'SC-2024-CRI-00678', 'SUPREME',
 '[{"charge": "Murder", "count": 1, "statute": "Penal Code Section 291"}]',
 '2024-11-05', 'PENDING', 'Hon. Justice Carolita Bethel', 'Mrs. Darnell Dorsett, DPP Office', 'Mr. Ramona Farquharson-Seymour', 'Alleged shooting death. Awaiting trial.'),

-- Latoya Cooper - Pending Drug Charges
('c3000001-0001-4000-8000-000000000015', 'b2000001-0001-4000-8000-000000000015', 'MC-2024-CRI-06789', 'MAGISTRATES',
 '[{"charge": "Possession of Dangerous Drugs with Intent to Supply", "count": 1, "statute": "Dangerous Drugs Act Section 22"}]',
 '2024-11-22', 'PENDING', 'Magistrate Carolyn Vogt-Evans', 'Cpl. Bain, RBPF', 'Ms. Simone Cambridge', 'Awaiting trial on drug charges.'),

-- Valentino Smith - Murder (Life sentence)
('c3000001-0001-4000-8000-000000000016', 'b2000001-0001-4000-8000-000000000016', 'SC-2018-CRI-00234', 'SUPREME',
 '[{"charge": "Murder", "count": 1, "statute": "Penal Code Section 291"}, {"charge": "Possession of Firearm", "count": 1, "statute": "Firearms Act Section 31"}]',
 '2018-02-20', 'ADJUDICATED', 'Hon. Justice Bernard Turner', 'Mr. Garvin Gaskin, DPP Office', 'Mr. Wayne Munroe QC', 'Gang-related homicide in Bain Town.'),

-- Jerome Johnson - Drugs
('c3000001-0001-4000-8000-000000000017', 'b2000001-0001-4000-8000-000000000017', 'SC-2022-CRI-00456', 'SUPREME',
 '[{"charge": "Possession of Dangerous Drugs with Intent to Supply", "count": 1, "statute": "Dangerous Drugs Act Section 22"}]',
 '2022-04-15', 'ADJUDICATED', 'Hon. Justice Cheryl Grant-Bethel', 'Ms. Olivia Blatch, DPP Office', 'Mr. Crispin Hall', '3kg marijuana seized from vehicle.'),

-- Lamont Williams - Robbery
('c3000001-0001-4000-8000-000000000018', 'b2000001-0001-4000-8000-000000000018', 'MC-2023-CRI-07890', 'MAGISTRATES',
 '[{"charge": "Robbery", "count": 1, "statute": "Penal Code Section 339"}]',
 '2023-06-05', 'ADJUDICATED', 'Chief Magistrate Joyann Ferguson-Pratt', 'Sgt. Wallace, RBPF', 'Mr. Lakeisha Hepburn', 'Street robbery in Carmichael Road area.'),

-- Shaquille Davis - Firearm
('c3000001-0001-4000-8000-000000000019', 'b2000001-0001-4000-8000-000000000019', 'SC-2021-CRI-00678', 'SUPREME',
 '[{"charge": "Possession of Unlicensed Firearm", "count": 1, "statute": "Firearms Act Section 3"}, {"charge": "Possession of Ammunition", "count": 1, "statute": "Firearms Act Section 4"}]',
 '2021-02-10', 'ADJUDICATED', 'Hon. Justice Ian Winder', 'Mr. Eucal Bonaby, DPP Office', 'Ms. Tonique Lewis', 'Firearm and ammunition found during home search.'),

-- Tyrone Brown - Armed Robbery
('c3000001-0001-4000-8000-000000000020', 'b2000001-0001-4000-8000-000000000020', 'SC-2019-CRI-00789', 'SUPREME',
 '[{"charge": "Armed Robbery", "count": 1, "statute": "Penal Code Section 339"}, {"charge": "Causing Grievous Harm", "count": 1, "statute": "Penal Code Section 260"}]',
 '2019-11-18', 'ADJUDICATED', 'Hon. Justice Vera Watkins', 'Mrs. Kendra Kelly, DPP Office', 'Mr. Murrio Ducille', 'Violent robbery of jewelry store, victim seriously injured.');

-- =============================================================================
-- SENTENCES
-- =============================================================================
INSERT INTO sentences (id, inmate_id, court_case_id, sentence_date, sentence_type, original_term_months, life_sentence, is_death_sentence, minimum_term_months, start_date, expected_release_date, time_served_days, good_time_days, sentencing_judge, notes) VALUES

-- Dwayne Rolle - 15 years
('d4000001-0001-4000-8000-000000000001', 'b2000001-0001-4000-8000-000000000001', 'c3000001-0001-4000-8000-000000000001',
 '2019-06-20', 'IMPRISONMENT', 180, false, false, NULL, '2019-06-20', '2034-06-20', 2025, 180,
 'Hon. Justice Vera Watkins', '15 years imprisonment. Armed robbery with firearm. Eligible for parole after 10 years.'),

-- Marcus Thompson - Life
('d4000001-0001-4000-8000-000000000002', 'b2000001-0001-4000-8000-000000000002', 'c3000001-0001-4000-8000-000000000002',
 '2018-03-14', 'LIFE', NULL, true, false, 300, '2018-03-14', NULL, 2490, 220,
 'Hon. Justice Carolita Bethel', 'Life imprisonment with minimum of 25 years before parole eligibility.'),

-- Jermaine Ferguson - 12 years
('d4000001-0001-4000-8000-000000000003', 'b2000001-0001-4000-8000-000000000003', 'c3000001-0001-4000-8000-000000000003',
 '2020-09-03', 'IMPRISONMENT', 144, false, false, NULL, '2020-09-03', '2032-09-03', 1585, 140,
 'Hon. Justice Renae McKay', '12 years for drug trafficking. Major narcotics operation.'),

-- Terrance Burrows - 5 years
('d4000001-0001-4000-8000-000000000004', 'b2000001-0001-4000-8000-000000000004', 'c3000001-0001-4000-8000-000000000004',
 '2021-11-15', 'IMPRISONMENT', 60, false, false, NULL, '2021-11-15', '2026-11-15', 1147, 100,
 'Hon. Justice Gregory Hilton', '5 years for multiple housebreaking offenses.'),

-- Kevin Cartwright - 3 years
('d4000001-0001-4000-8000-000000000005', 'b2000001-0001-4000-8000-000000000005', 'c3000001-0001-4000-8000-000000000005',
 '2022-04-28', 'IMPRISONMENT', 36, false, false, NULL, '2022-04-28', '2025-04-28', 982, 90,
 'Chief Magistrate Joyann Ferguson-Pratt', '3 years for robbery.'),

-- Rashad Bethel - 4 years
('d4000001-0001-4000-8000-000000000006', 'b2000001-0001-4000-8000-000000000006', 'c3000001-0001-4000-8000-000000000006',
 '2021-07-22', 'IMPRISONMENT', 48, false, false, NULL, '2021-07-22', '2025-07-22', 1262, 110,
 'Magistrate Samuel McKinney', '4 years for drug possession.'),

-- Davon Russell - 2 years
('d4000001-0001-4000-8000-000000000007', 'b2000001-0001-4000-8000-000000000007', 'c3000001-0001-4000-8000-000000000007',
 '2023-02-10', 'IMPRISONMENT', 24, false, false, NULL, '2023-02-10', '2025-02-10', 694, 60,
 'Magistrate Carolyn Vogt-Evans', '2 years for firearm possession.'),

-- Anthon Saunders - 7 years
('d4000001-0001-4000-8000-000000000008', 'b2000001-0001-4000-8000-000000000008', 'c3000001-0001-4000-8000-000000000008',
 '2020-12-08', 'IMPRISONMENT', 84, false, false, NULL, '2020-12-08', '2027-12-08', 1489, 130,
 'Hon. Justice Ian Winder', '7 years for assault causing grievous harm.'),

-- Shantel Knowles - 6 years
('d4000001-0001-4000-8000-000000000009', 'b2000001-0001-4000-8000-000000000009', 'c3000001-0001-4000-8000-000000000009',
 '2022-08-19', 'IMPRISONMENT', 72, false, false, NULL, '2022-08-19', '2028-08-19', 869, 75,
 'Hon. Justice Cheryl Grant-Bethel', '6 years for fraud and money laundering.'),

-- Patrice Moss - 18 months
('d4000001-0001-4000-8000-000000000010', 'b2000001-0001-4000-8000-000000000010', 'c3000001-0001-4000-8000-000000000010',
 '2023-05-03', 'IMPRISONMENT', 18, false, false, NULL, '2023-05-03', '2024-11-03', 612, 55,
 'Magistrate Kendra Kelly', '18 months for drug possession.'),

-- Ricardo Butler - 4 years
('d4000001-0001-4000-8000-000000000011', 'b2000001-0001-4000-8000-000000000011', 'c3000001-0001-4000-8000-000000000011',
 '2020-03-15', 'IMPRISONMENT', 48, false, false, NULL, '2020-03-15', '2024-03-15', 1756, 160,
 'Hon. Justice Guillimina Archer', '4 years for insurance fraud. Completed sentence, eligible for supervised release.'),

-- Cedric Bowe - 2 years
('d4000001-0001-4000-8000-000000000012', 'b2000001-0001-4000-8000-000000000012', 'c3000001-0001-4000-8000-000000000012',
 '2021-09-28', 'IMPRISONMENT', 24, false, false, NULL, '2021-09-28', '2023-09-28', 1194, 105,
 'Magistrate Algernon Allen Jr.', '2 years for stealing. Good behavior, work program.'),

-- Valentino Smith - Life
('d4000001-0001-4000-8000-000000000016', 'b2000001-0001-4000-8000-000000000016', 'c3000001-0001-4000-8000-000000000016',
 '2019-04-10', 'LIFE', NULL, true, false, 360, '2019-04-10', NULL, 2096, 185,
 'Hon. Justice Bernard Turner', 'Life imprisonment. Minimum 30 years before parole consideration.'),

-- Jerome Johnson - 5 years
('d4000001-0001-4000-8000-000000000017', 'b2000001-0001-4000-8000-000000000017', 'c3000001-0001-4000-8000-000000000017',
 '2022-06-30', 'IMPRISONMENT', 60, false, false, NULL, '2022-06-30', '2027-06-30', 919, 80,
 'Hon. Justice Cheryl Grant-Bethel', '5 years for drug trafficking.'),

-- Lamont Williams - 2 years
('d4000001-0001-4000-8000-000000000018', 'b2000001-0001-4000-8000-000000000018', 'c3000001-0001-4000-8000-000000000018',
 '2023-08-14', 'IMPRISONMENT', 24, false, false, NULL, '2023-08-14', '2025-08-14', 509, 45,
 'Chief Magistrate Joyann Ferguson-Pratt', '2 years for robbery.'),

-- Shaquille Davis - 4 years
('d4000001-0001-4000-8000-000000000019', 'b2000001-0001-4000-8000-000000000019', 'c3000001-0001-4000-8000-000000000019',
 '2021-04-05', 'IMPRISONMENT', 48, false, false, NULL, '2021-04-05', '2025-04-05', 1371, 120,
 'Hon. Justice Ian Winder', '4 years for firearm possession.'),

-- Tyrone Brown - 10 years
('d4000001-0001-4000-8000-000000000020', 'b2000001-0001-4000-8000-000000000020', 'c3000001-0001-4000-8000-000000000020',
 '2020-01-22', 'IMPRISONMENT', 120, false, false, NULL, '2020-01-22', '2030-01-22', 1809, 160,
 'Hon. Justice Vera Watkins', '10 years for armed robbery with grievous harm.');

-- =============================================================================
-- CLEMENCY PETITIONS - Prerogative of Mercy Applications
-- =============================================================================
INSERT INTO clemency_petitions (id, inmate_id, sentence_id, petition_number, petition_type, status, filed_date, petitioner_name, petitioner_relationship, grounds_for_clemency, supporting_documents, victim_notification_date, victim_response, committee_review_date, committee_recommendation, minister_review_date, minister_recommendation, governor_general_date, decision_date, decision_notes, granted_reduction_days) VALUES

-- Active Petitions Under Review
('e5000001-0001-4000-8000-000000000001', 'b2000001-0001-4000-8000-000000000001', 'd4000001-0001-4000-8000-000000000001',
 'POM-2024-0042', 'COMMUTATION', 'UNDER_REVIEW', '2024-09-15',
 'Gloria Rolle', 'Mother',
 'Petitioner respectfully requests commutation of sentence on the following grounds: (1) Exemplary conduct during incarceration with no disciplinary infractions; (2) Successful completion of anger management and vocational training programs; (3) Strong family support system and confirmed employment upon release with Thompson Construction Ltd; (4) Has served more than 5 years of 15-year sentence; (5) Victim family has expressed no objection to early release consideration.',
 '["character_references.pdf", "vocational_certificate.pdf", "employment_letter.pdf"]',
 '2024-10-01', 'Victim family indicated no objection to clemency consideration.',
 NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Committee Scheduled
('e5000001-0001-4000-8000-000000000002', 'b2000001-0001-4000-8000-000000000002', 'd4000001-0001-4000-8000-000000000002',
 'POM-2024-0028', 'PARDON', 'COMMITTEE_SCHEDULED', '2024-06-20',
 'Wayne Munroe QC', 'Legal Representative',
 'Application for full pardon based on new evidence: (1) Key prosecution witness has recanted testimony in sworn affidavit; (2) DNA evidence not available at trial now excludes applicant; (3) Alibi witnesses located who were not called at trial; (4) Request for Attorney General review of conviction. Applicant maintains innocence throughout.',
 '["witness_recantation.pdf", "dna_report.pdf", "alibi_statements.pdf", "legal_brief.pdf"]',
 NULL, NULL,
 '2025-02-20', NULL, NULL, NULL, NULL, NULL, NULL, NULL),

-- Awaiting Minister Review
('e5000001-0001-4000-8000-000000000003', 'b2000001-0001-4000-8000-000000000004', 'd4000001-0001-4000-8000-000000000004',
 'POM-2024-0035', 'REMISSION', 'AWAITING_MINISTER', '2024-07-10',
 'Terrance Lavardo Burrows', 'Self',
 'Application for remission of sentence: (1) First-time offender with no prior criminal history; (2) Full restitution of $15,000 made to victims; (3) Completed rehabilitation programs including substance abuse counseling; (4) Has served over 3 years of 5-year sentence; (5) Elderly mother in poor health requires care.',
 '["restitution_receipt.pdf", "program_certificates.pdf", "medical_report.pdf"]',
 '2024-08-15', 'Victims confirmed receipt of restitution. No objection to early release.',
 '2024-10-10', 'The Advisory Committee recommends approval of 12-month sentence reduction based on: rehabilitation progress, victim restitution, family circumstances, and first-offense status.',
 NULL, NULL, NULL, NULL, NULL, NULL),

-- Governor General Review
('e5000001-0001-4000-8000-000000000004', 'b2000001-0001-4000-8000-000000000011', 'd4000001-0001-4000-8000-000000000011',
 'POM-2024-0015', 'REMISSION', 'GOVERNOR_GENERAL', '2024-03-05',
 'Janet Butler', 'Wife',
 'Compassionate release request: (1) Petitioner diagnosed with Stage 3 colon cancer requiring ongoing treatment; (2) Has completed full sentence term and awaiting final release processing; (3) Family prepared to provide full-time care; (4) Non-violent offense with full restitution made; (5) Poses no risk to public safety.',
 '["medical_diagnosis.pdf", "treatment_plan.pdf", "family_care_plan.pdf"]',
 NULL, 'N/A - No direct victim in fraud case.',
 '2024-05-20', 'Committee strongly recommends immediate compassionate release given medical circumstances and completed sentence.',
 '2024-07-15', 'Minister concurs with Committee recommendation. Recommend expedited processing.',
 '2024-09-01', NULL, NULL, NULL),

-- Recently Granted
('e5000001-0001-4000-8000-000000000005', 'b2000001-0001-4000-8000-000000000012', 'd4000001-0001-4000-8000-000000000012',
 'POM-2023-0089', 'REMISSION', 'GRANTED', '2023-06-15',
 'Cedric Paul Bowe', 'Self',
 'Application for early release: (1) Exemplary work program participation - supervisor commendation; (2) Zero disciplinary infractions; (3) Completed sentence requirements with maximum good time credits; (4) Secured employment with family fishing business in Inagua; (5) Community support letters from Inagua community leaders.',
 '["work_evaluation.pdf", "community_letters.pdf", "employment_confirmation.pdf"]',
 '2023-07-20', 'No objection from affected party.',
 '2023-09-10', 'Committee recommends approval of 6-month early release based on exceptional rehabilitation.',
 '2023-10-25', 'Minister concurs. Recommend approval.',
 '2023-11-15', '2023-12-01',
 'Sentence remission of 180 days granted by His Excellency the Governor-General on recommendation of the Advisory Committee on the Prerogative of Mercy. Inmate demonstrated exceptional rehabilitation and has strong community reintegration plan.',
 180),

-- Previously Denied
('e5000001-0001-4000-8000-000000000006', 'b2000001-0001-4000-8000-000000000003', 'd4000001-0001-4000-8000-000000000003',
 'POM-2023-0045', 'COMMUTATION', 'DENIED', '2023-03-20',
 'Paulette Ferguson', 'Sister',
 'Request for sentence reduction: (1) Family hardship - sister sole supporter of elderly parents; (2) Brother has shown remorse for actions; (3) First drug offense; (4) Willing to participate in any required programs.',
 '["family_statement.pdf", "hardship_documentation.pdf"]',
 NULL, NULL,
 '2023-06-15', 'Committee does not recommend approval. Offense involved significant quantity of narcotics (15kg cocaine). Insufficient time served. Applicant should reapply after serving minimum of 6 years.',
 '2023-07-20', 'Minister concurs with Committee. Deny petition without prejudice to future application.',
 NULL, '2023-08-10',
 'Petition denied. Serious nature of offense and insufficient time served. May reapply after December 2026.',
 NULL),

-- Withdrawn petition
('e5000001-0001-4000-8000-000000000007', 'b2000001-0001-4000-8000-000000000009', 'd4000001-0001-4000-8000-000000000009',
 'POM-2023-0067', 'COMMUTATION', 'WITHDRAWN', '2023-08-01',
 'Shantel Marie Knowles', 'Self',
 'Request for sentence review based on cooperation with authorities in related investigations.',
 '["cooperation_letter.pdf"]',
 NULL, NULL,
 NULL, NULL, NULL, NULL, NULL, NULL,
 'Petition withdrawn by applicant pending outcome of cooperation agreement with Office of the Attorney General.',
 NULL),

-- Deferred petition
('e5000001-0001-4000-8000-000000000008', 'b2000001-0001-4000-8000-000000000020', 'd4000001-0001-4000-8000-000000000020',
 'POM-2024-0055', 'REPRIEVE', 'DEFERRED', '2024-10-01',
 'Angela Brown', 'Sister',
 'Request for temporary release reprieve: Mother critically ill in Princess Margaret Hospital. Request 14-day compassionate leave to be with family during this time.',
 '["hospital_admission.pdf", "family_petition.pdf"]',
 NULL, 'Victim objected to any form of release or leave.',
 '2024-11-05', 'Committee defers decision pending: (1) Resolution of victims objection; (2) Security assessment for temporary release; (3) Updated medical prognosis for mother.',
 NULL, NULL, NULL, NULL,
 'Deferred for additional information. Committee to reconvene January 2025.',
 NULL),

-- Another granted petition
('e5000001-0001-4000-8000-000000000009', 'b2000001-0001-4000-8000-000000000006', 'd4000001-0001-4000-8000-000000000006',
 'POM-2024-0022', 'REMISSION', 'GRANTED', '2024-04-12',
 'Vernita Bethel', 'Mother',
 'Application for sentence reduction: (1) Son has completed drug rehabilitation program with distinction; (2) Actively participates in prison ministry and mentors younger inmates; (3) Has maintained employment in prison agriculture program; (4) First drug offense, non-violent; (5) Family business (Bethel Farms, Long Island) prepared to employ upon release.',
 '["rehab_certificate.pdf", "ministry_letter.pdf", "employment_offer.pdf", "character_references.pdf"]',
 NULL, 'N/A - victimless drug offense.',
 '2024-06-20', 'Committee recommends approval of 8-month reduction. Exceptional rehabilitation demonstrated.',
 '2024-08-05', 'Minister concurs. Strongly support early release.',
 '2024-09-15', '2024-10-01',
 'His Excellency grants remission of 240 days. Inmate to be released with conditions including continued participation in community drug program.',
 240),

-- Recent submission
('e5000001-0001-4000-8000-000000000010', 'b2000001-0001-4000-8000-000000000017', 'd4000001-0001-4000-8000-000000000017',
 'POM-2024-0068', 'COMMUTATION', 'SUBMITTED', '2024-12-10',
 'Winston Johnson', 'Father',
 'Request for sentence reduction on behalf of son: (1) Young first-time offender, age 34; (2) Has shown genuine remorse and transformation; (3) Father willing to provide housing and supervision; (4) Has been accepted into University of The Bahamas correspondence program; (5) No prior criminal history.',
 '["father_statement.pdf", "university_acceptance.pdf", "rehabilitation_assessment.pdf"]',
 NULL, NULL,
 NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
SELECT 'Seed completed successfully!' as status;
SELECT 'Housing Units: ' || COUNT(*) FROM housing_units;
SELECT 'Inmates: ' || COUNT(*) FROM inmates;
SELECT 'Court Cases: ' || COUNT(*) FROM court_cases;
SELECT 'Sentences: ' || COUNT(*) FROM sentences;
SELECT 'Clemency Petitions: ' || COUNT(*) FROM clemency_petitions;

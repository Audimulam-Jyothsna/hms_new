CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL
);

CREATE TABLE appointment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    details TEXT NOT NULL,
    date_time VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES user (id),
    FOREIGN KEY (doctor_id) REFERENCES user (id)
);

CREATE TABLE medical_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    date VARCHAR(50) NOT NULL,
    diagnosis TEXT NOT NULL,
    treatment TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES user (id),
    FOREIGN KEY (doctor_id) REFERENCES user (id)
);

CREATE TABLE notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN DEFAULT 0,
    timestamp VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comments TEXT,
    FOREIGN KEY (patient_id) REFERENCES user (id),
    FOREIGN KEY (doctor_id) REFERENCES user (id)
);
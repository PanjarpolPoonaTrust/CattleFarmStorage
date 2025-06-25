CREATE DATABASE IF NOT EXISTS cattle_db;
USE cattle_db;

CREATE TABLE IF NOT EXISTS cattle_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    breed VARCHAR(100),
    color VARCHAR(50),
    age INT,
    shed_no VARCHAR(20),
    notes TEXT,
    photo1 VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS health_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cattle_id INT,
    checkup_date DATE,
    diagnosis TEXT,
    medicines TEXT,
    remarks TEXT,
    treatment_photo VARCHAR(255),
    FOREIGN KEY (cattle_id) REFERENCES cattle_info(id) ON DELETE CASCADE
);

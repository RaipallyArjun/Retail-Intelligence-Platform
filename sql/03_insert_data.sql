LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/processed_superstore.csv'

INTO TABLE Superstore

FIELDS TERMINATED BY ','

ENCLOSED BY '"'

LINES TERMINATED BY '\n'

IGNORE 1 ROWS;
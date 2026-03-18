CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT,
    department VARCHAR(255)
);

CREATE TABLE sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10, 2),
    sale_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO users (name, age, department) VALUES 
('Alice', 28, 'Sales'),
('Bob', 35, 'Engineering'),
('Charlie', 32, 'Sales'),
('David', 40, 'Marketing');

INSERT INTO sales (user_id, amount, sale_date) VALUES 
(1, 1500.50, '2023-10-01'),
(1, 2000.00, '2023-10-15'),
(3, 800.75, '2023-10-05'),
(3, 1200.00, '2023-10-20'),
(4, 500.00, '2023-10-10');

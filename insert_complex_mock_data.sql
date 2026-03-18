-- 1. 创建产品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- 2. 插入产品数据 (涵盖电子产品、办公用品、服装)
INSERT INTO products (name, category, unit_price) VALUES
('Laptop Pro', 'Electronics', 1200.00),
('Smartphone X', 'Electronics', 800.00),
('Wireless Mouse', 'Electronics', 45.00),
('Ergonomic Chair', 'Office', 150.00),
('Standing Desk', 'Office', 300.00),
('Cotton T-Shirt', 'Clothing', 25.00),
('Winter Jacket', 'Clothing', 120.00);

-- 3. 扩展原有销售表 (添加产品关联与数量)
CREATE TABLE IF NOT EXISTS complex_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT,
    total_amount DECIMAL(10, 2),
    region VARCHAR(100),
    sale_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 4. 插入具有时间序列和多维度的销售数据
INSERT INTO complex_sales (user_id, product_id, quantity, total_amount, region, sale_date) VALUES
(1, 1, 2, 2400.00, 'East', '2023-01-05'),
(1, 4, 5, 750.00, 'East', '2023-01-12'),
(2, 2, 10, 8000.00, 'West', '2023-01-15'),
(3, 6, 50, 1250.00, 'South', '2023-01-20'),
(4, 3, 20, 900.00, 'North', '2023-01-25'),
(1, 2, 5, 4000.00, 'East', '2023-02-02'),
(2, 1, 3, 3600.00, 'West', '2023-02-10'),
(2, 5, 4, 1200.00, 'West', '2023-02-14'),
(3, 7, 30, 3600.00, 'South', '2023-02-18'),
(4, 4, 10, 1500.00, 'North', '2023-02-28'),
(1, 1, 4, 4800.00, 'East', '2023-03-05'),
(1, 3, 30, 1350.00, 'East', '2023-03-10'),
(2, 2, 8, 6400.00, 'West', '2023-03-15'),
(3, 6, 80, 2000.00, 'South', '2023-03-20'),
(3, 7, 20, 2400.00, 'South', '2023-03-22'),
(4, 5, 6, 1800.00, 'North', '2023-03-28');

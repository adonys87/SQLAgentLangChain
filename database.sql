
--Create user to test
CREATE USER root WITH SUPERUSER PASSWORD 'admin';
GRANT ALL PRIVILEGES ON DATABASE "SQLAgent" to root;

-- Create the database
CREATE DATABASE SQLAgent;



-- Tabela de clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefone VARCHAR(15),
    endereco TEXT,
    saldo NUMERIC(10, 2) DEFAULT 0,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de produtos
CREATE TABLE produtos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    marca TEXT NOT NULL, 
    descricao TEXT,
    preco NUMERIC(10, 2) NOT NULL CHECK (preco >= 0),
    estoque INT NOT NULL CHECK (estoque >= 0),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de transações
CREATE TABLE transacoes (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL CHECK (quantidade > 0),
    valor_total NUMERIC(10, 2) NOT NULL CHECK (valor_total >= 0),
    data_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
);


--Inserts

INSERT INTO clientes (nome, email, telefone, endereco, saldo) VALUES
('João Silva', 'joao.silva@example.com', '(11) 9999-8888', 'Rua A, 123 - São Paulo, SP',500),
('Maria Oliveira', 'maria.oliveira@example.com', '(21) 8888-7777', 'Av. B, 456 - Rio de Janeiro, RJ',20),
('Carlos Souza', 'carlos.souza@example.com', '(31) 7777-6666', 'Rua C, 789 - Belo Horizonte, MG',1000),
('Ana Costa', 'ana.costa@example.com', '(41) 6666-5555', 'Av. D, 101 - Curitiba, PR',0),
('Pedro Santos', 'pedro.santos@example.com', '(51) 5555-4444', 'Rua E, 202 - Porto Alegre, RS',0),
('Fernanda Lima', 'fernanda.lima@example.com', '(61) 4444-3333', 'Av. F, 303 - Brasília, DF',70000),
('Ricardo Pereira', 'ricardo.pereira@example.com', '(71) 3333-2222', 'Rua G, 404 - Salvador, BA',8000),
('Juliana Almeida', 'juliana.almeida@example.com', '(81) 2222-1111', 'Av. H, 505 - Recife, PE',10),
('Lucas Gomes', 'lucas.gomes@example.com', '(91) 1111-0000', 'Rua I, 606 - Manaus, AM',0),
('Patrícia Rocha', 'patricia.rocha@example.com', '(85) 9999-8888', 'Av. J, 707 - Fortaleza, CE',500);


INSERT INTO produtos (nome, descricao, preco, estoque, marca) VALUES
('Notebook Dell', 'Notebook Dell Inspiron 15', 3500.00, 10, 'Dell'),
('Smartphone Samsung', 'Smartphone Samsung Galaxy S21', 2500.00, 20, 'Samsung'),
('TV LG 4K', 'TV LG 55 polegadas 4K UHD', 3000.00, 5, 'LG'),
('Fone de Ouvido Sony', 'Fone de Ouvido Sony WH-1000XM4', 1200.00, 15, 'Sony'),
('Tablet Apple', 'Tablet Apple iPad Pro 11', 4500.00, 8, 'Apple'),
('Câmera Canon', 'Câmera Canon EOS R6', 8000.00, 3, 'Canon'),
('Geladeira Brastemp', 'Geladeira Brastemp Frost Free', 4000.00, 7, 'Brastemp'),
('Máquina de Lavar Electrolux', 'Máquina de Lavar Electrolux 12kg', 2500.00, 6, 'Electrolux'),
('Micro-ondas Panasonic', 'Micro-ondas Panasonic 32L', 800.00, 12, 'Panasonic'),
('Ventilador Arno', 'Ventilador Arno Turbo Power', 200.00, 25, 'Arno');

INSERT INTO transacoes (cliente_id, produto_id, quantidade, valor_total) VALUES
(1, 1, 1, 3500.00),
(2, 2, 1, 2500.00),
(3, 3, 1, 3000.00),
(4, 4, 2, 2400.00),
(5, 5, 1, 4500.00),
(6, 6, 1, 8000.00),
(7, 7, 1, 4000.00),
(8, 8, 1, 2500.00),
(9, 9, 1, 800.00),
(10, 10, 3, 600.00),
(1, 2, 1, 2500.00),
(2, 3, 1, 3000.00),
(3, 4, 1, 1200.00),
(4, 5, 1, 4500.00),
(5, 6, 1, 8000.00),
(6, 7, 1, 4000.00),
(7, 8, 1, 2500.00),
(8, 9, 1, 800.00),
(9, 10, 2, 400.00),
(10, 1, 1, 3500.00),
(1, 3, 1, 3000.00),
(2, 4, 1, 1200.00),
(3, 5, 1, 4500.00),
(4, 6, 1, 8000.00),
(5, 7, 1, 4000.00),
(6, 8, 1, 2500.00),
(7, 9, 1, 800.00),
(8, 10, 1, 200.00),
(9, 1, 1, 3500.00),
(10, 2, 1, 2500.00),
(1, 4, 1, 1200.00),
(2, 5, 1, 4500.00),
(3, 6, 1, 8000.00),
(4, 7, 1, 4000.00),
(5, 8, 1, 2500.00),
(6, 9, 1, 800.00),
(7, 10, 1, 200.00),
(8, 1, 1, 3500.00),
(9, 2, 1, 2500.00),
(10, 3, 1, 3000.00),
(1, 5, 1, 4500.00),
(2, 6, 1, 8000.00),
(3, 7, 1, 4000.00),
(4, 8, 1, 2500.00),
(5, 9, 1, 800.00),
(6, 10, 1, 200.00),
(7, 1, 1, 3500.00),
(8, 2, 1, 2500.00),
(9, 3, 1, 3000.00),
(10, 4, 1, 1200.00);
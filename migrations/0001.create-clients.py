from yoyo import step

step("CREATE TABLE clients(id SERIAL PRIMARY KEY, name TEXT NOT NULL)", ignore_errors='apply')
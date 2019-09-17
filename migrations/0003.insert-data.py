from yoyo import step

step("INSERT INTO clients(name) VALUES "
     " ('Иванов Иван Иванович'),"
     " ('Петров Пётр Петрович'),"
     " ('Семёнов Семён Семёнович'),"
     " ('Алексеев Алексей Алексеевич'),"
     " ('Александров Александр Александрович')"
     )

step("INSERT INTO cards(owner_id, payment_system, currency, balance) VALUES"
     " (1, 'MasterCard', 'RUB', 15000),"
     " (2, 'Visa', 'RUB', 13000),"
     " (2, 'MasterCard', 'EUR', 2000),"
     " (3, 'Visa', 'EUR', 3000),"
     " (3, 'MasterCard', 'USD', 1500),"
     " (3, 'Мир', 'RUB', 20000),"
     " (4, 'PayPal', 'USD', 400)"
     )
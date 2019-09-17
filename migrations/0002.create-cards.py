from yoyo import step

step("CREATE TABLE CARDS("
     " id SERIAL PRIMARY KEY,"
     " owner_id BIGINT NOT NULL,"
     " payment_system TEXT NOT NULL,"
     " currency TEXT NOT NULL,"
     " balance NUMERIC NOT NULL DEFAULT 0,"
     " CONSTRAINT cards_fk FOREIGN KEY (owner_id) REFERENCES public.clients (id)"
     " ON UPDATE CASCADE ON DELETE RESTRICT)", ignore_errors='apply')
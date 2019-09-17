import model


class Database:

    def __init__(self, transactor):
        self.__transactor = transactor

    async def all_cards(self, offset, limit):
        result = []
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor('SELECT * FROM cards OFFSET $1 LIMIT $2', offset, limit):
                    result.append(model.Card(
                        id=record['id'],
                        owner_id=record['owner_id'],
                        payment_system=record['payment_system'],
                        currency=record['currency'],
                        balance=float(record['balance'])
                    ))
                count = await conn.fetchval('SELECT COUNT(*) FROM cards')
        return result, count

    async def all_cards_by_client_id(self, client_id):
        result = []
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor('SELECT * FROM cards WHERE owner_id = $1', client_id):
                    result.append(model.Card(
                        id=record['id'],
                        owner_id=record['owner_id'],
                        payment_system=record['payment_system'],
                        currency=record['currency'],
                        balance=float(record['balance'])
                    ))
        return result

    async def all_cards_by_owner_ids(self, ids):
        result = []
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor('SELECT * FROM cards WHERE owner_id = ANY($1::int[])', ids):
                    result.append(model.Card(
                        id=record['id'],
                        owner_id=record['owner_id'],
                        payment_system=record['payment_system'],
                        currency=record['currency'],
                        balance=float(record['balance'])
                    ))
        return result

    async def add_card(self, owner_id: int, payment_system: str, currency: str, balance: float):
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                record = await conn.fetchrow(
                    "INSERT INTO cards(owner_id, payment_system, currency, balance) VALUES($1, $2, $3, $4) RETURNING *",
                    owner_id, payment_system, currency, balance
                )
                return model.Card(
                    id=record['id'],
                    owner_id=record['owner_id'],
                    payment_system=record['payment_system'],
                    currency=record['currency'],
                    balance=float(record['balance'])
                )

    async def change_card(self, card_id, data):
        changes = [''.join(x) for x in [{'{} = ${}'.format(v, i + 2)} for (i, v) in enumerate(data)]]
        values = [card_id] + list(data.values())
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                record = await conn.fetchrow("UPDATE cards SET {} WHERE id = $1 RETURNING *".format(", ".join(changes)), *values)
                if record:
                    return model.Card(
                        id=record['id'],
                        owner_id=record['owner_id'],
                        payment_system=record['payment_system'],
                        currency=record['currency'],
                        balance=float(record['balance'])
                    )
                else:
                    return None

    async def all_clients(self, offset, limit):
        result = []
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                async for record in conn.cursor('SELECT * FROM clients OFFSET $1 LIMIT $2', offset, limit):
                    result.append(model.Client(
                        id=record['id'],
                        name=record['name'],
                        cards=frozenset()
                    ))
                count = await conn.fetchval('SELECT COUNT(*) FROM cards')
        return result, count

    async def client_by_id(self, client_id):
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                record = await conn.fetchrow("SELECT * FROM clients WHERE id = $1", client_id)
                if record:
                    return model.Client(
                        id=record['id'],
                        name=record['name'],
                        cards=frozenset()
                    )
                else:
                    return None

    async def add_client(self, name):
        async with self.__transactor.acquire() as conn:
            async with conn.transaction():
                record = await conn.fetchrow("INSERT INTO clients(name) VALUES($1) RETURNING *", name)
                return model.Client(
                    id=record['id'],
                    name=record['name'],
                    cards=frozenset()
                )
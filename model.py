import itertools

from asyncpg.exceptions import ForeignKeyViolationError
from database import Database
from dataclasses import dataclass, replace
from voluptuous import Schema, Required


@dataclass(frozen=True)
class Client:
    id: int
    name: str
    cards: list


@dataclass(frozen=True)
class Balance(Client):
    balance: float


@dataclass(frozen=True)
class Card:
    id: int
    owner_id: int
    payment_system: str
    currency: str
    balance: float


class ItemNotFoundException(Exception):
    pass


class ClientModel:
    def __init__(self, transactor):
        self.__data_source = Database(transactor)

    async def all_cards(self, offset, limit):
        return await self.__data_source.all_cards(offset, limit)

    async def add_card(self, data):
        Schema({
            'owner_id': int,
            'payment_system': str,
            'currency': str,
            'balance': float,
        }, required=True)(data)
        try:
            return await self.__data_source.add_card(
                data['owner_id'], data['payment_system'], data['currency'], data['balance']
            )
        except ForeignKeyViolationError:
            raise ItemNotFoundException('Клиент с идентификатором {} не найден'.format(data['owner_id']))

    async def all_clients(self, offset, limit):
        clients, count = await self.__data_source.all_clients(offset, limit)
        cards = {k: list(v) for (k, v) in itertools.groupby(
            await self.__data_source.all_cards_by_owner_ids(list(map(lambda x: x.id, clients))), lambda x: x.owner_id
        )}
        return list(map(lambda x: replace(x, cards=cards.get(x.id, list())), clients)), count

    async def add_client(self, data):
        Schema({Required('name'): str})(data)
        return await self.__data_source.add_client(data.get('name'))

    async def client_balance(self, client_id):
        client = await self.__data_source.client_by_id(client_id)
        if client is None:
            raise ItemNotFoundException('Клиент с идентификатором {} не найден'.format(client_id))
        cards = await self.__data_source.all_cards_by_client_id(client_id)
        balance = sum(list(map(lambda x: x.balance, cards)))
        return Balance(
            id=client.id,
            name=client.name,
            cards=cards,
            balance=balance
        )

    async def change_card(self, card_id, data):
        Schema({
            'owner_id': int,
            'payment_system': str,
            'currency': str,
            'balance': float,
        })(data)
        card = await self.__data_source.change_card(card_id, data)
        if card is None:
            raise ItemNotFoundException('Карта с идентификатором {} не найдена'.format(card_id))
        return card

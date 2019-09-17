import accept
import logging

from aiohttp import web, web_exceptions
from aiohttp_swagger import setup_swagger
from model import ClientModel, ItemNotFoundException
from protocol import *
from prometheus_client import REGISTRY, exposition
from urllib.parse import parse_qs
from voluptuous import MultipleInvalid


class Api:
    DEFAULT_CONTENT_TYPE = "application/json"
    logger = logging.getLogger(__name__)

    registry = REGISTRY
    __encoders = {
        "application/xml": XMLEncoder(),
        "application/json": JsonEncoder()
    }

    def __init__(self, host, port, transactor):
        self.__app = web.Application()
        self.__host = host
        self.__port = port
        self.__app.add_routes([
            web.get('/', self.health),
            web.get('/metrics', self.metrics),
            web.get('/v1/cards', self.card_list),
            web.post('/v1/cards', self.add_card),
            web.get('/v1/clients', self.client_list),
            web.post('/v1/clients', self.add_client),
            web.get(r'/v1/clients/{id:\d+}/balance', self.client_balance),
            web.put(r'/v1/cards/{id:\d+}', self.change_card)
        ])
        self.__client_model = ClientModel(transactor)

    def __paginate(self, request):
        qs = parse_qs(request.query_string)
        offsets = qs.get('offset', [0])
        if len(offsets) > 1:
            raise web_exceptions.HTTPBadRequest(text='Invalid offset value')

        limits = qs.get('limit', [20])
        if len(limits) > 1:
            raise web_exceptions.HTTPBadRequest(text='Invalid limit value')

        return int(offsets[0]), int(limits[0])

    def __choose_encoder(self, request):
        for accept_header in accept.parse(request.headers.get('Accept')):
            if accept_header.media_type == '*/*':
                return self.__encoders.get(self.DEFAULT_CONTENT_TYPE)
            encoder = self.__encoders.get(accept_header.media_type)
            if encoder is not None:
                return encoder
        raise web_exceptions.HTTPNotAcceptable()

    async def __decode_post(self, request):
        if request.content_type == "application/json":
            return await request.json()
        if request.content_type == "application/xml":
            return {"data": "xml"}
        raise web_exceptions.HTTPBadRequest(
            text="Unknown Content-Type header. Only application/json, application/xml are allowed."
        )

    async def start(self):
        setup_swagger(self.__app, swagger_url='/v1/docs')
        runner = web.AppRunner(self.__app)
        await runner.setup()
        service = web.TCPSite(runner, self.__host, self.__port)
        await service.start()
        self.logger.info('Service is started at %s:%s', self.__host, self.__port)

    async def health(self, _):
        """
        ---
        description: Запрос для проверки успешного запуска сервиса.
        tags:
        - Health check
        produces:
        - text/plain
        responses:
            "200":
                description: успех. Возвращает информацию о сервисе
        """
        return web.Response(text="Ok")

    async def metrics(self, request):
        """
        ---
        description: Запрос для получения метрик сервиса
        tags:
        - Metrics
        produces:
        - text/plain
        responses:
            "200":
                description: успех. Возвращает метрики
        """
        encoder, content_type = exposition.choose_encoder(request.headers.get('Accept'))
        scrape = encoder(self.registry)
        return web.Response(headers=dict([('Content-Type', content_type)]), body=scrape)

    async def card_list(self, request):
        """
        ---
        description: Запрос для получения списка карт клиентов
        tags:
        - Cards
        produces:
        - application/json
        - application/xml
        parameters:
        - name: offset
          in: query
          description: Pagination offset
          required: false
          type: integer
        - name: limit
          in: query
          description: Pagination limit
          required: false
          type: integer
        responses:
            "200":
                description: успех. Возвращает список карт клиентов
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        encoder = self.__choose_encoder(request)
        offset, limit = self.__paginate(request)
        cards, count = await self.__client_model.all_cards(offset, limit)
        return web.Response(content_type=encoder.content_type, body=encoder.encode(cards), headers={"X-Total": str(count)})

    async def add_card(self, request):
        """
        ---
        description: Запрос для добавления новой карты клиента
        tags:
        - Cards
        produces:
        - application/json
        - application/xml
        parameters:
        - name: card
          in: body
          description: данные новой карты
          required: true
          schema:
            type: object
            properties:
              owner_id:
                type: integer
                description: идентификатор владельца карты
                required: true
              payment_system:
                type: string
                description: платежная система
                required: true
              currency:
                type: string
                description: валюта карты
                required: true
              balance:
                type: numeric
                description: баланс карты
                required: true
        responses:
            "200":
                description: успех. Возвращает данные новой карты клиента
            "404":
                description: ошибка. Клиент не найден
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        encoder = self.__choose_encoder(request)
        data = await self.__decode_post(request)
        try:
            card = await self.__client_model.add_card(data)
            return web.HTTPCreated(content_type=encoder.content_type, body=encoder.encode(card))
        except MultipleInvalid as e:
            raise web_exceptions.HTTPBadRequest(text=str(e))
        except ItemNotFoundException as e:
            raise web_exceptions.HTTPNotFound(text=str(e))

    async def client_list(self, request):
        """
        ---
        description: Запрос для получения списка клиентов
        tags:
        - Clients
        produces:
        - application/json
        - application/xml
        parameters:
        - name: offset
          in: query
          description: Pagination offset
          required: false
          type: integer
        - name: limit
          in: query
          description: Pagination limit
          required: false
          type: integer
        responses:
            "200":
                description: успех. Возвращает список клиентов
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        encoder = self.__choose_encoder(request)
        offset, limit = self.__paginate(request)
        clients, count = await self.__client_model.all_clients(offset, limit)
        return web.Response(content_type=encoder.content_type, body=encoder.encode(clients), headers={"X-Total": str(count)})

    async def add_client(self, request):
        """
        ---
        description: Запрос для добавления нового клиента
        tags:
        - Clients
        produces:
        - application/json
        - application/xml
        parameters:
        - name: card
          in: body
          description: данные нового клиента
          required: true
          schema:
            type: object
            properties:
              name:
                type: string
                description: имя клиента
        responses:
            "200":
                description: успех. Возвращает данные нового клиента
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        encoder = self.__choose_encoder(request)
        data = await self.__decode_post(request)
        try:
            client = await self.__client_model.add_client(data)
            return web.HTTPCreated(content_type=encoder.content_type, body=encoder.encode(client))
        except MultipleInvalid as e:
            raise web_exceptions.HTTPBadRequest(text=str(e))

    async def client_balance(self, request):
        """
        ---
        description: Запрос для получения баланса клиента
        tags:
        - Clients
        produces:
        - application/json
        - application/xml
        parameters:
        - name: id
          in: path
          description: идентификатор клиента
          required: false
          type: integer
        responses:
            "200":
                description: успех. Возвращает данные нового клиента
            "404":
                description: ошибка. Клиент не найден
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        client_id = int(request.match_info.get('id'))
        encoder = self.__choose_encoder(request)
        client = await self.__client_model.client_balance(client_id)
        return web.Response(content_type=encoder.content_type, body=encoder.encode(client))

    async def change_card(self, request):
        """
        ---
        description: Запрос для изменение данных по карте
        tags:
        - Cards
        produces:
        - application/json
        - application/xml
        parameters:
        - name: id
          in: path
          description: идентификатор карты
          required: true
          type: integer
        - name: card
          in: body
          description: данные карты
          required: true
          schema:
            type: object
            properties:
              owner_id:
                type: integer
                description: идентификатор владельца карты
              payment_system:
                type: string
                description: платежная система
              currency:
                type: string
                description: валюта карты
              balance:
                type: float
                description: баланс карты
        responses:
            "200":
                description: успех. Возвращает измененные данные карты
            "400":
                description: ошибка клиента. Указаны неверные данные карты
            "404":
                description: ошибка. Карта не найдена
            "406":
                description: ошибка клиента. Указан неверный Accept
        """
        card_id = int(request.match_info.get('id'))
        encoder = self.__choose_encoder(request)
        data = await self.__decode_post(request)
        try:
            card = await self.__client_model.change_card(card_id, data)
            return web.Response(content_type=encoder.content_type, body=encoder.encode(card))
        except MultipleInvalid as e:
            raise web_exceptions.HTTPBadRequest(text=str(e))

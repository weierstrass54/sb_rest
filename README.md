## SB_REST

### Docker
`docker build -t sb_rest .`

`docker run --name sb_rest -p 8081:8081 --rm sb_rest:latest`

### Настройки
Настройки через переменные окружения:
- `SERVER_HOST` (по умолчанию 0.0.0.0)
- `SERVER_PORT` (по умолчанию 8081)
- `DB_DSN` (по умолчанию postgres://sb_rest:sb_rest@127.0.0.1:5432/sb_rest)

После запуска интерактивная документация доступна по пути `/v1/docs`

"""Точка входа приложения: запуск через `python -m app`."""
import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="vibe_mail API")
    parser.add_argument("--host", default="127.0.0.1", help="хост для привязки")
    parser.add_argument("--port", type=int, default=8000, help="порт")
    parser.add_argument("--reload", action="store_true", help="автоперезагрузка при изменениях")
    args = parser.parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

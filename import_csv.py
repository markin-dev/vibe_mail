#!/usr/bin/env python3
"""Собирает секцию recipients для config.yaml из CSV вида: имя,email,файл.

Строки с одинаковым email объединяются в одного получателя — одно письмо
со всеми его вложениями. Строки без email пропускаются и выводятся списком.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from send_mail import EMAIL_RE  # noqa: E402  (переиспользуем проверку адреса)

RECIPIENTS_RE = re.compile(r"^recipients\s*:", re.MULTILINE)


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path", help="CSV: имя,email,файл (без заголовка)")
    ap.add_argument("--config", default="config.yaml", help="конфиг, куда вписать recipients")
    ap.add_argument("--attachments-dir", default=None,
                    help="папка с вложениями для проверки наличия файлов "
                         "(по умолчанию attachments_dir рядом с конфигом)")
    ap.add_argument("--dry-run", action="store_true", help="показать блок, не трогая конфиг")
    ap.add_argument("--encoding", default="utf-8-sig", help="кодировка CSV")
    return ap.parse_args()


def read_rows(path, encoding):
    """Возвращает (recipients, skipped, problems)."""
    grouped = {}        # email.lower() -> {"email": ..., "files": [...]}
    skipped = []        # (номер строки, имя, файл)
    problems = []

    with open(path, newline="", encoding=encoding) as fh:
        for lineno, row in enumerate(csv.reader(fh), start=1):
            row = [c.strip() for c in row]
            if not any(row):
                continue
            if len(row) < 3:
                problems.append(f"строка {lineno}: ожидалось 3 колонки, получено {len(row)}: {row}")
                continue
            name, email, filename = row[0], row[1], row[2]
            if not filename:
                problems.append(f"строка {lineno}: не указан файл вложения")
                continue
            if not email:
                skipped.append((lineno, name, filename))
                continue
            if not EMAIL_RE.match(email):
                problems.append(f"строка {lineno}: некорректный адрес {email!r}")
                continue

            entry = grouped.setdefault(email.lower(), {"email": email, "files": []})
            if filename in entry["files"]:
                problems.append(f"строка {lineno}: файл {filename} уже добавлен для {email}")
                continue
            entry["files"].append(filename)

    return list(grouped.values()), skipped, problems


def render(recipients):
    """Получатели разделяются пустой строкой — так блок легче читать и править."""
    blocks = []
    for r in recipients:
        lines = [f"  - email: {r['email']}", "    attachments:"]
        lines += [f"      - {f}" for f in r["files"]]
        blocks.append("\n".join(lines))
    return "recipients:\n" + "\n\n".join(blocks) + "\n"


def splice(config_path, block):
    """Заменяет секцию recipients в конфиге, сохраняя всё, что выше неё."""
    text = config_path.read_text(encoding="utf-8")
    match = RECIPIENTS_RE.search(text)
    if match:
        head = text[: match.start()]
    else:
        head = text if text.endswith("\n") else text + "\n"
        head += "\n"
    backup = config_path.with_suffix(config_path.suffix + ".bak")
    backup.write_text(text, encoding="utf-8")
    config_path.write_text(head + block, encoding="utf-8")
    return backup


def main():
    args = parse_args()
    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        sys.exit(f"CSV не найден: {csv_path}")

    recipients, skipped, problems = read_rows(csv_path, args.encoding)

    if problems:
        print("Проблемы в CSV:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
    if skipped:
        print(f"\nПропущено без email ({len(skipped)}):", file=sys.stderr)
        for lineno, name, filename in skipped:
            print(f"  - строка {lineno}: {name} ({filename})", file=sys.stderr)
    if not recipients:
        sys.exit("\nНи одного получателя с адресом — конфиг не тронут.")

    total_files = sum(len(r["files"]) for r in recipients)
    multi = [r for r in recipients if len(r["files"]) > 1]
    print(
        f"\nПолучателей: {len(recipients)}, вложений: {total_files}, "
        f"из них с несколькими файлами: {len(multi)}",
        file=sys.stderr,
    )
    for r in multi:
        print(f"  - {r['email']}: {len(r['files'])} файла", file=sys.stderr)

    config_path = Path(args.config)
    att_dir = Path(args.attachments_dir) if args.attachments_dir else config_path.resolve().parent / "attachments"
    missing = [f for r in recipients for f in r["files"] if not (att_dir / f).is_file()]
    if missing:
        print(
            f"\nВнимание: {len(missing)} из {total_files} файлов пока нет в {att_dir} "
            f"(например {missing[0]}). Положите их до отправки — send_mail.py всё равно проверит.",
            file=sys.stderr,
        )

    block = render(recipients)
    if args.dry_run:
        print(block, end="")
        return 0
    if not config_path.is_file():
        sys.exit(f"\nКонфиг не найден: {config_path} (создайте из config.example.yaml)")
    backup = splice(config_path, block)
    print(f"\nСекция recipients в {config_path} перезаписана. Резервная копия: {backup}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

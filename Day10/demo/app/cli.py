import json
import os
import sqlite3
from pathlib import Path

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from .config import ROOT
from .db import get_db
from .masking import rule_values
from .validation import ApiError, email, password, text


def register(app):
    @app.cli.command("init-db")
    def init_db():
        """Create a new database, refusing to overwrite any existing file."""
        target = Path(current_app.config["DATABASE_PATH"])
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise click.ClickException("DB 파일이 이미 있습니다. 기존 데이터를 보존하기 위해 초기화를 거부합니다.") from None
        os.close(descriptor)
        connection = sqlite3.connect(target)
        try:
            connection.executescript((ROOT / "database-schema.sql").read_text(encoding="utf-8-sig"))
        except Exception:
            connection.close()
            target.unlink()
            raise
        finally:
            connection.close()
        click.echo(f"새 데이터베이스를 생성했습니다: {target}")

    @app.cli.command("create-admin")
    @click.option("--email", "address", prompt="관리자 이메일")
    @click.option("--nickname", prompt="관리자 닉네임")
    def create_admin(address, nickname):
        """Create a private administrator with an interactively entered password."""
        try:
            address = email(address)
            nickname = text(nickname, "닉네임", 30, trim=True)
            supplied = password(click.prompt("비밀번호", hide_input=True, confirmation_prompt=True))
            digest = generate_password_hash(supplied)
            db = get_db()
            with db:
                db.execute("INSERT INTO users(email,nickname,password_hash,role) VALUES (?,?,?,'ADMIN')",
                           (address, nickname, digest))
        except ApiError as error:
            raise click.ClickException(error.message) from None
        except sqlite3.IntegrityError:
            raise click.ClickException("이미 존재하는 이메일입니다. 기존 회원의 역할은 변경하지 않았습니다.") from None
        click.echo("관리자를 생성했습니다. 비밀번호는 출력하거나 원문으로 저장하지 않습니다.")

    @app.cli.command("import-rules")
    @click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
    def import_rules(source):
        """Import a local JSON list. Existing keywords are preserved."""
        try:
            if source.stat().st_size > 1024 * 1024:
                raise ApiError("규칙 파일은 1 MiB 이하여야 합니다.")
            records = json.loads(source.read_text(encoding="utf-8-sig"))
            if not isinstance(records, list) or len(records) > 500:
                raise ApiError("규칙은 최대 500개의 객체를 담은 배열이어야 합니다.")
            values = []
            for record in records:
                if not isinstance(record, dict) or set(record) - {"keyword", "replacement", "source_url", "source_checked_at"}:
                    raise ApiError("규칙 파일의 항목을 확인해주세요.")
                values.append(rule_values(record))
            db = get_db()
            count = 0
            with db:
                for value in values:
                    result = db.execute(
                        "INSERT INTO masking_rules(keyword,replacement,source_url,source_checked_at) VALUES (?,?,?,?) ON CONFLICT(keyword) DO NOTHING",
                        value,
                    )
                    count += result.rowcount
        except (json.JSONDecodeError, UnicodeError):
            raise click.ClickException("UTF-8 JSON 파일 형식을 확인해주세요.") from None
        except ApiError as error:
            raise click.ClickException(error.message) from None
        click.echo(f"규칙 {count}개 추가, {len(records) - count}개 중복 유지. 기존 규칙은 변경하지 않았습니다.")

    @app.cli.command("backup-db")
    @click.argument("destination", type=click.Path(path_type=Path))
    def backup_db(destination):
        """Make a consistent SQLite backup in a private, new file."""
        target = destination.resolve()
        static = (ROOT / "app" / "static").resolve()
        if target == Path(current_app.config["DATABASE_PATH"]) or static == target or static in target.parents:
            raise click.ClickException("원본 DB나 정적 파일 경로에는 백업할 수 없습니다.")
        source_db = get_db()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise click.ClickException("백업 파일이 이미 있습니다. 다른 파일명을 사용해주세요.") from None
        os.close(descriptor)
        backup = sqlite3.connect(target)
        try:
            source_db.backup(backup)
        except Exception:
            backup.close()
            target.unlink()
            raise
        finally:
            backup.close()
        click.echo(f"일관된 DB 백업을 생성했습니다: {target}")


"""Create private environment configuration once, without displaying the key."""
import argparse
import os
from pathlib import Path
import secrets


def main():
    parser = argparse.ArgumentParser(description="안전한 .env 설정 파일을 새로 만듭니다.")
    parser.add_argument("--production", action="store_true", help="HTTPS 배포 설정")
    parser.add_argument("--database", type=Path, help="DB의 절대 경로 (기본: 프로젝트/instance/note-demo.sqlite3)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    database = args.database or root / "instance" / "note-demo.sqlite3"
    if not database.is_absolute() or any(c in str(database) for c in ('\n', '\r', '"', '$')):
        parser.error("DB는 줄바꿈·따옴표·달러 기호가 없는 절대 경로로 지정해주세요.")
    database = database.resolve()
    static = (root / "app" / "static").resolve()
    if static == database or static in database.parents:
        parser.error("DB는 app/static 밖에 저장해야 합니다.")
    content = (
        f"APP_ENV={'production' if args.production else 'development'}\n"
        f"SECRET_KEY={secrets.token_hex(32)}\n"
        f'DATABASE_PATH="{database.as_posix()}"\n'
    )
    try:
        descriptor = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.exit(1, ".env가 이미 있습니다. 기존 키를 보존했습니다. 변경이 필요하면 파일을 직접 편집하세요.\n")
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(".env를 생성했습니다. 비밀키는 출력하지 않았습니다. 다음으로 init-db를 실행하세요.")


if __name__ == "__main__":
    main()


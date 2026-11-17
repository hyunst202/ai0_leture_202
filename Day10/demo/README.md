# note-demo

Flask + SQLite로 구현한 작은 게시판입니다. 제목·본문 글쓰기, 10개씩 목록 조회, 같은 화면의 상세·댓글, 본인 글 수정·삭제, 관리자 키워드 마스킹을 제공합니다.

**작성·공식 자료 확인: 2026-10-28 (Asia/Seoul).** PythonAnywhere 무료 계정의 일반 WSGI 배포를 기준으로 안내합니다. 로컬 구현과 테스트를 진행했으며 실제 PythonAnywhere 계정 배포는 아직 수행하지 않았습니다.

## 1. 구현 범위

- 이메일·닉네임·개인별 비밀번호로 가입하고 로그인·로그아웃합니다. 비밀번호 원문 대신 Werkzeug 해시를 저장합니다.
- 방문자는 글·댓글을 읽고, 로그인 사용자는 글·댓글을 작성합니다. 글 수정·삭제와 편집용 원문 조회는 작성자에게만 허용합니다.
- 목록·상세·댓글에 공통 마스킹을 적용합니다. 관리자는 키워드를 추가·삭제하며 기존 글에도 현재 규칙이 적용됩니다.
- 화면은 게시판·계정·규칙 관리의 세 영역이며, 상세와 작성·수정 폼은 같은 영역을 재사용합니다.
- 비밀번호 찾기는 **실제 메일 발송·비밀번호 변경이 없는 목업**입니다. SNS 로그인·이메일 소유 확인·첨부파일·검색·대댓글은 구현하지 않았습니다.

## 2. Windows 로컬 실행

PowerShell에서 프로젝트 폴더를 엽니다. Python 3.12를 권장하며, 설치된 Python을 가리키는 실행 명령을 사용하세요.

```powershell
cd C:\AI4\Day10\demo
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe scripts\configure.py
.\.venv\Scripts\python.exe -m flask --app app:create_app init-db
.\.venv\Scripts\python.exe -m flask --app app:create_app import-rules seed\masking-rules.json
.\.venv\Scripts\python.exe -m flask --app app:create_app create-admin
.\.venv\Scripts\python.exe -m flask --app app:create_app run --host 127.0.0.1 --port 5000
```

브라우저에서 [로컬 게시판](http://127.0.0.1:5000)을 엽니다. 일반 회원은 화면의 회원가입으로 만들고, 관리자는 `create-admin`의 이메일·닉네임·비밀번호 입력으로 생성합니다. 비밀번호는 콘솔에 표시하지 않으며 공개된 기본 관리자 계정은 없습니다.

이 작업 폴더에는 `.venv`, 로컬 `.env`, DB와 초기 규칙이 이미 준비되어 있습니다. **이미 존재하는 가상환경 생성·configure·init-db는 생략**하고 필요하면 관리자 생성과 서버 실행부터 진행하세요. `configure.py`와 `init-db`는 기존 파일을 덮어쓰지 않습니다.

현재 PC처럼 `py`/`python`이 PATH에 없는 경우에는 설치한 Python의 전체 경로를 사용합니다. 이 작업에서 가상환경을 만든 실행 파일은 다음과 같습니다. 다른 PC에서는 자신의 경로로 바꾸세요.

```powershell
& 'C:\Users\Playdata\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
```

PowerShell 활성화 스크립트는 필요하지 않습니다. 명령마다 `.venv\Scripts\python.exe`를 직접 사용하므로 실행 정책을 변경할 필요도 없습니다.

## 3. 설정과 데이터 유지

`scripts/configure.py`는 프로젝트 루트에 `.env`를 한 번 생성하고 충분한 길이의 무작위 비밀키를 파일에만 저장합니다. 값은 출력하지 않습니다. 기존 설정을 바꾸려면 `.env`를 직접 편집하세요.

| 키 | 로컬 | PythonAnywhere |
| --- | --- | --- |
| APP_ENV | development | production |
| SECRET_KEY | 생성된 비밀값 유지 | 배포 서버에서 새로 생성하고 Reload 때 유지 |
| DATABASE_PATH | 생성된 프로젝트/instance 절대 경로 | `/home/계정명/note-demo/instance/note-demo.sqlite3` 등 절대 경로 |

서버는 콘솔·WSGI 모두 프로젝트 루트의 같은 `.env`를 읽습니다. 프로세스에 이미 설정된 환경변수는 `.env`보다 우선합니다. 배포에서 비밀키가 없거나 너무 짧거나 DB 경로가 상대 경로이면 시작을 거부합니다.

회원·글·댓글·규칙은 SQLite 파일에 유지됩니다. 로그인의 기본 유효기간은 8시간이며 **같은 계정의 가장 최근 로그인만 유효**합니다. 새 로그인이나 로그아웃은 DB의 `auth_version`을 올려 이전 쿠키를 무효화합니다. 같은 키와 DB를 사용하는 Web Reload는 유효한 로그인을 유지합니다.

`.env`, `instance/`, 가상환경, 백업은 버전 관리·배포 압축에서 제외합니다. DB는 공개 정적 파일 경로 밖에 둡니다. 서버 시작·Reload는 스키마·규칙·관리자를 자동 생성하지 않습니다.

## 4. 테스트

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

테스트는 임시 DB를 사용하므로 로컬 게시판의 글이나 관리자를 삭제하지 않습니다. 비밀번호 해시·입력 검증, 계정 전환·쿠키 무효화·Reload, CSRF, 사용자 간 권한, 페이징, 댓글 관계, 마스킹 변경, CLI·DB 백업·WSGI import와 비공개 파일 경로를 검증합니다. 실행 결과는 [검증 기록](docs/verification.md)에 기록합니다.

## 5. PythonAnywhere 무료 계정에 배포

### 무료 계정에서 확인한 조건

2026-10-28 공식 안내 기준으로 무료 계정은 웹 앱 1개·워커 1개·디스크 512 MiB·웹 앱 만료 1개월을 제공합니다. 2026-01-15 이전 계정(EU는 01-08 이전)은 일부 기능이 다를 수 있지만, 이 앱은 무료 MySQL·예약 작업을 전제로 하지 않습니다. [공식 무료 계정 기능](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)

SQLite는 무료 계정에서도 사용할 수 있으나 PythonAnywhere는 클라우드 파일 시스템의 SQLite를 고부하 운영 DB로 권장하지 않습니다. 이 앱은 작은 데모·저트래픽 사용을 대상으로 합니다. [공식 DB 안내](https://help.pythonanywhere.com/pages/KindsOfDatabases)

### 5-1. 비밀정보 없는 소스 압축 준비

로컬에서 다음을 실행합니다.

```powershell
.\.venv\Scripts\python.exe scripts\package.py
```

생성되는 `dist/note-demo.zip`에는 소스·설계·규칙·문서만 들어갑니다. 로컬 `.env`, SQLite, `.venv`, 백업, 캐시는 포함하지 않습니다. 프로젝트 폴더 전체를 직접 압축해 로컬 비밀값이나 Windows DB 경로를 업로드하지 마세요.

### 5-2. 파일 업로드와 가상환경

PythonAnywhere의 **Files**에서 소스 ZIP을 자신의 홈 디렉터리에 업로드합니다. **Consoles → Bash**에서 다음을 실행합니다. `YOUR_USERNAME`은 실제 계정명으로 바꾸세요. ZIP을 다시 풀 때 기존 `.env`와 DB는 포함되어 있지 않으므로 보존됩니다.

```bash
mkdir -p /home/YOUR_USERNAME/note-demo
cd /home/YOUR_USERNAME/note-demo
unzip -o /home/YOUR_USERNAME/note-demo.zip
mkvirtualenv --python=/usr/bin/python3.12 note-demo
python -m pip install -r requirements.txt
```

`/usr/bin/python3.12`가 제공되는지 먼저 확인하고 **가상환경과 Web 앱의 Python 버전을 반드시 일치**시킵니다. 계정 이미지가 다르면 Web 탭에서 제공하는 버전으로 조정하세요. 이미 만든 가상환경은 `workon note-demo`로 재사용합니다. 배포에는 테스트 전용 의존성을 설치할 필요가 없습니다. [공식 Flask 배포·가상환경 안내](https://help.pythonanywhere.com/pages/Flask/)

### 5-3. 배포 설정·DB·관리자 준비

같은 Bash 콘솔과 프로젝트 폴더에서 최초 배포에만 실행합니다.

```bash
python scripts/configure.py --production
python -m flask --app app:create_app init-db
python -m flask --app app:create_app import-rules seed/masking-rules.json
python -m flask --app app:create_app create-admin
```

이 스크립트가 생성한 `.env`에는 Linux의 절대 DB 경로와 배포 비밀키가 들어갑니다. 비밀키를 웹페이지·저장소·질문 게시글에 붙여 넣지 마세요. 이미 `.env`가 있다면 생성 스크립트는 거부하므로 `APP_ENV=production`과 Linux DB 절대 경로를 직접 확인하세요. 재배포 때 `init-db`를 반복하지 않습니다.

현재 스키마 버전은 2입니다. 예전 버전 DB를 발견하면 앱이 503으로 거부합니다. 기존 DB를 삭제하거나 NULL 비밀번호를 공통 암호로 채우지 말고, 백업 후 별도 데이터 이전을 준비하세요.

### 5-4. Web 탭의 WSGI 설정

1. **Web → Add a new web app → Manual configuration**을 선택합니다.
2. 가상환경과 같은 Python 버전을 선택합니다.
3. **Virtualenv**에 `/home/YOUR_USERNAME/.virtualenvs/note-demo`를 지정합니다.
4. **WSGI configuration file** 링크를 열어 기존 예제 코드를 정리하고 다음을 저장합니다.

```python
import sys

project_dir = '/home/YOUR_USERNAME/note-demo'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from app import create_app
application = create_app()
```

앱의 `create_app()`이 프로젝트 `.env`를 절대 경로로 로드하므로 콘솔에서만 `export`한 값에 의존하지 않습니다. 루트의 `wsgi.py`도 같은 팩토리를 사용하며 로컬 import 검증용으로 제공됩니다. Web 탭에서 실제로 읽는 것은 해당 탭의 WSGI 설정 파일입니다. [Flask WSGI 안내](https://help.pythonanywhere.com/pages/Flask/), [환경변수와 WSGI 안내](https://help.pythonanywhere.com/pages/EnvironmentVariables)

### 5-5. 정적 파일·HTTPS·Reload

**Static files**에 아래 한 항목만 추가합니다.

| URL | Directory |
| --- | --- |
| `/static/` | `/home/YOUR_USERNAME/note-demo/app/static` |

프로젝트 루트, `instance`, `.env`, 백업 디렉터리는 매핑하지 않습니다. HTML과 API는 Flask가 처리합니다. [공식 정적 파일 매핑](https://help.pythonanywhere.com/pages/StaticFiles/)

계정에 제공된 기본 도메인의 HTTPS로 접속하고 **Force HTTPS**를 켭니다. 기본 `pythonanywhere.com` 도메인의 인증서는 플랫폼에서 제공하므로 별도 구매가 필요하지 않습니다. EU 계정이면 Web 탭에 표시된 실제 EU 도메인을 사용하세요. 배포 설정에서는 Secure·HttpOnly·SameSite=Lax 쿠키와 DEBUG=False가 적용됩니다. [HTTPS 안내](https://help.pythonanywhere.com/pages/HTTPSSetup/)

마지막으로 **Reload**를 누르고 공개 HTTPS 주소를 확인합니다. PythonAnywhere 콘솔에서 `flask run`, `app.run()`, Uvicorn 또는 Gunicorn을 계속 띄워 공개 서버로 사용하지 않습니다. 일반 Web 앱은 플랫폼의 WSGI가 실행합니다. [공식 Flask 실행 방식](https://help.pythonanywhere.com/pages/Flask/)

### 5-6. 배포 후 확인

- 첫 화면·CSS·JavaScript가 로드되고 일반 회원가입·로그인이 동작하는지 확인합니다.
- 글·댓글 작성, 본인 글 수정·삭제, 관리자 규칙 추가·삭제를 확인합니다.
- 다른 브라우저 계정으로 남의 글 수정과 관리자 API가 거부되는지 확인합니다.
- Reload 후 DB·규칙·유효한 로그인이 유지되는지 확인합니다.
- `/.env`, `/instance/note-demo.sqlite3`, `/database-schema.sql`이 404인지 확인합니다.
- Web 탭의 오류 로그·만료일·연장 동작을 확인합니다. 무료 웹 앱은 만료 전에 수동 연장하고, 가상환경·DB·백업을 합친 디스크 사용량을 관리하세요.

## 6. 규칙·백업·업데이트

초기 규칙의 출처·확인일·선정 기준과 라이선스는 [초기 규칙 설명](docs/masking-sources.md)에 있습니다. 배포 서버는 인터넷 검색·자동 갱신을 하지 않으므로 무료 계정의 외부 통신 허용 목록에 의존하지 않습니다. [외부 통신 정책](https://help.pythonanywhere.com/pages/RequestingAllowlistAdditions)

규칙은 관리자 화면에서 관리합니다. 초기 파일을 **명시적으로 다시 반입하면** 그 사이 삭제한 키워드가 다시 추가될 수 있습니다. Reload 자체는 반입을 수행하지 않습니다.

백업 예시입니다. PowerShell에서는 `python` 대신 `.\.venv\Scripts\python.exe`를 사용하고, Linux에서는 가상환경을 활성화한 `python`을 사용합니다.

```bash
python -m flask --app app:create_app backup-db private-backups/note-demo-20261028.sqlite3
```

SQLite backup API로 일관된 사본을 생성하며 기존 파일·공개 정적 경로·원본 DB로의 덮어쓰기는 거부합니다. 백업은 Files에서 수동 다운로드하고 오래된 사본은 별도로 관리하세요. **실행 중인 DB를 단순 복사하여 백업하지 않습니다.**

복구는 서비스 쓰기를 중단한 유지보수 상태에서 현재 DB도 별도 보관한 뒤 확인한 백업으로 교체하고 Reload합니다. `.env`의 키와 DB 경로를 함께 확인하세요. 업데이트는 소스 압축 업로드·압축 해제·필요 시 의존성 갱신·Reload 순서이며 `.env`와 DB를 덮어쓰거나 `init-db`를 실행하지 않습니다.

## 7. 문제 해결

| 현상 | 확인할 내용 |
| --- | --- |
| `py` 또는 `python`을 찾지 못함 | Python 전체 경로로 가상환경을 만들고 `.venv` 실행 파일을 직접 사용 |
| `.env가 이미 있습니다` / 초기화 거부 | 데이터 보호 동작. 기존 파일을 유지하고 생성 단계 생략 |
| SECRET_KEY 오류 | configure 실행 여부, 실제 Web 앱이 읽는 프로젝트 경로와 환경변수 우선순위 |
| DB 관련 503 | 절대 경로, 파일·디렉터리 쓰기 권한, init-db 실행 여부, 스키마 버전 확인 |
| 배포 502/504 | Web 오류 로그, 가상환경 버전, WSGI import, import 중 app.run() 여부 |
| 로그인했는데 유지되지 않음 | HTTPS·Secure 쿠키, .env 비밀키의 유지, 같은 계정의 다른 로그인 여부 |
| CSRF 400 | 페이지 새로고침 후 재시도. 개발 중 CSRF 검증을 끄지 않음 |
| CSS/JS 404 | `/static/` 매핑의 절대 경로와 Reload, 브라우저 새로고침 |
| 비밀번호 찾기 메일이 오지 않음 | 현재는 실제 발송·재설정이 없는 목업 |

전체 ERD와 테이블 정의는 [실행 프롬프트](agent-prompt.md), 초기 DDL은 [database-schema.sql](database-schema.sql), 구현 순서는 [plan.md](plan.md)를 참고하세요.


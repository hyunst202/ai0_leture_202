# PythonAnywhere 배포 안내

공식 자료 확인일: 2026-10-28 (Asia/Seoul).

배포 단계는 중복된 명령이 서로 달라지지 않도록 [README의 PythonAnywhere 배포 절차](../README.md#5-pythonanywhere-무료-계정에-배포)를 단일 기준으로 관리합니다.

1. `scripts/package.py`로 비밀정보·DB·가상환경을 제외한 ZIP 생성.
2. Files 업로드와 Bash 압축 해제, Web 앱과 같은 Python의 가상환경 준비.
3. 서버에서 `configure.py --production`, 최초 `init-db`, `import-rules`, `create-admin` 실행.
4. 일반 Web 앱의 Manual configuration·Virtualenv·WSGI `application` 설정.
5. `/static/`만 공개 폴더에 매핑하고 HTTPS·Force HTTPS 확인.
6. Reload 후 실제 도메인에서 기능·권한·데이터 유지 확인.

공식 근거: [Flask WSGI](https://help.pythonanywhere.com/pages/Flask/), [무료 기능](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/), [환경변수](https://help.pythonanywhere.com/pages/EnvironmentVariables), [정적 매핑](https://help.pythonanywhere.com/pages/StaticFiles/), [HTTPS](https://help.pythonanywhere.com/pages/HTTPSSetup/).

실제 PythonAnywhere 계정에 접속하거나 배포를 수행한 상태는 아닙니다. 검증된 로컬 동작과 실제 배포 확인을 구분해 [검증 기록](verification.md)에 남깁니다.


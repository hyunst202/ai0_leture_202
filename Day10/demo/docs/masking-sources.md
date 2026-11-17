# 초기 마스킹 규칙의 출처

확인일: **2026-10-28 (Asia/Seoul)**

- 원자료: [LDNOOBW / List of Dirty, Naughty, Obscene, and Otherwise Bad Words — 한국어 목록](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/blob/master/ko)
- 저작자·관리 주체: LDNOOBW 저장소 기여자. 자료는 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)으로 공개되어 있다. [저장소 라이선스](https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/blob/master/LICENSE)
- 변경 내용: 전체 목록에서 직접적인 모욕·욕설 5개만 선별하고 JSON 형식으로 변환했다. 원자료 전체를 배포하지 않는다. 중립적 용례가 많은 단어, 집단 명칭, 정체성 표현은 자동 반입하지 않았다.
- 구현 파일: `seed/masking-rules.json`. 항목마다 출처 URL과 확인일이 포함된다. `source_checked_at`은 확인일을 UTC 자정으로 정규화한 날짜 표기이며 원자료의 게시일·실제 확인 시분초를 뜻하지 않는다.

이는 확인일에 접근 가능한 공개 목록을 검토한 초기 정책이다. 최근 신조어를 모두 포함하거나 최신 유행을 반영한 사전이라고 보장하지 않는다. 띄어쓰기·문자 치환·문맥을 이용한 우회는 탐지하지 못할 수 있으며, 인용·비판·교육 목적의 사용도 같은 문자열이면 가려질 수 있다.

키워드는 NFC 정규화 후 문자 그대로 매칭한다. 영문 대소문자만 무시하며, 긴 키워드를 먼저 적용하고 치환 결과는 다시 마스킹하지 않는다. DB에는 원문을 보관하므로 규칙을 삭제하면 읽기 결과에도 즉시 반영된다.

조사는 개발 환경에서만 수행했다. 배포 서버는 외부 목록을 다운로드하거나 자동 갱신하지 않는다. 초기 반입은 `import-rules` 명령으로 명시적으로 수행하고 이후에는 관리자가 추가·삭제한다. 같은 파일을 다시 반입하면 기존 키워드는 덮어쓰지 않는다. 삭제했던 키워드를 **다시 명시적으로 반입하면** 추가될 수 있지만, 서버 Reload만으로 추가되지는 않는다.


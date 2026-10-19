"""채팅 메시지에서 금지 단어를 별표로 가리는 간단한 예제."""

import re


def mask_bad_words(chat_message: str, bad_words: list[str]) -> str:
    """메시지 안의 금지 단어를 단어 길이만큼 '*'로 바꿔 반환한다."""
    # 빈 단어는 어디에나 일치할 수 있으므로 제외하고, 긴 단어부터 검사한다.
    words = sorted((word for word in bad_words if word), key=len, reverse=True)

    # 금지 단어가 없으면 정규식을 만들지 않고 원래 메시지를 그대로 돌려준다.
    if not words:
        return chat_message

    # 단어 안의 정규식 기호는 특별한 의미가 없도록 이스케이프하고 하나의 패턴으로 묶는다.
    pattern = re.compile("|".join(re.escape(word) for word in words), re.IGNORECASE)

    # 일치한 부분의 길이만큼 별표를 만들어 원래 위치에 넣는다.
    return pattern.sub(lambda match: "*" * len(match.group()), chat_message)


def run_assertions() -> None:
    """일반 입력과 경계 사례를 assert로 검증한다."""
    # 금지 단어 하나와 여러 번 반복된 단어를 확인한다.
    assert mask_bad_words("너는 바보야", ["바보"]) == "너는 **야"
    assert mask_bad_words("바보, 바보!", ["바보"]) == "**, **!"

    # 영어 대소문자를 구분하지 않으며 문장 부호와 공백은 그대로 유지한다.
    assert mask_bad_words("BAD bad BaD!", ["bad"]) == "*** *** ***!"
    assert mask_bad_words("hello, WORLD.", ["world"]) == "hello, *****."

    # 여러 단어, 겹치는 단어, 정규식 기호가 포함된 단어를 확인한다.
    assert mask_bad_words("나쁜말과 바보", ["나쁜말", "바보"]) == "***과 **"
    assert mask_bad_words("foobar", ["foo", "foobar"]) == "******"
    assert mask_bad_words("a.b aXb", ["a.b"]) == "*** aXb"

    # 빈 금지어 목록과 빈 금지 단어는 메시지를 바꾸지 않는다.
    assert mask_bad_words("그대로 유지", []) == "그대로 유지"
    assert mask_bad_words("그대로 유지", [""]) == "그대로 유지"
    assert mask_bad_words("", ["바보"]) == ""


if __name__ == "__main__":
    run_assertions()
    print("모든 assert 검증을 통과했습니다.")

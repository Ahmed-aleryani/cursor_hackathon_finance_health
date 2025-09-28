import re

_whitespace = re.compile(r"\s+")
_non_alnum = re.compile(r"[^0-9a-zA-Z\s]+")


def clean_description(text: str) -> str:
    if text is None:
        return ""
    text = text.strip()
    text = _whitespace.sub(" ", text)
    return text


def normalized_key(text: str) -> str:
    if text is None:
        return ""
    text = text.lower()
    text = _non_alnum.sub(" ", text)
    text = _whitespace.sub(" ", text)
    return text.strip()

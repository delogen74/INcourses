import bleach


def html_to_plain_text(content: str) -> str:
    return bleach.clean(content or '', tags=[], strip=True)

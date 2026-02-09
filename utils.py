def escape_md(text: str) -> str:
    """Экранирование спецсимволов для Markdown"""
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

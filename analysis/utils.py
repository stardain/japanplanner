import re

def decode_unicode(text):
    if not isinstance(text, str):
        return text
    return re.sub(
        r'\\u([0-9a-fA-F]{4})',
        lambda m: chr(int(m.group(1), 16)),
        text
    )

def clean_whole_dict(data: dict) -> dict:
    """Clean all string values in a dict"""
    return {
        key: decode_unicode(value) if isinstance(value, str) else value
        for key, value in data.items()
    }

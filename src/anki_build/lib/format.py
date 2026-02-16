from markdown import markdown

def format_text(text):
    return text

def format_markdown(text):
    if not text: return ''
    if not isinstance(text, str):
        text = str(text)
    return markdown(text)

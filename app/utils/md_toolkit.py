from markdown import markdown
from bs4 import BeautifulSoup

def md_to_text(md: str) -> str:
    html = markdown(md)  # Convert Markdown to HTML
    return BeautifulSoup(html, "html.parser").get_text().strip()
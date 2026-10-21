"""Conversão entre o texto simples digitado no anúncio e o HTML guardado em Post.content.

Regras do texto simples:
- uma linha em branco separa parágrafos; quebras de linha simples são mantidas;
- linhas que começam com "- " viram itens de lista;
- o link de uma imagem (.jpg, .jpeg, .png, .gif, .webp) sozinho numa linha vira <img>.
"""
import re
from html import escape
from html.parser import HTMLParser

IMAGE_RE = re.compile(r'^https?://\S+\.(?:jpe?g|png|gif|webp)(?:\?\S*)?$', re.IGNORECASE)


def _kind(line):
    if IMAGE_RE.match(line):
        return 'img'
    if line.startswith('- '):
        return 'li'
    return 'p'


def _render(kind, lines):
    if kind == 'img':
        return ''.join(f'<p><img src="{escape(url)}" alt=""></p>' for url in lines)
    if kind == 'li':
        items = ''.join(f'<li>{escape(line[2:].strip())}</li>' for line in lines)
        return f'<ul>{items}</ul>'
    return '<p>' + '<br>'.join(escape(line) for line in lines) + '</p>'


def text_to_html(text):
    """Converte o texto do usuário em HTML, escapando qualquer tag digitada."""
    html = []
    for block in re.split(r'\n\s*\n', text.replace('\r\n', '\n').strip()):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        kind, group = None, []
        for line in lines:
            if _kind(line) != kind and group:
                html.append(_render(kind, group))
                group = []
            kind = _kind(line)
            group.append(line)
        if group:
            html.append(_render(kind, group))
    return '\n'.join(html)


class _TextExtractor(HTMLParser):
    BLOCKS = {'p', 'div', 'ul', 'ol', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.first_cell = True

    def _newline(self, count=1):
        self.parts.append('\n' * count)

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKS:
            self._newline(2)
        elif tag == 'br':
            self._newline()
        elif tag == 'li':
            self._newline()
            self.parts.append('- ')
        elif tag == 'tr':
            self._newline()
            self.first_cell = True
        elif tag in ('td', 'th'):
            if not self.first_cell:
                self.parts.append(': ')
            self.first_cell = False
        elif tag == 'img':
            src = dict(attrs).get('src')
            if src:
                self._newline()
                self.parts.append(src)
                self._newline()

    def handle_data(self, data):
        self.parts.append(re.sub(r'\s+', ' ', data))


def html_to_text(html):
    """Faz o caminho inverso, para editar no formulário um anúncio já salvo."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    lines = [line.strip() for line in ''.join(parser.parts).split('\n')]
    text = '\n'.join(lines)
    return re.sub(r'\n{3,}', '\n\n', text).strip()

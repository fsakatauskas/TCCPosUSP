# pip install nada
"""Gera doc/<documento>/referencia.docx a partir do template padrão do Pandoc,
aplicando Arial, espaçamento 1,5, margens 2,5 cm, texto justificado e títulos pretos.

  python3 .guardrail/referencia.py [documento]
"""

import io
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = "Arial"
LINHA = "360"        # 1,5 em 240 avos
MARGEM = "1418"      # 2,5 cm em twips
TAMANHO = "24"       # 12 pt em meios-pontos
COR_TITULO = "000000"


def paragrafos(s):
    """Aplica espaçamento 1,5 e texto justificado nos estilos de corpo."""
    espaco = f'<w:spacing w:line="{LINHA}" w:lineRule="auto" w:after="0"/>'
    justo = '<w:jc w:val="both"/>'

    def troca(m):
        bloco = m.group(0)
        if "<w:pPr>" in bloco:
            bloco = re.sub(r"<w:spacing[^/]*/>", "", bloco)
            bloco = re.sub(r"<w:jc[^/]*/>", "", bloco)
        else:
            bloco = bloco.replace("/>", "><w:pPr></w:pPr>", 1)
        return bloco.replace("<w:pPr>", f"<w:pPr>{espaco}{justo}", 1)

    for nome in ("Normal", "BodyText", "FirstParagraph", "Compact", "Bibliography", "BlockText"):
        s = re.sub(rf'<w:style [^>]*w:styleId="{nome}">.*?</w:style>', troca, s, flags=re.S)
    return s


def ajustar_styles(s):
    s = re.sub(r'w:ascii="[^"]*"', f'w:ascii="{FONTE}"', s)
    s = re.sub(r'w:hAnsi="[^"]*"', f'w:hAnsi="{FONTE}"', s)
    s = re.sub(r'w:cs="[^"]*"', f'w:cs="{FONTE}"', s)
    s = re.sub(r'w:asciiTheme="[^"]*"', f'w:ascii="{FONTE}"', s)
    s = re.sub(r'w:hAnsiTheme="[^"]*"', f'w:hAnsi="{FONTE}"', s)
    s = re.sub(r'w:eastAsiaTheme="[^"]*"', f'w:eastAsia="{FONTE}"', s)
    s = re.sub(r'w:cstheme="[^"]*"', f'w:cs="{FONTE}"', s)
    s = re.sub(r'<w:sz w:val="\d+"', f'<w:sz w:val="{TAMANHO}"', s)
    s = re.sub(r'<w:szCs w:val="\d+"', f'<w:szCs w:val="{TAMANHO}"', s)
    s = re.sub(r'w:lang w:val="[^"]*"', 'w:lang w:val="pt-BR"', s)
    s = paragrafos(s)
    # docDefaults manda em Normal/Bibliography, que não declaram espaçamento próprio
    s = re.sub(
        r"(<w:pPrDefault>\s*<w:pPr>)(.*?)(</w:pPr>)",
        rf'\1<w:spacing w:line="{LINHA}" w:lineRule="auto" w:after="0"/>\3',
        s, flags=re.S,
    )
    for nivel in range(1, 7):
        s = re.sub(
            rf'(<w:style [^>]*w:styleId="Heading{nivel}">.*?)<w:color w:val="[^"]*"',
            rf'\1<w:color w:val="{COR_TITULO}"', s, flags=re.S,
        )
    s = re.sub(r'<w:style [^>]*w:styleId="Heading(\d)">', r'<w:style w:type="paragraph" w:styleId="Heading\1">', s)
    s = s.replace('<w:color w:val="2F5496"', f'<w:color w:val="{COR_TITULO}"')
    s = s.replace('<w:color w:val="1F3864"', f'<w:color w:val="{COR_TITULO}"')
    return s


def main():
    doc = sys.argv[1] if len(sys.argv) > 1 else "00-projeto-pesquisa"
    destino = RAIZ / "doc" / doc / "referencia.docx"
    with tempfile.TemporaryDirectory() as tmp:
        padrao = Path(tmp) / "padrao.docx"
        subprocess.run(
            ["pandoc", "-o", str(padrao), "--print-default-data-file", "reference.docx"],
            check=True, capture_output=True,
        )
        origem = zipfile.ZipFile(io.BytesIO(padrao.read_bytes()))

    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as saida:
        for item in origem.infolist():
            dados = origem.read(item.filename)
            if item.filename == "word/styles.xml":
                dados = ajustar_styles(dados.decode("utf8")).encode("utf8")
            elif item.filename == "word/theme/theme1.xml":
                t = dados.decode("utf8")
                t = re.sub(r'(<a:(?:major|minor)Font>\s*<a:latin typeface=")[^"]*"', rf'\1{FONTE}"', t)
                dados = t.encode("utf8")
            elif item.filename == "word/document.xml":
                d = dados.decode("utf8")
                m = re.search(r"<w:sectPr.*?</w:sectPr>", d, re.S)
                if m:
                    sect = re.sub(r'w:(top|right|bottom|left)="\d+"', rf'w:\1="{MARGEM}"', m.group(0))
                    d = d.replace(m.group(0), sect)
                dados = d.encode("utf8")
            elif item.filename == "word/fontTable.xml":
                dados = dados.decode("utf8").replace("Calibri", FONTE).replace("Aptos", FONTE).encode("utf8")
            saida.writestr(item, dados)

    print(f"{destino.relative_to(RAIZ)}: {FONTE} {int(TAMANHO)//2}pt, espaçamento 1,5, margens 2,5 cm")


if __name__ == "__main__":
    sys.exit(main())

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
LINHA = "360"           # 1,5 em 240 avos
SIMPLES = "240"         # 1,0 em 240 avos
MARGEM = "1418"         # 2,5 cm em twips
TAMANHO = "24"          # 12 pt em meios-pontos
TAMANHO_CITACAO = "20"  # 10 pt
TAMANHO_TABELA = "20"   # 10 pt
RECUO_CITACAO = "2268"  # 4 cm em twips
COR_TITULO = "000000"
CORPO = ("Normal", "BodyText", "FirstParagraph", "Compact", "Bibliography")
CABECA = ("name", "basedOn", "next", "link", "uiPriority", "semiHidden",
          "unhideWhenUsed", "qFormat", "rsid")


def escrever_ppr(bloco, conteudo):
    """Repõe o <w:pPr> depois dos filhos de cabeçalho, como o schema do OOXML exige."""
    bloco = re.sub(r"<w:pPr\s*/>|<w:pPr>.*?</w:pPr>", "", bloco, flags=re.S)
    corte = bloco.index(">") + 1
    for filho in CABECA:
        for m in re.finditer(rf"<w:{filho}\b[^>]*/>", bloco):
            corte = max(corte, m.end())
    return f"{bloco[:corte]}<w:pPr>{conteudo}</w:pPr>{bloco[corte:]}"


def paragrafos(s):
    """Aplica espaçamento 1,5 e texto justificado nos estilos de corpo."""
    conteudo = f'<w:spacing w:line="{LINHA}" w:lineRule="auto" w:after="0"/><w:jc w:val="both"/>'
    for nome in CORPO:
        s = re.sub(rf'<w:style [^>]*w:styleId="{nome}">.*?</w:style>',
                   lambda m: escrever_ppr(m.group(0), conteudo), s, flags=re.S)
    return s


def citacao(s):
    """Citação longa: recuo de 4 cm, 10 pt e espaçamento simples."""
    s = simples(s, "BlockText", TAMANHO_CITACAO)
    return simples(s, "Bibliography", None, depois="120")


def simples(s, nome, tamanho=None, depois="0"):
    """Entrelinha simples, como a norma pede em tabela, nota de rodapé e referência."""
    alvo = re.search(rf'<w:style [^>]*w:styleId="{nome}">.*?</w:style>', s, re.S)
    if not alvo:
        return s
    b = re.sub(r"<w:rPr>.*?</w:rPr>", "", alvo.group(0), flags=re.S)
    b = escrever_ppr(b, (
        f'<w:spacing w:line="{SIMPLES}" w:lineRule="auto" w:after="{depois}"/>'
        '<w:jc w:val="both"/>' + (f'<w:ind w:left="{RECUO_CITACAO}" w:right="0" w:firstLine="0"/>'
                                  if nome == "BlockText" else "")
    ))
    if tamanho:
        b = b.replace("</w:style>", f'<w:rPr><w:sz w:val="{tamanho}"/><w:szCs w:val="{tamanho}"/></w:rPr></w:style>')
    return s.replace(alvo.group(0), b)


def tabela(s):
    """Célula de tabela bem menor: 12 pt numa grade de 8 colunas quebra a palavra no meio."""
    s = simples(s, "Compact", TAMANHO_TABELA)
    return simples(s, "FootnoteText", TAMANHO_CITACAO)


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
    s = citacao(s)
    s = tabela(s)
    # docDefaults manda em Normal/Bibliography, que não declaram espaçamento próprio
    s = re.sub(
        r"(<w:pPrDefault>\s*<w:pPr>)(.*?)(</w:pPr>)",
        rf'\1<w:spacing w:line="{LINHA}" w:lineRule="auto" w:after="0"/>\3',
        s, flags=re.S,
    )
    def preto(m):
        return re.sub(r"<w:color[^/]*/>", f'<w:color w:val="{COR_TITULO}"/>', m.group(0))

    # Heading1Char em diante também carrega a cor de tema do Pandoc
    s = re.sub(r'<w:style [^>]*w:styleId="Heading\d(?:Char)?">.*?</w:style>', preto, s, flags=re.S)
    s = re.sub(r'<w:style [^>]*w:styleId="Heading(\d)">', r'<w:style w:type="paragraph" w:styleId="Heading\1">', s)
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
                margens = (
                    f'<w:pgMar w:top="{MARGEM}" w:right="{MARGEM}" '
                    f'w:bottom="{MARGEM}" w:left="{MARGEM}" w:header="708" '
                    'w:footer="708" w:gutter="0"/>'
                )
                if "<w:pgMar" in d:
                    d = re.sub(r"<w:pgMar[^/]*/>", margens, d)
                else:
                    d = d.replace("<w:sectPr>", f"<w:sectPr>{margens}", 1)
                dados = d.encode("utf8")
            elif item.filename == "word/fontTable.xml":
                dados = dados.decode("utf8").replace("Calibri", FONTE).replace("Aptos", FONTE).encode("utf8")
            saida.writestr(item, dados)

    print(f"{destino.relative_to(RAIZ)}: {FONTE} {int(TAMANHO)//2}pt, entrelinha 1,5, margens 2,5 cm, "
          f"tabelas {int(TAMANHO_TABELA)//2}pt, citação longa {int(TAMANHO_CITACAO)//2}pt recuo 4 cm")


if __name__ == "__main__":
    sys.exit(main())

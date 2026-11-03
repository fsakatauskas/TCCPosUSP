"""Valida os arquivos e as saídas do documento contra as regras de conformidade.

Uso:
  python3 .guardrail/guardrail.py              # checa fontes do documento
  python3 .guardrail/guardrail.py --render     # checa também as saídas em output/
  python3 .guardrail/guardrail.py --doc 01-artigo
"""

import re
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "doc"
NOMES_DOC = {
    "00-projeto-pesquisa": "Projeto de Pesquisa",
    "01-resultados-preliminares": "Resultados Preliminares",
    "02-tcc": "TCC",
}
TERMOS_TITULO = ("estudo de", "análise de", "influência de", "elaboração de", "efeito de")
PRESENTE = (
    "é conduzida",
    "é desenvolvido",
    "realizam-se",
    "são analisados",
    "é realizada",
    "será conduzida a revisão bibliográfica, com fontes obtidas",
)
FUTURO = "r[áã]o?|ser[áã]o|ir[áã]|ser[áã]"
SECOES_PROJETO = [
    "Introdução",
    "Objetivo",
    "Metodologia",
    "Resultados Esperados",
    "Cronograma de Atividades",
]


def erro(regra, msg):
    print(f"  FALHA  [{regra}] {msg}")
    return 1


def ok(regra, msg):
    print(f"  ok     [{regra}] {msg}")
    return 0


def docs(apenas=None):
    if apenas:
        return [DOCS / apenas]
    return sorted(p for p in DOCS.iterdir() if p.is_dir())


def ler_metadata(d):
    """Lê o frontmatter YAML sem depender de pyyaml: só pares `chave: valor` simples."""
    arquivo = d / "metadata.yaml"
    if not arquivo.exists():
        return None
    texto = arquivo.read_text(encoding="utf8")
    if not texto.strip().startswith("---"):
        return None
    corpo = texto.strip().strip("-").split("\n---")[0]
    meta = {}
    for linha in corpo.splitlines():
        if linha[:1].isspace() or ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:
            meta[chave.strip()] = valor
    return meta or None


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def nome_arquivo(d, meta):
    """Primeiro nome + último sobrenome + tipo do documento."""
    completo = sem_acento(str(meta.get("aluno", ""))).split()
    if len(completo) < 2:
        return None
    tipo = NOMES_DOC.get(d.name, d.name.split("-", 1)[-1].replace("-", " ").title())
    return f"{completo[0]} {completo[-1]} - {tipo}"


def regras_fonte(d, meta):
    """Regras verificáveis direto nos .md e no metadata, sem compilar."""
    falhas = 0
    arquivos = sorted(d.glob("[0-9][0-9]-*.md"))
    corpo = "\n".join(p.read_text(encoding="utf8") for p in arquivos)
    titulos = [sem_acento(m).lower() for p in arquivos for m in re.findall(r"^# (.+)$", p.read_text(encoding="utf8"), re.M)]

    if nome_arquivo(d, meta):
        falhas += ok("arquivo:nome", nome_arquivo(d, meta))
    else:
        falhas += erro("arquivo:nome", "não foi possível derivar do campo aluno")

    for campo in ("pagetitle", "aluno", "orientador", "curso"):
        if meta.get(campo):
            falhas += ok(f"metadata:{campo}", "presente")
        else:
            falhas += erro(f"metadata:{campo}", f"ausente no metadata.yaml")

    titulo = str(meta.get("pagetitle", ""))
    if titulo:
        palavras = len(titulo.split())
        if palavras <= 15:
            falhas += ok("titulo:15-palavras", f"{palavras} palavras")
        else:
            falhas += erro("titulo:15-palavras", f"{palavras} palavras, máximo 15")
        baixo = titulo.lower()
        achado = [t for t in TERMOS_TITULO if baixo.startswith(t)]
        if achado:
            falhas += erro("titulo:termos-proibidos", f"começa com {achado[0]!r}")
        else:
            falhas += ok("titulo:termos-proibidos", "sem termos redundantes")

    if "projeto-pesquisa" in d.name:
        faltando = [s for s in SECOES_PROJETO if sem_acento(s).lower() not in titulos]
        if faltando:
            falhas += erro("projeto:secoes", f"faltando {faltando}")
        else:
            falhas += ok("projeto:secoes", f"{len(SECOES_PROJETO)} seções obrigatórias presentes")

    achados = [t for t in PRESENTE if t in corpo]
    if achados:
        falhas += erro("tempo-verbal", f"presente do indicativo no planejamento: {achados}")
    else:
        falhas += ok("tempo-verbal", "seções de planejamento no futuro")

    if re.search(r"ABNT|Associa[çc][ãa]o Brasileira", corpo, re.I):
        falhas += erro("norma-institucional", "menção a ABNT; a norma é o manual da instituição")
    else:
        falhas += ok("norma-institucional", "sem menção a ABNT")

    for chave, valor in meta.items():
        if isinstance(valor, str) and ":" in valor and not re.search(r"https?://", valor):
            if not (d / "metadata.yaml").read_text(encoding="utf8").count(f'"{valor}"'):
                falhas += erro("yaml:aspas", f"{chave} contém ':' sem aspas (vira mapa)")
    falhas += ok("yaml:aspas", "valores com ':' estão entre aspas")

    if re.search(r"@\w+", corpo):
        falhas += ok("citacoes:pandoc", "citações no formato [@chave]")
    else:
        falhas += erro("citacoes:pandoc", "nenhuma citação encontrada")

    bib = d / "referencias.bib"
    texto_bib = bib.read_text(encoding="utf8") if bib.exists() else ""
    autores = re.findall(r"@\w+\{([^,]+),.*?author\s*=\s*\{+([^,}]+)", texto_bib, re.S)
    sobrenomes = {k: v.strip().strip("{}").strip().split(",")[0] for k, v in autores}
    orfas = []
    for m in re.finditer(r"\[-@([\w:.-]+)\]", corpo):
        antes = corpo[max(0, m.start() - 40):m.start()]
        if sobrenomes.get(m.group(1), "") not in antes:
            orfas.append(m.group(1))
    if orfas:
        falhas += erro("citacoes:autoria", f"[-@…] sem o sobrenome no texto: {orfas}")
    else:
        falhas += ok("citacoes:autoria", "toda citação traz a autoria no texto ou no parêntese")

    if bib.exists():
        identificacao = d / "00-identificacao.md"
        if identificacao.exists():
            cabecalho = identificacao.read_text(encoding="utf8").split("#")[0]
            if "Disponibilidade" in cabecalho:
                falhas += erro("cabecalho:campos", "só Aluno(a), Orientador(a), Curso e o título")
            else:
                falhas += ok("cabecalho:campos", "apenas os campos do template")

        chaves = re.findall(r"^@\w+\{([^,]+),", texto_bib, re.M)
        usadas = set(re.findall(r"@([\w:.-]+)", corpo))
        orfas = [c for c in chaves if c not in usadas]
        if orfas and 'nocite: "@*"' not in (d / "metadata.yaml").read_text(encoding="utf8"):
            falhas += erro("bib:orfas", f"referências não citadas: {orfas}")
        else:
            falhas += ok("bib:integro", f"{len(chaves)} referências")

        entradas = re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", texto_bib, re.S)
        sem_acesso = [
            k for tipo, k, campos in entradas
            if "url" in campos and "urldate" not in campos
        ]
        if sem_acesso:
            falhas += erro("bib:data-acesso", f"sem Acesso em: {sem_acesso}")
        else:
            falhas += ok("bib:data-acesso", "todo recurso on-line tem data de acesso")

        sem_local = [k for tipo, k, campos in entradas if tipo == "book" and "address" not in campos]
        if sem_local:
            falhas += erro("bib:local-livro", f"livro sem local/país: {sem_local}")
        else:
            falhas += ok("bib:local-livro", "livros com local completo")
    return falhas


def xml_valido(z):
    """Valida a sintaxe de cada parte XML: o Word repara ou rejeita pacote malformado."""
    from xml.etree import ElementTree
    for nome in z.namelist():
        if not nome.endswith((".xml", ".rels")):
            continue
        try:
            ElementTree.fromstring(z.read(nome))
        except ElementTree.ParseError as e:
            return f"{nome}: {e}"
    return None


def estilos_docx(z):
    estilos = z.read("word/styles.xml").decode("utf8")
    blocos = dict(re.findall(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>', estilos, re.S))
    return estilos, blocos


def ordem_schema(blocos):
    """No schema OOXML, name/basedOn/next/link vêm antes e rPr depois de pPr."""
    falhas = []
    for nome, bloco in blocos.items():
        if len(re.findall(r"<w:pPr\s*(?:/>|>)", bloco)) > 1:
            falhas.append(f"{nome}: mais de um <w:pPr>")
        if re.search(r"<w:pPr\s*(?:/>|>)", bloco) and re.search(r"<w:name\b", bloco):
            if bloco.index("<w:pPr") < bloco.index("<w:name"):
                falhas.append(f"{nome}: <w:pPr> antes de <w:name>")
        if re.search(r"<w:pPr\s*(?:/>|>)", bloco) and re.search(r"<w:rPr\s*(?:/>|>)", bloco):
            if bloco.index("<w:rPr") < bloco.index("<w:pPr"):
                falhas.append(f"{nome}: <w:rPr> antes de <w:pPr>")
    return falhas


def integridade_docx(caminho):
    """Confere o pacote OOXML e a formatação: é isso que o Word exige para abrir decente."""
    partes = [
        "[Content_Types].xml",
        "_rels/.rels",
        "word/document.xml",
        "word/_rels/document.xml.rels",
        "word/styles.xml",
        "word/theme/theme1.xml",
    ]
    try:
        with zipfile.ZipFile(caminho) as z:
            ruim = z.testzip()
            faltando = [x for x in partes if x not in set(z.namelist())]
            if faltando:
                return f"pacote sem {faltando}"
            xml = z.read("word/document.xml").decode("utf8")
            if "<w:document" not in xml or "</w:document>" not in xml:
                return "word/document.xml malformado"
            if "word/document.xml" not in z.read("_rels/.rels").decode("utf8"):
                return "pacote sem relacao com o documento principal"
            estilos = z.read("word/styles.xml").decode("utf8")
            if "Arial" not in estilos + z.read("word/theme/theme1.xml").decode("utf8"):
                return "fonte Arial ausente dos estilos"
            usados = set(re.findall(r'w:pStyle w:val="([^"]+)"', xml))
            definidos = set(re.findall(r'w:styleId="([^"]+)"', estilos))
            orfaos = sorted(usados - definidos)
            if orfaos:
                return f"estilos usados e nao definidos (Word cai no padrao): {orfaos}"
            ruim = xml_valido(z)
            if ruim:
                return f"XML malformado: {ruim}"
            problemas = ordem_schema(estilos_docx(z)[1])
            if problemas:
                return "; ".join(problemas[:4])
    except zipfile.BadZipFile as e:
        return f"nao e um zip valido: {e}"
    except (UnicodeDecodeError, KeyError) as e:
        return f"parte do pacote ilegivel: {e}"
    return f"entrada corrompida: {ruim}" if ruim else None


def abnt_docx(caminho):
    """Confere as regras de formatação da norma nos estilos que o corpo do texto usa."""
    z = zipfile.ZipFile(caminho)
    estilos, blocos = estilos_docx(z)
    documento = z.read("word/document.xml").decode("utf8")
    corpo = ("Normal", "BodyText", "FirstParagraph")
    falhas = []

    sem_15 = [n for n in corpo if n in blocos and not re.search(r'w:line="360"', blocos[n])]
    if sem_15:
        falhas.append(f"sem entrelinha 1,5: {sem_15}")
    sem_simples = [n for n in ("Compact", "FootnoteText", "Bibliography")
                   if n in blocos and not re.search(r'w:line="240"', blocos[n])]
    if sem_simples:
        falhas.append(f"fora de espacamento simples (tabela/nota/referencia): {sem_simples}")
    sem_justo = [n for n in corpo if n in blocos
                 and n != "Compact" and not re.search(r'<w:jc w:val="both"\s*/>', blocos[n])]
    if sem_justo:
        falhas.append(f"sem texto justificado: {sem_justo}")
    # TODO corpo herda tamanho e fonte do docDefaults quando o estilo nao declara os seus
    padrao = re.search(r"<w:rPrDefault>.*?</w:rPrDefault>", estilos, re.S)
    padrao = padrao.group(0) if padrao else ""
    if not re.search(r"<w:sz w:val=\"24\"", padrao):
        falhas.append("corpo nao declara 12 pt")
    if re.search(r'w:(?:ascii|hAnsi|cs)="(?!Arial)[^"]+"', padrao):
        falhas.append("corpo nao declara Arial")
    if re.search(r'w:ascii="(?!Arial)[^"]+"', estilos):
        outras = sorted(set(re.findall(r'w:ascii="([^"]+)"', estilos)) - {"Arial"})
        falhas.append(f"fontes fora do padrao: {outras}")

    tabela = blocos.get("Compact", "")
    if tabela and not re.search(r'<w:sz w:val="20"', tabela):
        falhas.append("celula de tabela fora de 10 pt")
    citacao = blocos.get("BlockText", "")
    if citacao:
        if not re.search(r'w:line="240"', citacao):
            falhas.append("citacao longa fora de espacamento simples")
        if not re.search(r'<w:sz w:val="20"', citacao):
            falhas.append("citacao longa fora de 10 pt")
        recuo = re.search(r'<w:ind[^/]*w:left="(\d+)"', citacao)
        if not recuo or int(recuo.group(1)) < 2000:
            falhas.append("citacao longa com recuo menor que 4 cm")

    if not re.search(r'<w:pgMar[^/]*w:left="1418"', documento):
        falhas.append("margens diferentes de 2,5 cm")
    # o rotulo da primeira coluna precisa caber em uma linha: o Pandoc reparte a grade
    # em colunas iguais e, sem largura declarada no md, sobra 1,2 cm para o rotulo
    for grade in re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", documento, re.S):
        colunas = [int(c) for c in re.findall(r'<w:gridCol w:w="(\d+)"', grade)]
        if len(colunas) < 2:
            continue
        if colunas[0] < 2400 or colunas[0] < colunas[1]:
            falhas.append(f"tabela com o rotulo da 1a coluna em {colunas[0]} twips "
                          f"(contra {colunas[1]} nas demais): estreito demais")
    titulos = [b for n, b in blocos.items() if re.match(r"Heading\dChar$", n)]
    coloridos = [t for t in titulos if re.search(r'<w:color w:val="(?!000000)[0-9A-Fa-f]{6}"', t)]
    if coloridos:
        falhas.append(f"{len(coloridos)} titulos com cor diferente de preto")
    return "; ".join(falhas) if falhas else None


def integridade_pdf(caminho):
    """Confere a estrutura do PDF e extrai texto, como faz um leitor."""
    dados = caminho.read_bytes()
    if not dados.startswith(b"%PDF-"):
        return "sem cabecalho %PDF-"
    if b"%%EOF" not in dados[-2048:]:
        return "sem marcador %%EOF no fim"
    if b"/Root" not in dados:
        return "sem catalogo /Root"
    try:
        texto = _extrair_texto_pdf(caminho)
    except Exception as e:
        return f"ilegivel para o extrator: {e}"
    if texto is None:
        print("  aviso  [formato:pdf] pdftotext ausente; checagem estrutural apenas")
        return None
    if len(texto.strip()) < 500:
        return f"texto extraido muito curto ({len(texto.strip())} caracteres)"
    paginas = texto.count("\f") + 1
    if paginas < 2:
        return f"apenas {paginas} pagina extraivel"
    return None


def _extrair_texto_pdf(caminho):
    """pdftotext quando disponivel. Sem ele, devolve None: sem extrator, sem veredito."""
    try:
        r = subprocess.run(["pdftotext", str(caminho), "-"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    return None


def _texto_docx(caminho):
    with zipfile.ZipFile(caminho) as z:
        xml = z.read("word/document.xml").decode("utf8")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def regras_render(d, meta):
    """Regras que exigem as saidas compiladas em output/."""
    falhas = 0
    nome = nome_arquivo(d, meta)
    saida = RAIZ / "output"
    print()

    for extensao, checar in ((".docx", integridade_docx), (".pdf", integridade_pdf)):
        arquivo = saida / f"{nome}{extensao}"
        if not arquivo.exists():
            falhas += erro(f"output:{extensao[1:]}", f"{arquivo.name} nao encontrado; rode `make all DOC={d.name}`")
            continue
        problema = checar(arquivo)
        if problema:
            falhas += erro(f"formato:{extensao[1:]}", f"{arquivo.name}: {problema}")
        else:
            falhas += ok(f"formato:{extensao[1:]}", f"{arquivo.name} integro ({arquivo.stat().st_size // 1024} KB)")

    dpath = saida / f"{nome}.docx"
    if dpath.exists():
        problema = abnt_docx(dpath)
        if problema:
            falhas += erro("abnt:formatacao", problema)
        else:
            falhas += ok("abnt:formatacao", "Arial 12 pt, 1,5, justificado, margens 2,5 cm, "
                                           "tabela 10 pt, citação longa 10 pt/recuo 4 cm")

    docx = saida / f"{nome}.docx"
    if not docx.exists():
        return falhas
    texto = _texto_docx(docx)
    if re.search(r"\btrue\b|\bfalse\b", texto):
        falhas += erro("docx:yaml-mapa", "valor booleano renderizado (':' sem aspas no YAML)")
    else:
        falhas += ok("docx:yaml-mapa", "sem valores booleanos vazados")

    if "Aluno(a)" in texto and "Orientador" in texto:
        falhas += ok("docx:identificacao", "cabecalho Aluno/Orientador presente")
    else:
        falhas += erro("docx:identificacao", "cabecalho institucional ausente")

    if "Table of Contents" in texto:
        falhas += erro("docx:sumario", "sumario presente; o Projeto de Pesquisa nao o leva")
    else:
        falhas += ok("docx:sumario", "sem sumario, conforme o template")

    if re.search(r"\bABNT\b", texto, re.I):
        falhas += erro("docx:norma", "mencao a ABNT na saida")
    else:
        falhas += ok("docx:norma", "sem mencao a ABNT")

    if re.search(r"\b(é conduzida|é desenvolvido|realizam-se)\b", texto):
        falhas += erro("docx:tempo-verbal", "presente do indicativo na saida")
    else:
        falhas += ok("docx:tempo-verbal", "planejamento no futuro")

    refs = re.findall(r"^\s*[A-ZÀ-Ý][\w'’]+,\s+[A-Z]\.", texto, re.M)
    if refs:
        falhas += ok("docx:referencias", f"{len(refs)} referencias no padrao institucional")
    else:
        falhas += erro("docx:referencias", "referencias fora do padrao Sobrenome, N.")

    if "Disponível em:" in texto and "Acesso em:" in texto:
        falhas += ok("docx:acesso", "todo recurso on-line com Disponivel em/Acesso em")
    else:
        falhas += erro("docx:acesso", "falta 'Disponivel em:' ou 'Acesso em:'")

    orfas_ano = [
        m.group(0) for m in re.finditer(r".{40}\(\d{4}\)", texto, re.S)
        if not re.search(r"[A-ZÀ-Ý]\w+\s*$", m.group(0)[:-6])
    ]
    if orfas_ano:
        falhas += erro("docx:citacao-sem-autor", f"citacao so com o ano: {orfas_ano}")
    else:
        falhas += ok("docx:citacao-sem-autor", "nenhuma citacao orfa de autoria")

    if "Disponibilidade" in texto.split("#")[0][:400]:
        falhas += erro("docx:cabecalho", "campo fora do template no cabecalho")
    else:
        falhas += ok("docx:cabecalho", "cabecalho conforme o template")
    return falhas


def main():
    args = sys.argv[1:]
    render = "--render" in args
    apenas = args[args.index("--doc") + 1] if "--doc" in args else None
    total = 0
    for d in docs(apenas):
        meta = ler_metadata(d)
        if meta is None:
            total += erro("metadata:arquivo", f"{d.name} sem metadata.yaml valido")
            continue
        print(f"\n{d.name}")
        total += regras_fonte(d, meta)
        if render:
            total += regras_render(d, meta)
    print(f"\n{'OK — tudo conforme' if total == 0 else f'{total} violacoes'}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

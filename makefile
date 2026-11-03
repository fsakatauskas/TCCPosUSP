# make all DOC=00-projeto-pesquisa | make list | make clean | make check
# TOC=1 gera sumário | NUM=1 numera as seções
# NAME= override do nome do arquivo (padrão: primeiro nome + último sobrenome + tipo do documento)
DOC    ?= 00-projeto-pesquisa
NAME   ?= $(shell python3 .guardrail/nome.py $(DOC))
TOC    ?= 0
NUM    ?= 0
DIR    := doc/$(DOC)
OUT    := output
META   := $(DIR)/metadata.yaml
SRC    := $(sort $(wildcard $(DIR)/*.md))
FLAGS  := $(if $(filter 1,$(TOC)),--toc) $(if $(filter 1,$(NUM)),--number-sections)
SHARED := --metadata-file=$(META) --citeproc $(FLAGS) --resource-path=.:$(DIR)

pdf: check-files
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o "$(OUT)/$(NAME).pdf" --pdf-engine=xelatex -V geometry:margin=3cm -V fontsize=12pt -V mainfont=Arial

docx: check-files
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o "$(OUT)/$(NAME).docx" --reference-doc=$(DIR)/referencia.docx

html: check-files
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o "$(OUT)/$(NAME).html" --standalone --embed-resources --css=$(DIR)/estilo.css

all: pdf docx html

check: check-doc
	python3 .guardrail/guardrail.py --doc $(DOC) --render

check-doc:
	python3 .guardrail/guardrail.py --doc $(DOC)

check-all:
	python3 .guardrail/guardrail.py --render

list:
	@ls -d doc/*/ | sed 's|doc/||;s|/||'

check-files:
	@test -f "$(META)" || { echo "sem $(META)"; exit 1; }

clean:
	rm -rf $(OUT)

.PHONY: pdf docx html all check check-doc check-all list check-files clean

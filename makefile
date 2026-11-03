# make pdf DOC=00-projeto-pesquisa | make list | make clean
DOC    ?= 00-projeto-pesquisa
NAME   ?= Sakatauskas
DIR    := doc/$(DOC)
OUT    := output
META   := $(DIR)/metadata.yaml
SRC    := $(sort $(wildcard $(DIR)/*.md))
SHARED := --metadata-file=$(META) --citeproc --toc --number-sections --resource-path=.:$(DIR)

pdf: check
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o $(OUT)/$(NAME).pdf --pdf-engine=xelatex -V geometry:margin=3cm -V fontsize=12pt -V mainfont=Arial

docx: check
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o $(OUT)/$(NAME).docx --reference-doc=$(DIR)/referencia.docx

html: check
	@mkdir -p $(OUT)
	pandoc $(SHARED) $(SRC) -o $(OUT)/$(NAME).html --standalone --embed-resources --css=$(DIR)/estilo.css

all: pdf docx html

list:
	@ls -d doc/*/ | sed 's|doc/||;s|/||'

check:
	@test -f "$(META)" || { echo "sem $(META)"; exit 1; }

clean:
	rm -rf $(OUT)

.PHONY: pdf docx html all list check clean
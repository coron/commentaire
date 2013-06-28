DVDPATH=~/CommentaireDVD
ARCHIVEFILE=$(DVDPATH)/CollectionCommentaire.exe

all: articles2.xml authors.xml
	mkdir -p pdf
	mkdir -p temp
	python small.py

articles2.xml : articles.xml
	cat articles.xml | tr -d '\r' | ./insertnewline.sh > articles2.xml

articles.xml :
	-unzip $(ARCHIVEFILE) articles.xml

authors.xml :
	-unzip $(ARCHIVEFILE) authors.xml


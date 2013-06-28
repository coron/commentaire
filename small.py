# -*- coding: iso-8859-15 -*-

import Image,ImageDraw
import xml.dom.minidom
import os

hmax=1000
wmax=815
dymin=4;dymax=50

from os.path import expanduser
home=expanduser("~")

archivedvdpath=home+"/CommentaireDVD/archive/"
destFolder="pdf/"
tempFolder="temp/"

fdx=3.5; fdy=1.3

def toUpper(s):
  return s.encode('ascii','ignore').upper()

def isInt(s):
  try:
    int(s)
    return True
  except ValueError:
    return False
  
def dims(box):
  w=box[2]-box[0]
  h=box[3]-box[1]
  return w,h

def resize(w,h,wmax):
  fa=1
  if w>wmax:
    fa=(1.*wmax)/w
    h=int(h*fa)
    w=wmax
  return w,h

def imageFileNameId(id):
  file=id[:-5]
  return file

def imageFileId(id):
  folder=archivedvdpath+"image/"+id[:10]+"/"
  return folder+imageFileNameId(id)+".tif"

def loadImageId(id):
  tiffile=imageFileId(id)
  pngfile=tempFolder+imageFileNameId(id)+".png"
  print "Loading image:",id
  try:
    open(pngfile)
  except IOError:
    import os
    os.system("convert \"%s\" %s" % (tiffile,pngfile))

  im=Image.open(pngfile)
  return im

def imageFileName(year,season,num,page):
  return "%d-%d-%d_5p_%04d" % (year,season,num,page)

def imageFile(year,season,num,page):
  folder="image/%d-%d-%d/" % (year,season,num)
  filename=imageFileName(year,season,num,page)+".tif"
  return dvdpath+folder+filename
  
def numero(id):
  return int(id.split("_")[0][-3:])

"Return a list of id given the first id and the number of pages"
def listId(id,nbPages):
  listid=[]
  page=int(id.split("_")[2])
  for i in range(page,page+nbPages):
    li=id.split("_")
    li[2]="%04d" % i
    vid="_".join(li)
    listid=listid+[vid]
  return listid

"""Generates a list of ids corresponding to a year"""
def genArticles(aut="ALAIN BES",cat="Articles",nmaxart=2,num=-1,year=1978):
  document=open("articles2.xml").read()
  dom=xml.dom.minidom.parseString(document)

  nart=0
  for art in dom.getElementsByTagName("art"):
    if art.childNodes:
      author=art.childNodes[0].attributes["name"].value
      title=art.attributes["title"].value
      category=art.attributes["category"].value
      nbPages=int(art.attributes["nbPages"].value)
      id=art.attributes["id"].value
      idyear=int(id.split("-")[0])
      if cat!=category: continue
      if (aut!="" and author.encode('ascii','ignore')==aut.encode('ascii','ignore')) or numero(id)==num or idyear==year:
        nart=nart+1
        if nart>nmaxart: break
        yield title,author,category,nbPages,listId(id,nbPages)

"""Generates the pdf for all articles of a given year"""
def parseCom(nmaxart=2000,aut="",cat="Articles",num=-1,year=1978):
  startpage=1
  indpage=startpage
  str=""
  strpage=""
  indart=1
  listfiles=""
  empty=True
  for title,author,category,nbPages,lid in genArticles(aut="",cat=cat,nmaxart=nmaxart,num=num,year=year):
    empty=False
    try:
      from pyPdf import PdfFileReader
      input=PdfFileReader(file("pdf/%s.pdf" % lid[0],"rb"))
      deltapage=input.getNumPages()
    except IOError:
      print "Making %s %s" % (title,author)
      deltapage=makeArticle(title,author,lid)
    
    title=title.replace("&quot;","").replace("%","")
    str=str+("\item %s, {\\sl %s} \\dotfill \\hyperlink{test%d.1}{%d}\n" % \
            (author.title(),title,indart,indpage)).encode("iso-8859-1","ignore")
    indpage=indpage+deltapage

    strpage=strpage+"\\includepdf[pages={-},link,linkname=test%d]{pdf/%s.pdf}\n" % (indart,lid[0])
    indart=indart+1
    listfiles=listfiles+" pdf/%s.pdf" % lid[0]

  if empty: return
  strtemplate=open("template.tex").read()
  ftexname="commentaire%d.tex" % year
  open(ftexname,"w").write((strtemplate % (year,str))+strpage.encode("iso-8859-1","ignore")+"\n\end{document}")
  os.system("pdflatex "+ftexname)
  os.system("rm -f *.aux *.log *.out commentaire*.tex")

def testMakeArticle():
  lid=genFirstArticle()[4]
  makeArticle("","RAYMOND ARON",lid)

"""Produces a pdf file for a given article. 
   Only lid is important, title and authors are only used 
   to remove occurence of title and authors in the text."""
def makeArticle(title,author,lid):
  indpage=makePage(genPagesSimple(genWordsIds(lid),title,author),0)
  listfiles=" ".join(["pdf/com%04d.pdf" % i for i in range(indpage)])
  destfile="pdf/%s.pdf" % lid[0]
  import os
  os.system("gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=%s %s" % (destfile,listfiles))
  os.system("rm %s" % listfiles)
  return indpage

def FullBox(u):
  "Given a list of boxes, give the box that encompasses them"
  return [max(u,key=lambda x:s*x[i])[i] for s,i in ((-1,0),(-1,1),(1,2),(1,3))]

def testMakePage():
  lid=genFirstArticle()[4]
  gword=genWordsIds(lid[0:2])
  gpage=genPagesSimple(gword,"","")
  makePage(gpage)

"Makes the pages from the generator of pages"
def makePage(gpage,startdestpage=1):
  indpage=startdestpage
  refold=False
  for li in gpage:
    xmin,ymin,xmax,ymax=FullBox([pa for (box,lmots,ref,pa) in li])
    print "Page", indpage, "Size of page:",xmax-xmin,ymax-ymin
    im2=Image.new("1",(wmax,ymax),1)

    for box,lmots,ref,pas in li:
      id=ref
      if refold!=ref:
        im=loadImageId(id)
      refold=ref
      region=im.crop(box)
      if dims(pas)!=dims(box):
        region=region.resize(dims(pas))
      im2.paste(region,pas)
  
    im2.save("pdf/com%04d.pdf" % indpage)
    indpage=indpage+1
  return indpage
  

"Generates the data for the first Raymond Aron article"
def genFirstArticle():
  return list(genArticles(aut="",cat="Articles",nmaxart=2,num=1))[1]

def testGenBoxes():
  lid=genFirstArticle()[4]
  print lid
  gword=list(genWordsIds(lid[0:2]))
  print gword
  print list(genBoxes(gword))
  print list(genPagesSimple(gword,"",""))

"A generator of list of box positions, a list per page"
def genPagesSimple(gwords,title,author):
  lhlim=[hmax]
  gboxes=genBoxes(gwords,lhlim)
  hc=0
  li=[]
  y2old=0
  for box,lmots,ref,newPage in gboxes:
    if "COMMENTAIRE" in lmots: continue
    if len(lmots)==1 and isInt(lmots[0]): continue
    if lmots==toUpper(author).split(" "): continue
    if lmots==toUpper(title).split(" "): continue 
    w,h=dims(box)
    y=box[1]
    dy=y-y2old  # distance with previous box
    if dy>dymax: dy=dymax 
    if dy<dymin: dy=dymin
    w,h=resize(w,h,wmax)
    dx=(wmax-w)/2
    
    li.append((box,lmots,ref,(dx,hc+dy,w+dx,hc+h+dy)))
    hc=hc+h+dy
    y2old=box[3]
    
    if newPage:
      yield li
      li=[]
      hc=0
    lhlim[0]=hmax-hc
  if li: yield li

"A generator of boxes, where lhlim[0] controls page break"
def genBoxes(gword,lhlim=[hmax]):
  yrefbox=0
  yold=0;y2old=0;hold=0
  u,mots=[],[]
  for (x,y,x2,y2),mot,ref in gword:
    inRange=y in range(yold-int(hold*fdy),y2old+int(hold*fdy))
    newPage=(y2-yrefbox)>lhlim[0]
    if u==[] or (inRange and not newPage):
      if u==[]:
        yrefbox=y
      else:
        yrefbox=min(y,yrefbox)
      u.append((x,y,x2,y2))
      mots.append(mot)
      ref2=ref
    else:
      box=FullBox(u)
      yield box,mots,ref2,newPage
      yrefbox=y
      u=[(x,y,x2,y2)]
      mots=[mot]
    y2old=y2;yold=y;hold=y2-y
  
  if u:
    box=FullBox(u)
    yield box,mots,ref2,True

def xmlId(id):
  year=id[:4]
  folder="xml/"+year+"/"
  filename=id[:-5]+".xml"
  return archivedvdpath+folder+filename

"Generates the words inside a page given by its Id"
def genWordsId(Id="1978-1-001_5p_0007_art1"):
  fname=xmlId(Id)
  try:
    s=open(fname).read()
    dom=xml.dom.minidom.parseString(s)
    print "Id=",Id
    for words in dom.getElementsByTagName("wd"):
      mot=words.childNodes[0].data
      x,y,w,h=[int(words.attributes[s].value) for s in ["x","y","w","h"]]
      yield (x,y,x+w+1,y+h+1),mot,Id
  except IOError:
    print "File not found: "+fname
    pass

"Generates the words from a list of pages given by their ids"
def genWordsIds(gids):
  return (w for Id in gids for w in genWordsId(Id))
  
if __name__=="__main__":
  for year in range(1978,2010):
    parseCom(year=year)

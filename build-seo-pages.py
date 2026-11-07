"""Restore home-page SEO after a site export and stage the single-page website."""

from pathlib import Path

from html import escape

from html.parser import HTMLParser

from urllib.parse import urlparse

import json,re

import shutil

import sys



ROOT=Path(__file__).resolve().parent

BASE='https://media-circle.ru/'

data=json.loads((ROOT/'content.json').read_text(encoding='utf-8-sig'))

index=(ROOT/'index.html').read_text(encoding='utf-8')

def normalize_text(value):

 return value.replace('http://media-circle.ru','https://media-circle.ru').replace('"instagram":"instagram.com/k_media_circle"','"instagram":"https://www.instagram.com/k_media_circle/"').replace('"instagram": "instagram.com/k_media_circle"','"instagram": "https://www.instagram.com/k_media_circle/"')

index=normalize_text(index)

data=json.loads(normalize_text(json.dumps(data,ensure_ascii=False)))

home_title='медиакружок'

home_description='Сообщество артистов из Сибири, которым интересно медиаискусство.'

index=re.sub(r'<title>.*?</title>','<title>'+home_title+'</title>',index,count=1)

for attr,key,value in [('name','description',home_description),('property','og:title',home_title),('property','og:description',home_description),('name','twitter:title',home_title),('name','twitter:description',home_description)]:

 index=re.sub(r'(<meta '+attr+'="'+re.escape(key)+r'" content=")[^"]*(">)',lambda m:m[1]+value+m[2],index,count=1)

canonical='<link rel="canonical" href="https://media-circle.ru/">'

if re.search(r'<link[^>]*rel="canonical"[^>]*>',index):index=re.sub(r'<link[^>]*rel="canonical"[^>]*>',canonical,index)

else:index=index.replace('</head>',canonical+'\n</head>',1)
favicon = '<link rel="icon" type="image/png" sizes="64x64" href="/favicon.png">'
if not re.search(r'<link\b[^>]*\brel="(?:shortcut )?icon"', index, re.I):
    index = index.replace('</head>', favicon + '\n</head>', 1)

home_schema={'@context':'https://schema.org','@graph':[{'@type':'Organization','@id':BASE+'#organization','name':'Медиакружок','url':BASE,'description':home_description,'email':'hello@media-circle.ru','location':{'@type':'City','name':'Красноярск'},'sameAs':['https://t.me/k_media_circle','https://www.instagram.com/k_media_circle/']},{'@type':'WebSite','@id':BASE+'#website','url':BASE,'name':'Медиакружок','inLanguage':'ru-RU','publisher':{'@id':BASE+'#organization'}}]}

index=re.sub(r'<script type="application/ld\+json">.*?</script>','',index,flags=re.S)

index=re.sub(r'\s*</head>','\n<script type="application/ld+json">'+json.dumps(home_schema,ensure_ascii=False)+'</script>\n</head>',index,count=1)

index=index.replace("if(['karst','livecoding','pustotu','angarida'].includes(item.slug))", "if(item.type==='project'&&!item.demo)")

embedded=json.loads(re.search(r'window.MEDIA_CONTENT=(.*?);?</script>',index,re.S)[1].removesuffix(';'))

assert embedded==data,'Export both index.html and content.json together before building.'

# Ignore the retired tools category in older editor exports.
data['items'] = [item for item in data['items'] if item.get('type') != 'meeting']
index = re.sub(r'<button[^>]*data-filter="meeting"[^>]*>[^<]*</button>', '', index)
index = re.sub(r",\s*\{id:'meeting',\s*label:'инструменты'\}", '', index)
index = index.replace('Скоро здесь появятся проекты и инструменты.', 'Скоро здесь появятся проекты.')
def url(v):

 v=str(v or '').replace('http://media-circle.ru','https://media-circle.ru')

 return v if urlparse(v).scheme in ('http','https','mailto') else ''

class Clean(HTMLParser):

 def __init__(self):super().__init__();self.out=[];self.skip=0

 def handle_starttag(self,t,a):

  if t in ('script','style','iframe'):self.skip+=1;return

  if self.skip:return

  if t in {'p','div','span','br','strong','b','em','i','ul','ol','li','h2','h3','h4','blockquote','a'}:

   at=dict(a);attrs=''

   if t=='a' and url(at.get('href')):attrs=' href="'+escape(url(at['href']),quote=True)+'"'

   self.out.append('<'+t+attrs+'>')

 def handle_endtag(self,t):

  if t in ('script','style','iframe'):self.skip=max(0,self.skip-1);return

  if not self.skip and t in {'p','div','span','strong','b','em','i','ul','ol','li','h2','h3','h4','blockquote','a'}:self.out.append('</'+t+'>')

 def handle_data(self,s):

  if not self.skip:self.out.append(escape(s))

def rich(b):

 c=Clean();c.feed(b.get('richHTML') or '<p>'+escape(b.get('text',''))+'</p>');return ''.join(c.out)

def plain(s):return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',s)).strip()

items=[i for i in data['items'] if i.get('type')=='project' and not i.get('demo')]

for item in items:assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',item.get('slug','')), 'Invalid project slug'

descriptions={

 'karst':'Видеоарт Инны Шестаковой: геологические формы и генеративная графика. Проект Медиакружка для Музея геологии Центральной Сибири в Красноярске, 2026.',

 'livecoding':'Аудиовизуальный лайвкодинг: музыка Алексея Акимова и визуал Инны Шестаковой создаются в реальном времени. Медиакружок, 29 сентября 2026 года.',

 'pustotu':'Барельефы Алексея Акимова и видеомэппинг Инны Шестаковой в проекте «Невечная мерзлота». Документация Медиакружка, 2026.',

 'angarida':'Аудиовизуальный перформанс Медиакружка в Красноярске в рамках выставки «Ангарида: место, где тебе рады». Работа со звуком и генеративной графикой.'}

for item in items:

 slug=item['slug']

 if slug not in descriptions:

  paragraphs=[plain(rich(b)) for b in item.get('blocks',[]) if b.get('kind')=='text']

  descriptions[slug]=(next((x for x in paragraphs if len(x)>90),item['title']+' — проект Медиакружка.'))[:240]

 item['summary']=descriptions[slug]

(ROOT/'content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')

index=re.sub(r'(window.MEDIA_CONTENT=).*?(;?</script>)',lambda m:m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<',chr(92)+'u003c')+';'+m[2].lstrip(';'),index,count=1,flags=re.S)

index=re.sub(r'<!-- seo-pages:start -->.*?<!-- seo-pages:end -->','',index,flags=re.S)
index=re.sub(r"if\(item.type==='project'&&!item.demo\)\{const link=el\('a','text-link','Страница проекта ↗'\);[\s\S]*?container.append\(p\);\}",'',index)
(ROOT/'index.html').write_text(index,encoding='utf8',newline='')

urls=[BASE]

(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+x+'</loc></url>' for x in urls)+'</urlset>\n',encoding='utf8')

(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: https://media-circle.ru/sitemap.xml\n',encoding='utf8')

if '--stage' in sys.argv:

 stage=ROOT/'_site'

 stage.mkdir(exist_ok=True)

 # Replace retired standalone pages with redirects, including on reused builds.
 for staged in stage.glob('*.html'):
  if staged.name!='index.html' and not re.fullmatch(r'google[a-f0-9]+\.html|yandex_[a-f0-9]+\.html',staged.name):staged.unlink()

 for p in ROOT.iterdir():

  if p.is_file() and (p.name in ('index.html','content.json','sitemap.xml','robots.txt','CNAME','.nojekyll','favicon.png','favicon.ico') or re.fullmatch(r'google[a-f0-9]+\.html|yandex_[a-f0-9]+\.html',p.name)):shutil.copy2(p,stage/p.name)

 if (ROOT/'media').is_dir():shutil.copytree(ROOT/'media',stage/'media',dirs_exist_ok=True)

 redirect='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>медиакружок</title><meta name="robots" content="noindex, follow"><meta http-equiv="refresh" content="0;url=https://media-circle.ru/"><link rel="canonical" href="https://media-circle.ru/"></head><body><a href="https://media-circle.ru/">Перейти на главную</a></body></html>'''
 for retired in ('about.html','projects.html','karst.html','livecoding.html','pustotu.html','angarida.html'):
  (stage/retired).write_text(redirect,encoding='utf-8')

 assert (stage/'index.html').is_file()

print('Generated:',', '.join(urls))



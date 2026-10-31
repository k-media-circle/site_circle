"""Run after a site export: python build-seo-pages.py. No dependencies."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse
import json,re

ROOT=Path(__file__).resolve().parent
BASE='https://media-circle.ru/'
data=json.loads((ROOT/'content.json').read_text(encoding='utf-8-sig'))
index=(ROOT/'index.html').read_text(encoding='utf-8')
home_title='Медиакружок | Красноярск'
home_description='Сообщество артистов из Сибири, которым интересно медиаискусство.'
index=re.sub(r'<title>.*?</title>','<title>'+home_title+'</title>',index,count=1)
for attr,key,value in [('name','description',home_description),('property','og:title',home_title),('property','og:description',home_description),('name','twitter:title',home_title),('name','twitter:description',home_description)]:
 index=re.sub(r'(<meta '+attr+'="'+re.escape(key)+r'" content=")[^"]*(">)',lambda m:m[1]+value+m[2],index,count=1)
embedded=json.loads(re.search(r'window.MEDIA_CONTENT=(.*?);?</script>',index,re.S)[1].removesuffix(';'))
assert embedded==data,'Export both index.html and content.json together before building.'
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
def media(b,title):
 src=url((b.get('preview') or {}).get('src') or b.get('src'))
 if not src:return ''
 alt=escape(b.get('alt') or 'Документация проекта «'+title+'»',quote=True)
 if b.get('kind')=='video':
  if 'youtu' in src:return '<p><a href="'+escape(src,quote=True)+'">Смотреть видеозапись</a></p>'
  return '<figure><video controls playsinline preload="none" src="'+escape(src,quote=True)+'" aria-label="'+alt+'"></video></figure>'
 return '<figure><img loading="lazy" decoding="async" src="'+escape(src,quote=True)+'" alt="'+alt+'"></figure>'
def blocks(bs,title):
 out=[]
 for b in bs:
  kind=b.get('kind')
  if kind in ('text','heading'):out.append(rich(b))
  elif kind in ('image','video'):out.append(media(b,title))
  elif kind=='gallery':out.append('<div class="gallery">'+''.join(media(x,title) for x in b.get('items',[]))+'</div>')
  elif b.get('text'):out.append('<p>'+escape(b['text'])+'</p>')
 return '\n'.join(out)
items=[i for i in data['items'] if i.get('type')=='project' and not i.get('demo')]
descriptions={
 'karst':'Видеоарт Инны Шестаковой: геологические формы и генеративная графика. Проект Медиакружка для Музея геологии Центральной Сибири в Красноярске, 2026.',
 'livecoding':'Аудиовизуальный лайвкодинг: музыка Алексея Акимова и визуал Инны Шестаковой создаются в реальном времени. Медиакружок, 29 сентября 2026 года.',
 'pustotu':'Барельефы Алексея Акимова и видеомэппинг Инны Шестаковой в проекте «Невечная мерзлота». Документация Медиакружка, 2026.',
 'angarida':'Аудиовизуальный перформанс Медиакружка в Красноярске в рамках выставки «Ангарида: место, где тебе рады». Работа со звуком и генеративной графикой.'}
CSS='''*{box-sizing:border-box}body{margin:0;background:#10110f;color:#e9e9e1;font:18px/1.65 Arial,Helvetica,sans-serif}a{color:inherit;text-underline-offset:5px}a:hover,a:focus-visible{color:#c8ec01}:focus-visible{outline:2px solid #c8ec01;outline-offset:6px}header,main,footer{max-width:1120px;margin:auto;padding:28px 6vw}header{display:flex;justify-content:space-between;gap:24px;align-items:center;border-bottom:1px solid #393d35}nav{display:flex;gap:24px;flex-wrap:wrap;font-size:15px}.brand{font-weight:bold;text-decoration:none;letter-spacing:-.04em;font-size:24px}main{padding-top:64px;padding-bottom:80px}h1{font-size:clamp(36px,6vw,76px);line-height:1.04;letter-spacing:-.055em;font-weight:500;margin:20px 0 32px;overflow-wrap:anywhere}h2{font-size:30px;line-height:1.2;font-weight:500;margin:56px 0 24px}h3,h4{line-height:1.3}.lead{font-size:clamp(21px,2.8vw,30px);line-height:1.4;max-width:860px;margin-bottom:48px;color:#cbd0c2}.body{max-width:900px}.body p,.body li{margin-bottom:22px}.body a{overflow-wrap:anywhere}.body img,.body video{display:block;width:100%;height:auto;max-height:720px;object-fit:contain;background:#171817}figure{margin:30px 0}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.gallery figure{margin:10px 0}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.card{display:block;padding:26px;border:1px solid #393d35;text-decoration:none;background:#171817}.card h2{margin:0 0 20px}.card p{font-size:16px;color:#a8aea1}.eyebrow{font-size:13px;color:#c8ec01;text-transform:uppercase;letter-spacing:.1em}.back{display:inline-block;margin:36px 0 0}footer{border-top:1px solid #393d35;font-size:15px;padding-top:32px;padding-bottom:40px}footer a{margin-right:24px}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:#10110f;padding:12px}@media(max-width:600px){header{align-items:flex-start;flex-direction:column}.cards,.gallery{grid-template-columns:1fr}main{padding-top:36px}.body{font-size:17px}}'''
for item in items:item['summary']=descriptions[item['slug']]
(ROOT/'content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
index=re.sub(r'(window.MEDIA_CONTENT=).*?(;?</script>)',lambda m:m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<',chr(92)+'u003c')+';'+m[2].lstrip(';'),index,count=1,flags=re.S)
if 'data-project-page' not in index:
 old='if(Array.isArray(item.blocks)){window.MEDIA_TOOLS.renderBlocks(container,item.blocks,mediaNode);return}'
 new="if(['karst','livecoding','pustotu','angarida'].includes(item.slug)){const link=el('a','text-link','Страница проекта ↗');link.href='/'+item.slug+'.html';link.setAttribute('data-project-page','');const p=el('p');p.append(link);container.append(p);} "+old
 assert index.count(old)==1
 index=index.replace(old,new,1)
def page(filename,title,description,body,schema_type='WebPage',image=None):
 canonical=BASE+filename
 image=image or BASE+'media/a640081616316f353845c1e004c6c9053b931635.png'
 graph={'@context':'https://schema.org','@type':schema_type,'name':title,'description':description,'url':canonical,'inLanguage':'ru-RU','isPartOf':{'@type':'WebSite','name':'Медиакружок','url':BASE}}
 if schema_type=='CreativeWork':graph['publisher']={'@type':'Organization','name':'Медиакружок','url':BASE}
 graph_json=json.dumps(graph,ensure_ascii=False).replace('<',chr(92)+'u003c')
 doc=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} — Медиакружок</title><meta name="description" content="{escape(description,quote=True)}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:locale" content="ru_RU"><meta property="og:site_name" content="Медиакружок"><meta property="og:title" content="{escape(title,quote=True)} — Медиакружок"><meta property="og:description" content="{escape(description,quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{escape(image,quote=True)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title,quote=True)} — Медиакружок"><meta name="twitter:description" content="{escape(description,quote=True)}"><meta name="twitter:image" content="{escape(image,quote=True)}"><script type="application/ld+json">{graph_json}</script><style>{CSS}</style></head><body><a class="skip" href="#content">К содержанию</a><header><a class="brand" href="/">медиакружок</a><nav aria-label="Основная навигация"><a href="/about.html">о сообществе</a><a href="/projects.html">проекты</a><a href="/#contact">связь</a></nav></header><main id="content"><div class="eyebrow">искусство × технологии · Красноярск · Сибирь</div><h1>{escape(title)}</h1>{body}</main><footer><a href="https://t.me/k_media_circle">Telegram</a><a href="https://www.instagram.com/k_media_circle/">Instagram</a><a href="mailto:hello@media-circle.ru">hello@media-circle.ru</a></footer></body></html>'''
 (ROOT/filename).write_text(doc,encoding='utf8')
for i in items:
 slug=i['slug'];title=i['title'];desc=descriptions[slug]
 body='<p class="lead">'+escape(desc)+'</p><article class="body">'+blocks(i.get('blocks',[]),title)+'</article>'
 body+='<a class="back" href="/#'+slug+'">Открыть в интерактивной галерее ↗</a>'
 if slug=='angarida':body+='<p><a href="https://muzey-geologii-tsentralno.timepad.ru/event/4272487/">Актуальная информация и регистрация у организатора ↗</a></p>'
 body+='<h2>Другие проекты</h2><nav>'+''.join('<a href="/'+x['slug']+'.html">'+escape(x['title'])+'</a>' for x in items if x!=i)+'</nav>'
 page(slug+'.html',title,desc,body,'CreativeWork',url((i.get('cover',{}).get('preview') or {}).get('src')) or None)
cards='<div class="cards">'+''.join('<a class="card" href="/'+i['slug']+'.html"><h2>'+escape(i['title'])+'</h2><p>'+escape(descriptions[i['slug']])+'</p></a>' for i in items)+'</div>'
page('projects.html','Проекты Медиакружка','Видеоарт, лайвкодинг, видеомэппинг и аудиовизуальные перформансы сообщества Медиакружок из Красноярска. Описания, авторы и документация проектов.',cards,'CollectionPage')
aboutdesc='Медиакружок — сообщество художников, музыкантов и дизайнеров Сибири. Медиаискусство, генеративные и аудиовизуальные практики, встречи в Красноярске.'
about='<p class="lead">'+aboutdesc+'</p><article class="body">'+blocks(data.get('aboutBlocks',[]),'Медиакружок')+'</article><h2>Как присоединиться</h2><p>Связаться с сообществом и узнать о встречах можно в <a href="https://t.me/k_media_circle">Telegram</a> или по почте <a href="mailto:hello@media-circle.ru">hello@media-circle.ru</a>.</p><h2>Практика сообщества</h2>'+cards
page('about.html','Медиаискусство в Красноярске — о сообществе',aboutdesc,about,'AboutPage')
# Public HTML links work without executing the gallery scripts. Stable hash routes remain intact.
section='''<!-- seo-pages:start --><section aria-label="О сообществе и проектах" style="padding:40px var(--gutter);background:var(--ink);font:16px/1.6 Arial,sans-serif"><p>Медиакружок — медиаискусство и аудиовизуальные практики в Красноярске и Сибири.</p><nav aria-label="Страницы сообщества" style="display:flex;gap:24px;flex-wrap:wrap;margin-top:16px"><a href="/about.html">О сообществе ↗</a><a href="/projects.html">Все проекты ↗</a>'''+''.join('<a href="/'+i['slug']+'.html">'+escape(i['title'])+' ↗</a>' for i in items)+'''</nav></section><!-- seo-pages:end -->'''
if '<!-- seo-pages:start -->' in index:index=re.sub(r'<!-- seo-pages:start -->.*?<!-- seo-pages:end -->',lambda m:section,index,flags=re.S)
else:index=index.replace('    <footer class="contact"',section+'\n    <footer class="contact"',1)
(ROOT/'index.html').write_text(index,encoding='utf8',newline='')
urls=[BASE]+[BASE+f for f in ['about.html','projects.html']+[i['slug']+'.html' for i in items]]
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+x+'</loc></url>' for x in urls)+'</urlset>\n',encoding='utf8')
print('Generated:',', '.join(urls))

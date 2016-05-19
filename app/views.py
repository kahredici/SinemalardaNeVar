from flask import render_template
from bs4 import BeautifulSoup
from imdbpie import Imdb
import requests
from app import app
import operator
import json

imdb = Imdb()

#türkçe karakterler sıkıntı olmasın diye fonksiyon
def utf8_2_ascii(string):
	tab = {"Ö": "O", "ç": "c", "Ü": "U",  "Ç": "C",   "İ": "I",   "ı": "i",
	    "Ğ": "G", "ö": "o", "ş": "s", "ü": "u", "Ş": "S",  "ğ": "g"}
	new_string=""
	for i in string:
		if i in tab:	
			new_string += tab[i]
		else:		
			new_string +=i
	return new_string

@app.route('/')
@app.route('/index')
def index():
	try:
		#veri tabanı json yardımıyla açılıyor
		dosya = open("app/static/db","r")
		db_films = json.loads(dosya.read())
		dosya.close()
	except:
		#eğer data base dosyası yoksa
		open("app/static/db", 'w').close()
		db_films=[]
	
	#db deki film isimleri bulunuyor
	db_film_names = [i['finding_name'] for i in db_films]

	dosya = open("app/static/sinemalar","r")
	siteler = json.loads(dosya.read())
	dosya.close()
	
	#Sinemalardaki filmlerin isimlerini çekiyor
	film_names = set()
	for site in siteler:
		site_html = requests.get(site).content
		soup = BeautifulSoup(site_html, 'html.parser')
		film_divs = soup.find_all(class_="cinema-detail")

		for film_div in film_divs:
			name_div = film_div.find(class_="bestof-detail")
			film_names.add(name_div.find("small").string)
	print("\n --- Sinemadaki film isimleri çekildi. Arama yapılıyor--- ")
	
	film_names = list(film_names)	
	
	#İmdb'den film verileri çekiliyor
	imdbde_olmayan_filmler =[]

	films =[]

	#film internette var db de yoksa
	#internetten veriler çekiliyor films listesine kaydediliyor
	gen = (i for i in film_names if i not in db_film_names)
	for film_name in gen:
		film = {"finding_name":film_name,"finded_name":"","link":"","raiting":None}
		print(film_name+" ' filminin verileri alınıyor")

		try:
			#türkçe karakterler silinip arama linki oluşturup aranıyor
			imdb_search_link = "http://www.imdb.com/find?q={}&s=tt&ref_=fn_al_tt_mr".format(utf8_2_ascii(film_name))
			imdb_search_html = requests.get(imdb_search_link).content
			soup = BeautifulSoup(imdb_search_html,"html.parser")
			table = soup.find(class_="findSection")
			film_imdb_id = table.find(class_="findResult").a['href']
			#link içerisinden id çekiliyor
			film_imdb_id = film_imdb_id[7:16]
		except:
			imdbde_olmayan_filmler.append(film_name)
			continue

		film_get = imdb.get_title_by_id(film_imdb_id)
		#imdb puanını çekme
		temp = film_get.rating
		film['raiting'] = temp

		#imdb isimini çekme
		temp = film_get.title
		film['finded_name'] = temp
		
		#link oluşturma
		temp = "http://www.imdb.com/title/"+film_imdb_id
		film['link']=temp
		films.append(film)

	#film internettede db de de varsa 
	#veriler db den çekiliyor internet boşa yorulmuyor
	gen = (i for i in film_names if i in db_film_names)
	for film_name in gen:
		for k in db_films:
			if k['finding_name'] == film_name:
				films.append(k)

	films.sort(key=operator.itemgetter('raiting'))
	# sıralamayı terse çevirme
	films = [films[i] for i in range(len(films)-1,-1,-1)]
	dosya = open("app/static/db","w")
	dosya.write(json.dumps(films))
	dosya.close()
	print("İşlem Tamam")
	return render_template('index.html',
							films = films,
							not_fond_films=imdbde_olmayan_filmler,
							sites = siteler)

# -*- coding: utf-8 -*-

import MySQLdb as mdb
import MySQLdb.cursors
import datetime

from flask import Flask, render_template

## DB Conf
dbHost = 'localhost'
dbUser = 'root'
dbPassword = None
dbDb = 'MyVideos75'

## Pathing config
thumbRoot = "http://192.168.1.20/xbmcthumbs"

app = Flask(__name__)

@app.route('/')
def home():
  navContext = {'main': 'Home', 'bread': [['/', 'Home']]}
  mediaCount = {'tveps': 0, 'songs': 0}
  totalRunTime = 0
  con = mdb.connect(host = dbHost, user = dbUser, db = dbDb, cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
  cur = con.cursor()
  cur.execute('select c11 as runtime from movie')
  con.close()
  data = cur.fetchall()
  for row in data:
    totalRunTime = totalRunTime + int(row['runtime'])
  mediaCount['movies'] = len(data)
  mediaCount['moviesRunTime'] = datetime.timedelta(0, totalRunTime)
  return render_template('home.html', navContext=navContext, mediaCount=mediaCount)

@app.route('/movies')
def movies():
  navContext = {'main': 'Movies', 'bread': [['/', 'Home'], ['/movies', 'Movies']]}
  info = {}
  con = mdb.connect(host = dbHost, user = dbUser, db = dbDb, cursorclass=MySQLdb.cursors.DictCursor, charset='utf8')
  cur = con.cursor()
  cur.execute('select idMedia from taglinks where idTag = 1 and media_type = "movie"')
  tags = cur.fetchall()
  cur.execute('select idMovie, c07 AS "year", c09 as "imdb", c11 AS "runtime", c16 AS "title", c22 AS "path" from movie')
  movies = cur.fetchall()
  movies = sorted(movies, key=lambda x: x['title'])
  cur.execute('select url, media_id, art_id from art where media_type = "movie" and type = "poster"')
  con.close()
  thumbs = cur.fetchall()
  for item in movies:
    thumb_tuple = [row for row in thumbs if row['media_id'] == item['idMovie']]
    item['runtime'] = "%02d:%02d" % divmod(int(item['runtime']), 60)
    if len(thumb_tuple) > 0:
      item['poster'] = getPoster(thumb_tuple[0]['url'])
    if [row for row in tags if row['idMedia'] == item['idMovie']]:
      item['tagged'] = True
  info['count'] = len(movies)
  return render_template('movies.html', navContext=navContext, movies=movies, info=info)

@app.route('/movie/<moveIdx>')
def movieView(idx):
  
  return 'null'

@app.route('/tvshows')
def tvshows():
  navContext = {'main': 'TV Shows', 'bread': [['/', 'Home'], ['/tvshows', 'TV Shows']]}
  return render_template('tvshows.html', navContext=navContext)
  
@app.route('/music')
def music():
  navContext = {'main': 'Music', 'bread': [['/', 'Home'], ['/music', 'Music']]}
  return render_template('music.html', navContext=navContext)

def getPoster(input_str):
  # TODO: Run through PIL to make small res thumbs? -kevin
  fileHash = get_crc32(input_str)
  poster = '%s/%s/%s.jpg' % (thumbRoot, fileHash[0], fileHash)
  return poster

def get_crc32(string):
  string = string.lower()        
  bytes = bytearray(string.encode())
  crc = 0xffffffff;
  for b in bytes:
      crc = crc ^ (b << 24)          
      for i in range(8):
          if (crc & 0x80000000 ):                 
              crc = (crc << 1) ^ 0x04C11DB7                
          else:
              crc = crc << 1;                        
      crc = crc & 0xFFFFFFFF
  return '%08x' % crc

if __name__ == "__main__":
  app.debug = True
  app.run(host='0.0.0.0', port=9712)
# -*- coding: utf-8 -*-

import datetime
import os
import MySQLdb.cursors

from flask import Flask, render_template
from flaskext.mysql import MySQL
from PIL import Image


## Configs
baseWebRoot = 'http://192.168.1.20/xbmc/'
thumbRoot = '/mnt/data/xbmc/thumbs/'
resizeThumbs = True
resizedThumbRoot = '/var/www/xbmc/thumbs/'
## DB Config
db_host = 'localhost'
db_user = 'xbmc'
db_password = 'xbmc'
db_name = 'MyVideos75'


app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = db_host
app.config['MYSQL_DATABASE_USER'] = db_user
app.config['MYSQL_DATABASE_PASSWORD'] = db_password
app.config['MYSQL_DATABASE_DB'] = db_name
mysql = MySQL()
mysql.init_app(app)


## Routes
@app.route('/')
def home():
    navContext = {'main': 'Home', 'bread': [['/', 'Home']]}
    mediaCount = {'tveps': 0, 'songs': 0}
    movies = getMovies()
    mediaCount['movies'] = len(movies)

    return render_template('home.html', navContext=navContext,
                           mediaCount=mediaCount)


@app.route('/movies')
def movies():
    navContext = {'main': 'Movies', 'bread': [['/', 'Home'],
                                              ['/movies', 'Movies']]}
    info = {}
    movies = getMovies()
    movies = sorted(movies, key=lambda x: x['title'])
    info['count'] = len(movies)
    info['webroot'] = baseWebRoot
    posters = getArt('WHERE type = "poster" AND media_type = "movie"')
    streamDetails = getStreamDetails()
    for item in movies:
        poster = [row for row in posters if row['media_id'] == item['id']]
        if len(poster) > 0:
            item['poster'] = getPoster(poster[0]['url'])
        stream = [row for row in streamDetails
                  if row['idFile'] == item['idFile']]
        item['stream'] = parseStreamDetails(stream)
        duration = item['stream']['video']['duration']
        item['stream']['video']['duration'] = (datetime.timedelta(0,
                                               duration))

    return render_template('movies.html', navContext=navContext, movies=movies,
                           info=info)


@app.route('/movie/<moveIdx>')
def movieView(idx):
    return 'null'


@app.route('/tvshows')
def tvshows():
    navContext = {'main': 'TV Shows', 'bread': [['/', 'Home'],
                                                ['/tvshows', 'TV Shows']]}
    return render_template('tvshows.html', navContext=navContext)


@app.route('/music')
def music():
    navContext = {'main': 'Music', 'bread': [['/', 'Home'],
                                             ['/music', 'Music']]}
    return render_template('music.html', navContext=navContext)


## Database Functions
def getMovies():
    query = ('SELECT idMovie AS id, '
             'c00 AS title, '
             'c01 AS plot, '
             'c02 AS plot_outline, '
             'c03 AS tagline, '
             'c04 AS votes, '
             'c05 AS rating, '
             'c06 AS writers, '
             'c07 AS year, '
             'c08 AS thumbnails, '
             'c09 AS imdb_id, '
             'c10 AS sort_title, '
             'c11 AS runtime, '
             'c12 AS mpaa_ranking, '
             'c13 AS imdb_ranking, '
             'c14 AS genre, '
             'c15 AS director, '
             'c16 AS orig_title, '
             'c18 AS studio, '
             'c19 AS trailer_url, '
             'c20 AS fanart_url, '
             'c21 AS country, '
             'c22 AS path, '
             'c23 AS id_path, '
             'idFile from movie')
    cursor = mysql.get_db().cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    movies = cursor.fetchall()

    return movies


def getArt(where=None):
    query = ('SELECT art_id, '
             'media_id, '
             'media_type, '
             'type, '
             'url from art')
    if where:
        query = query + ' ' + where
    cursor = mysql.get_db().cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    art = cursor.fetchall()

    return art


def getStreamDetails():
    query = ('SELECT idFile, '
             'iStreamType, '
             'strVideoCodec, '
             'fVideoAspect, '
             'iVideoWidth, '
             'iVideoHeight, '
             'strAudioCodec, '
             'iAudioChannels, '
             'strAudioLanguage, '
             'strSubtitleLanguage, '
             'iVideoDuration from streamdetails')
    cursor = mysql.get_db().cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    stream = cursor.fetchall()

    return stream


## Misc Junk Functions
def parseStreamDetails(stream):
    output = {}
    for s in stream:
        if s['iStreamType'] == 0:
            output['video'] = {'codec': s['strVideoCodec'],
                               'duration': s['iVideoDuration'],
                               'height': s['iVideoHeight'],
                               'width': s['iVideoWidth'],
                               'aspect': s['fVideoAspect']}
        elif s['iStreamType'] == 1:
            output['audio'] = {'codec': s['strAudioCodec'],
                               'channels': s['iAudioChannels'],
                               'language': s['strAudioLanguage']}

    return output


def getPoster(url):
    fileHash = get_crc32(url)
    poster = '%s/%s.jpg' % (fileHash[0], fileHash)
    if resizeThumbs:
        gen_thumb(fileHash)

    return poster


def gen_thumb(image):
    origfile = '%s/%s/%s.jpg' % (thumbRoot, image[0], image)
    thumbfile = '%s/%s/%s.jpg' % (resizedThumbRoot, image[0], image)
    exists = os.path.exists(thumbfile)
    if not exists:
        print "Making thumb for %s to %s" % (origfile, thumbfile)
        mkthumb(origfile, thumbfile)


def mkthumb(orig, thumbfile):
    size = 100, 150
    im = Image.open(orig)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(thumbfile)


def get_crc32(string):
    string = string.lower()
    bytes = bytearray(string.encode())
    crc = 0xffffffff

    for b in bytes:
        crc = crc ^ (b << 24)

        for i in range(8):
            if (crc & 0x80000000):
                crc = (crc << 1) ^ 0x04C11DB7

            else:
                crc = crc << 1
        crc = crc & 0xFFFFFFFF

    return '%08x' % crc


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=9712)

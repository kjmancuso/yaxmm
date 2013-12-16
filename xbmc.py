# -*- coding: utf-8 -*-

import datetime
import os

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from PIL import Image

import sqlalchemy as sa
from sqlalchemy.sql.expression import cast

## Configs
db_conf = 'mysql://xbmc:xbmc@localhost/MyVideos75'
thumbWebRoot = 'http://192.168.1.20/xbmc_thumbs'
thumbRoot = '/mnt/data/xbmc/thumbs/'
resizeThumbs = True
resizedThumbRoot = '/var/www/xbmc_thumbs/'


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_conf
db = SQLAlchemy(app)


class NumericString(sa.types.TypeDecorator):
    impl = sa.types.Numeric

    def column_expression(self, col):
        return cast(col, sa.Integer)


class Tag(db.Model):
    __tablename__ = 'tag'

    id = db.Column('idTag', db.Integer, primary_key=True)
    tag = db.Column('strTag', db.Text, unique=True)


class TagLink(db.Model):
    __tablename__ = 'taglinks'

    idTag = db.Column('idTag', db.Integer, db.ForeignKey('tag.id'))
    idMedia = db.Column('idMedia', db.Integer, primary_key=True)
    mediaType = db.Column('media_type', db.Text)


class Art(db.Model):
    __tablename__ = 'art'

    id = db.Column('art_id', db.Integer, primary_key=True)
    media_id = db.Column('media_id', db.Integer)
    media_type = db.Column('media_type', db.Text)
    art_type = db.Column('type', db.Text)
    url = db.Column('url', db.Text)


class StreamDetails(db.Model):
    __tablename__ = 'streamdetails'

    idFile = db.Column('idFile', db.Integer, primary_key=True)
    stream_type = db.Column('iStreamType', db.Integer)
    video_codec = db.Column('strVideoCodec', db.Text)
    video_aspect = db.Column('fVideoAspect', db.Float)
    video_width = db.Column('iVideoWidth', db.Integer)
    video_height = db.Column('iVideoHeight', db.Integer)
    audio_codec = db.Column('strAudioCodec', db.Text)
    audio_channels = db.Column('iAudioChannels', db.Integer)
    audio_lang = db.Column('strAudioLanguage', db.Text)
    subtitle_lang = db.Column('strSubtitleLanguage', db.Text)
    video_duration = db.Column('iVideoDuration', db.Integer)


class Movie(db.Model):
    __tablename__ = 'movie'

    id = db.Column('idMovie', db.Integer, primary_key=True)
    title = db.Column('c00', db.Text)
    plot = db.Column('c01', db.Text)
    plot_outline = db.Column('c02', db.Text)
    tagline = db.Column('c03', db.Text)
    votes = db.Column('c04', db.Text)
    rating = db.Column('c05', db.Text)
    writers = db.Column('c06', db.Text)
    year = db.Column('c07', db.Text)
    thumbnails = db.Column('c08', db.Text)
    imdb_id = db.Column('c09', db.Text)
    sort_title = db.Column('c10', db.Text)
    runtime = db.Column('c11', NumericString)
    mpaa_rating = db.Column('c12', db.Text)
    imdb_ranking = db.Column('c13', db.Text)
    genre = db.Column('c14', db.Text)
    director = db.Column('c15', db.Text)
    orig_title = db.Column('c16', db.Text)
    thumb_spoof = db.Column('c17', db.Text)
    studio = db.Column('c18', db.Text)
    trailer_url = db.Column('c19', db.Text)
    fanart_urls = db.Column('c20', db.Text)
    country = db.Column('c21', db.Text)
    path = db.Column('c22', db.Text)
    id_path = db.Column('c23', db.Text)
    file_id = db.Column('idFile', db.Integer)
    arts = db.relationship(Art, primaryjoin='Movie.id == Art.media_id',
                           foreign_keys='Art.media_id')
    stream = db.relationship(StreamDetails, primaryjoin='Movie.file_id =='
                             ' StreamDetails.idFile',
                             foreign_keys='StreamDetails.idFile')


@app.route('/')
def home():
    navContext = {'main': 'Home', 'bread': [['/', 'Home']]}
    mediaCount = {'tveps': 0, 'songs': 0}
    res = db.session.query(sa.func.count(Movie.id),
                           sa.func.sum(Movie.runtime)).first()
    mediaCount['movies'] = res[0]
    mediaCount['moviesRunTime'] = datetime.timedelta(0, res[1])

    return render_template('home.html', navContext=navContext,
                           mediaCount=mediaCount)


@app.route('/movies')
def movies():
    navContext = {'main': 'Movies', 'bread': [['/', 'Home'],
                                              ['/movies', 'Movies']]}
    info = {}
    movies = Movie.query.order_by(Movie.id)
    info['count'] = movies.count()
    posters = {}
    for item in movies:
        posters[item.id] = getPoster(item.arts)
    return render_template('movies.html', navContext=navContext, movies=movies,
                           info=info, posters=posters)


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


def getPoster(art):
    url = None
    for item in art:
        if item.art_type == 'poster':
            url = item.url
            break
    if url:
        fileHash = get_crc32(url)
        poster = '%s/%s/%s.jpg' % (thumbWebRoot, fileHash[0], fileHash)
    else:
        poster = None
    if resizeThumbs and url:
        gen_thumb(fileHash)
    return poster


def gen_thumb(image):
    origfile = '%s/%s/%s.jpg' % (thumbRoot, image[0], image)
    thumbfile = '%s/%s/%s.jpg' % (resizedThumbRoot, image[0], image)
    exists = os.path.exists(thumbfile)
    if not exists:
        #print "Making thumb for %s to %s" % (origfile, thumbfile)
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

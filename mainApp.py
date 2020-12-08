'''
Author: vvrrww
Project: Movie Recommending Twitter Bot
First written: 10 May 2020
'''

import schedule
import time
from datetime import date
import tweepy
import tmdbsimple as tmdb
import random

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from io import BytesIO

import textwrap

#   Initialize Local File Path
LOCAL_MY_MOVIEDB_PATH = './res/film_db.txt'
LOCAL_PREVIOUSLY_SUGGESTED_MOVIE_PATH = './res/log_previous_day.txt'
LOCAL_PREVIOUS_TWEET_ID_PATH = './res/previous_tweet_id.txt'
LOCAL_HIEWNUNG_FILMID_DB_PATH = './res/hiewnung_ep_film_db.txt'

#
#   ATTENTION:: Add your keys and token before starting
#

#   Initialize Twitter API key, etc.
CONSUMER_KEY = ''
CONSUMER_SECRET_KEY = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''

#   Initialize TMDB API KEY
TMDB_API_KEY = ''
tmdb.API_KEY = TMDB_API_KEY

#   Init all_movies_id
ALL_MOVIES_ID_LIST = list()
FILM_NEVER_DUPLICACTED_LIMIT = 365
TWITTER_STATUS_FORMAT = 'Today ({date}) \n\nWe recommend \"{movie_title} ({movie_year})\"\n#movietwit'
HIEWNUNG_SUFFIX_FORMAT = '\n\nHiewnung podcast once talked about this film.\nCheck it out >> {url}'

#   Image poster path
TO_UPLOAD_PHOTO_TMP_FILE = './res/to_upload.jpg'
DefaultImageSize = 'w500'
TMDB_IMAGE_FORMAT = 'https://image.tmdb.org/t/p/{img_size}/{img_path}'

LOGO_IMG_PATH = './res/W2W_Logo.png'
IMAGE_INNER_W = 2042
IMAGE_INNER_H = 1101
IMAGE_EDGE = 50
IMAGE_W = IMAGE_INNER_W + ( 2 * IMAGE_EDGE )
IMAGE_H = IMAGE_INNER_H + ( 2 * IMAGE_EDGE )

TEMPLATE_BG_COLOR = '#FFFFFF'

TEMPLATE_BORDER_COLOR = '#E9E5D6'

POSTER_EDGE_COLOR = '#E8E6D6'
POSTER_EDGE_SIZE = 3

FILM_TITLE_FORMAT = '{movie_title} ({movie_year})'
DIR_FORMAT = 'dir. {director_name}'
creditStr = '@WhatToWatch_th'

###############################################################

def loadDataFromFileToList( filepath ):
    ''' This function returns file to list
    '''
    myList = list()

    print('loadDataFromFileToList() - Opening \'{}\' file ...'.format(filepath))
    with open(filepath, 'r' ) as f:
        lines = f.read().splitlines()
        for line in lines:
            myList.append(line.strip())
        f.close()
        print('loadDataFromFileToList() - Closed \'{}\' file'.format(filepath))

    return myList

def writeListToFile( myList, filepath ):
    ''' This function writes item in list to file
    '''
    print('writeListToFile() - Opening \'{}\' file ...'.format(filepath))
    file = open(filepath, 'w')
    for item in myList:
        file.write(str(item)+'\n')
    file.close()
    print('writeListToFile() - Closed \'{}\' file'.format(filepath))

def getMovieTMDBNameAndYear( movie_id, supportThai=False ):
    ''' This function connects TMDB API and initialize movie
        If Thai movie, return thai name
        Return movie_name and release_year
    '''
    movie = tmdb.Movies(movie_id)
    response = movie.info()

    movieTitle = movie.title
    movieYear = movie.release_date[:4]

    if supportThai and movie.original_language == 'th':
        movieTitle = movie.original_title

    return movieTitle, movieYear

def getMovieTMDBImagePosterSuffix( movie_id ):
    ''' This function connects TMDB API and initialize movie
        Return moviePathSuffix
    '''
    movie = tmdb.Movies(movie_id)
    response = movie.info()

    moviePathSuffix = movie.poster_path

    return moviePathSuffix

def getMovieTMDBDirectorName( movie_id ):
    ''' This function connects TMDB API and initialize movie
        Return director name list
    '''
    movie = tmdb.Movies(movie_id)
    response = movie.credits()
    directors = [credit['name'] for credit in movie.crew if credit["job"] == "Director"]

    return directors

def addMoreWeightToFilms( initial_id_list ):
    ''' Add chance to random these movie:
        - (A) countries = TH, US, GB, JP
        - (B) year >= 2000
        - (C) mentioned by Hiewnung podcast

        n(normal priority) = 3
        n(A) += 2
        n(B) += 5
        n(C) += 3
    '''
    #   copy list to start
    result_list = list(initial_id_list)

    for film_id in initial_id_list:
        movie = tmdb.Movies(film_id)
        response = movie.info()

        movie_countries = movie.production_countries

        for country in movie_countries:

            #   auto add 2 for every movie
            result_list.append(film_id)
            result_list.append(film_id)

            #   Country priviledge
            country_code = country['iso_3166_1']
            if country_code == 'TH' or country_code == 'US' or country_code == 'GB' or country_code == 'JP':
                result_list.append(film_id)
                result_list.append(film_id)

            #   Year priviledge
            movieYear = movie.release_date[:4]
            if movieYear[0] == 2:
                result_list.append(film_id)
                result_list.append(film_id)
                result_list.append(film_id)
                result_list.append(film_id)
                result_list.append(film_id)

            #   Initialize hiewnung dict
            hiewnungDict = initializeHiewnungURLDict()
            if film_id in hiewnungDict.keys():
                result_list.append(film_id)
                result_list.append(film_id)
                result_list.append(film_id)

    return result_list

def getTodaysDate( withYear=True ):

    today = date.today()
    if withYear:
        date_str = today.strftime("%d %b %Y")
    else:
        date_str = today.strftime("%d %b")
    return date_str

def add_border(input_image, output_image, border, color=0):
    img = Image.open(input_image)
    if isinstance(border, int) or isinstance(border, tuple):
        bimg = ImageOps.expand(img, border=border, fill=color)
    else:
        raise RuntimeError('Border is not an integer or tuple!')
    bimg.save(output_image)

def draw_image_internal( dateStr, movie_id ):

    movie_title, movie_year = getMovieTMDBNameAndYear( movie_id )
    titleStr = FILM_TITLE_FORMAT.format(movie_title=movie_title, movie_year = movie_year)

    #   Create image background
    template_inner_img = Image.new('RGB', (IMAGE_INNER_W, IMAGE_INNER_H), color = TEMPLATE_BG_COLOR)
    template_img = Image.new('RGB', ( IMAGE_W , IMAGE_H ), color = TEMPLATE_BORDER_COLOR )
    template_img.paste(template_inner_img, ( IMAGE_EDGE , IMAGE_EDGE))

    date_fnt = ImageFont.truetype('Prompt-SemiBold.ttf', 71)
    title_fnt = ImageFont.truetype('Prompt-Medium.ttf', 71)
    director_fnt = ImageFont.truetype('Prompt-Italic.ttf', 54)
    credit_fnt = ImageFont.truetype('Prompt-Light.ttf', 36)

    TEXT_CENTER_X = int( IMAGE_W * 2/3 )

    #
    #   Draw logo
    #
    logo = Image.open(LOGO_IMG_PATH)
    logo_w = 202
    logo_h = 202
    logo = logo.resize((logo_w,logo_h))
    logo_x = int( TEXT_CENTER_X - logo_w/2 )
    logo_y = 205
    template_img.paste(logo, (logo_x, logo_y), logo)

    #
    #   Draw credits
    #
    drawCredits = ImageDraw.Draw(template_img)
    creditW, creditH = drawCredits.textsize(creditStr, font=credit_fnt)

    creditPosX = int( TEXT_CENTER_X - creditW/2 )
    creditPosY = logo_y+logo_h+creditH-35
    drawCredits.text( ( creditPosX,creditPosY ), creditStr ,font=credit_fnt, fill='#4E4644')

    #
    #   Draw date
    #
    drawDate = ImageDraw.Draw(template_img)
    dateW, dateH = drawDate.textsize(dateStr, font=date_fnt)

    datePosX = int( TEXT_CENTER_X - dateW/2 )
    datePosY = creditPosY+creditH+60
    drawDate.text(( datePosX,datePosY ), dateStr ,font=date_fnt, fill='#37302F')

    #
    #   Draw Title
    #
    drawTitle = ImageDraw.Draw(template_img)
    titleW, titleH = drawTitle.textsize('example_height', font=title_fnt)

    para = textwrap.wrap(titleStr, width=30)
    current_h, pad = datePosY+dateH, 10
    for line in para:
        w, h = drawTitle.textsize(line, font=title_fnt)
        drawTitle.text((int( TEXT_CENTER_X - w/2 ), current_h), line, font=title_fnt, fill='#E3232F')
        current_h += h + pad

    #
    #   Draw Director
    #

    #   get dir list
    dir_list = getMovieTMDBDirectorName( movie_id )
    dir_str = DIR_FORMAT.format(director_name=', '.join(dir_list))


    #   draw from bottom
    para = textwrap.wrap(dir_str, width=40)
    current_h, pad = int( IMAGE_H - 194 ), 10
    for index in range(len(para)-1,-1,-1):
        w, h = drawTitle.textsize(para[index], font=director_fnt)
        drawTitle.text((int( TEXT_CENTER_X - w/2 ), current_h), para[index], font=director_fnt, fill='#E3232F')
        current_h -= (h + pad)

    #
    #   Draw Poster
    #
    tmdb_poster_suffix = getMovieTMDBImagePosterSuffix( movie_id )
    img_url = TMDB_IMAGE_FORMAT.format(img_size=DefaultImageSize,img_path=tmdb_poster_suffix)
    response = requests.get(img_url)

    poster_img = Image.open(BytesIO(response.content))

    POSTER_WIDTH = 643
    POSTER_HEIGHT = int(poster_img.height * POSTER_WIDTH / poster_img.width )

    poster_img = poster_img.resize( ( POSTER_WIDTH , POSTER_HEIGHT ))

    #   poster with border
    new_size = (POSTER_WIDTH+(2*POSTER_EDGE_SIZE), POSTER_HEIGHT+(2*POSTER_EDGE_SIZE))
    poster_border_img = Image.new("RGB", new_size, color = POSTER_EDGE_COLOR)
    poster_border_img.paste(poster_img, (POSTER_EDGE_SIZE, POSTER_EDGE_SIZE))

    POSTER_X = int( ( IMAGE_H - poster_border_img.height ) / 2 )
    POSTER_Y = int((IMAGE_H*0.5) - (poster_border_img.height*0.5))

    template_img.paste(poster_border_img, (POSTER_X, POSTER_Y))


    template_img.save(TO_UPLOAD_PHOTO_TMP_FILE,'jpeg')

###############################################################

#   Authenticate Twitter API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitterApi = tweepy.API(auth)

def prepare_image( movie_id, dateStr ):

    draw_image_internal( dateStr, movie_id )

def upload_with_media( movieName, movieYear, img_file_path, dateStr, hiewnung_url = None ):

    status_text = TWITTER_STATUS_FORMAT.format(date = dateStr, movie_title=movieName, movie_year=movieYear)

    if hiewnung_url != None:
        status_text += HIEWNUNG_SUFFIX_FORMAT.format( url = str(hiewnung_url) )

    ret = twitterApi.media_upload(img_file_path)
    tweet = twitterApi.update_status(status_text,
                      media_ids=[ret.media_id])
    print('Uploaded: \"{movieName} ({movieYear})\"'.format(movieName=movieName, movieYear=movieYear))
    return tweet.id

def upload( movieName, movieYear ):
    ''' This function update status in the following format 'MovieName (year)'
        e.g. 'The Matrix (1996)'
    '''
    today = getTodaysDate(withYear=False)

    status_text = TWITTER_STATUS_FORMAT.format(date = today, movie_title=movieName, movie_year=movieYear)

    tweet = twitterApi.update_status(status_text)
    print('Uploaded: \"{movieName} ({movieYear})\"'.format(movieName=movieName, movieYear=movieYear))
    return tweet.id


def initializeMyMovieDB():
    ''' Load movie_ids from local file
    '''
    return loadDataFromFileToList( LOCAL_MY_MOVIEDB_PATH )

def initializeHiewnungURLDict():
    ''' Return dict that maps movie_id to Hiewnung ep URL
    '''

    #   Initialize dict
    filmId_HiewungURL_dict = dict()

    #   Open file
    file = open(LOCAL_HIEWNUNG_FILMID_DB_PATH, 'r')

    #   Loop all movie_id and add to dict
    for line in file:
        line_list = line.strip().split()
        movie_ids = line_list[1:]
        for movie_id in movie_ids:
            filmId_HiewungURL_dict[movie_id] = line_list[0]

    #   Close file
    file.close()

    #   Return dict
    return filmId_HiewungURL_dict

def getFilmListToRandom( ALL_MOVIES_ID_LIST, amount = 1 ):
    ''' This function select an item from list randomly
        Return - randomized item
    '''

    #   whole id
    whole_id_set = set(ALL_MOVIES_ID_LIST)

    #   get previous logged film history
    previous_film_set = set(loadDataFromFileToList( LOCAL_PREVIOUSLY_SUGGESTED_MOVIE_PATH ))

    #   not_recently_uploaded_film
    film_candidates_list = list( whole_id_set.difference(previous_film_set) )

    #   random as amount
    result_list = random.sample( film_candidates_list , amount)

    return result_list

def write_uploaded_film_to_log( movie_id ):
    ''' Add film to log. Limit to amount
        For log, front is the latest
    '''

    #   load log list
    logged_list = loadDataFromFileToList( LOCAL_PREVIOUSLY_SUGGESTED_MOVIE_PATH )

    #   add movie_id to front of list
    logged_list.insert(0,movie_id)

    #   check exceed limit
    if len(logged_list) > FILM_NEVER_DUPLICACTED_LIMIT:
        writeListToFile( logged_list[0:FILM_NEVER_DUPLICACTED_LIMIT], LOCAL_PREVIOUSLY_SUGGESTED_MOVIE_PATH )
    else:
        writeListToFile( logged_list, LOCAL_PREVIOUSLY_SUGGESTED_MOVIE_PATH )

def doDailyUpdate( dateStr = None ):
    ''' Update tweet daily
    '''

    #   if not specified dateStr, let dateStr be today
    if dateStr == None:
        dateStr = getTodaysDate( withYear = False )

    #   load film list again in case film db changed
    ALL_MOVIES_ID_LIST = initializeMyMovieDB()

    #   initialize hiewnung dict
    HIEWNUNG_URL_DICT = initializeHiewnungURLDict()

    #   random 5 movies from list
    movie_ids_list = getFilmListToRandom(ALL_MOVIES_ID_LIST, amount = 5)
    print('movies candidates = {}'.format(movie_ids_list))

    #   add more weight to films for random
    movie_ids_for_random = addMoreWeightToFilms(movie_ids_list)
    print('priviledged candidates = {}'.format(movie_ids_for_random))

    #   get film
    movie_id = random.sample( movie_ids_for_random, 1 )[0]
    print('selected film id = {}'.format(movie_id))

    #   get movie title and year
    movie_title, movie_year = getMovieTMDBNameAndYear(movie_id, supportThai=True )

    #   prepare image to tweet
    prepare_image( movie_id, dateStr )

    #   check if Hiewnung ever talked about this film
    hiewnungURL = None
    if movie_id in HIEWNUNG_URL_DICT.keys():
        hiewnungURL = HIEWNUNG_URL_DICT[movie_id]

    #   tweet!
    tweet_id = upload_with_media( movie_title, movie_year, TO_UPLOAD_PHOTO_TMP_FILE, dateStr, hiewnung_url=hiewnungURL )
    # upload( movie_title, movie_year )

    #   save tweet
    writeListToFile( [tweet_id], LOCAL_PREVIOUS_TWEET_ID_PATH )

    #   add film to log
    write_uploaded_film_to_log( movie_id )

def retweetDaily():
    ''' Retweet today daily's update
    '''

    #   read today tweet id
    tweet_ids = loadDataFromFileToList( LOCAL_PREVIOUS_TWEET_ID_PATH )

    try:
        #   retweet
        twitterApi.retweet(int(tweet_ids[0]))
    except:
        print('Cannot retweetDaily')

def unretweetDaily():
    ''' Unretweet today daily's update
    '''

    #   read today tweet id
    tweet_ids = loadDataFromFileToList( LOCAL_PREVIOUS_TWEET_ID_PATH )

    try:
        #   unretweet
        twitterApi.unretweet(int(tweet_ids[0]))
    except:
        print('Cannot unretweetDaily')

if __name__ == '__main__':

    #   Run doDailyUpdate every day at 9AM BKK time
    schedule.every().day.at("02:00").do(doDailyUpdate)

    #   retweet every 12PM and 7PM
    schedule.every().day.at("05:00").do(retweetDaily)
    schedule.every().day.at("11:55").do(unretweetDaily)
    schedule.every().day.at("12:00").do(retweetDaily)
    schedule.every().day.at("17:00").do(unretweetDaily)

    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute


import re
import tmdbsimple as tmdb

file_to_add = './res/film_to_add_name_list.txt'
db_file = './res/film_db.txt'

#   Initialize TMDB API KEY
TMDB_API_KEY = '' # Add your key here
tmdb.API_KEY = TMDB_API_KEY

year_regex = '[1-2][0-9]{3}'

def extract_year( full_film_string, start_index=0 ):
    ''' This functions get title string and year, e.g. "Interstellar (2014)"
        Return - titleName = Interstellar
                - year = 2014
    '''

    film_string = full_film_string[ start_index: ]
    parenIndex = film_string.find('(')

    if parenIndex == -1:
        return None
    else:
        yearCandidate = film_string[ parenIndex+1:parenIndex+5 ]

        #   match year pattern
        result = re.match( year_regex, yearCandidate)

        if result != None:
            return full_film_string[:start_index+parenIndex].strip(), yearCandidate
        else:
            return extract_year( full_film_string, start_index=start_index+parenIndex+1 )

def getIdFromTileAndYear( film_title, film_year ):
    ''' Return - get tmdb id list that query and match year
    '''
    int_film_year = int(film_year)
    search = tmdb.Search()

    response = search.movie(query=film_title, include_adult=False, year=film_year)

    #   Not found
    if len(search.results) == 0:
        return list()
    else:
        filmList = list()
        for s in search.results:
            filmList.append( s['id'] )
        return filmList

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

def waitUserAnswer( film_id_list, film_string ):
    ''' Return - correct film id
    '''
    film_name_choice_string = ''

    for i in range(1,len(film_id_list)+1):
        movie = tmdb.Movies(film_id_list[i-1])
        response = movie.info()
        film_name_choice_string += '{}: {} ({}) {{id={}}}\n'.format(i, movie.title, movie.release_date[:4], film_id_list[i-1])
    print('='*20)
    print('\nPlease choose film that matches \'{}\''.format(film_string))
    index = int(input(film_name_choice_string+'0: No match at all\n>Choose (num): '))

    if index == 0:
        return None
    return film_id_list[index-1]

def write_id_to_file( file_path, id_list ):

    id_str_list = [str(a) for a in id_list]

    whole_string = '\n' + '\n'.join(id_str_list)
    file = open(file_path,'a')
    file.write( whole_string )
    file.close()


if __name__=='__main__':

    film_string_list = loadDataFromFileToList( file_to_add )
    film_id_to_add = list()
    film_with_no_match = list()
    for film_string in film_string_list:
        title, year = extract_year(film_string)
        film_id_list = getIdFromTileAndYear( title, year )
        if len(film_id_list) == 0:
            film_with_no_match.append(film_string)
            print( 'Not match' )
        elif len(film_id_list) == 1:
            print( 'Added id = {}'.format(film_id_list[0]))
            film_id_to_add.append(film_id_list[0])
        else:
            film_id = waitUserAnswer( film_id_list, film_string )
            if film_id != None:
                print( 'Added id = {}'.format(film_id))
                film_id_to_add.append(film_id)
            else:
                film_with_no_match.append(film_string)
                print( 'Not match' )
    print('|'*30)
    if len(film_with_no_match) != 0:
        print('\nFilm without a match = {}'.format(film_with_no_match))


    write_id_to_file( db_file, film_id_to_add )
    print('\nAdded id = {}'.format(film_id_to_add))

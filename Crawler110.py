# Crawler 1.1.0.
# 26 June 2016 
# A simple URL Crawler & Link Resolver with database storage and
# options to crawl within home domain only or to roam more freely

#################################################################
###                                                           ###
###   PLEASE UPDATE HARD CODED URL & HOME DOMAIN (L99, L133)  ###
###                                                           ###
#################################################################


# import libraries
import urllib
import sqlite3
from bs4 import *
import time
import datetime
import re


# FUNCTION: drop database
def drop(curs):
    drp = raw_input('Reset database to empty (Y/N): ')
    if drp.lower() == 'n' or len(drp) < 0 : pass
    elif drp.lower() == 'y' :
        curs.executescript('''
            DROP TABLE IF EXISTS Doc;
            DROP TABLE IF EXISTS Url;
            DROP TABLE IF EXISTS Link;
            DROP TABLE IF EXISTS Pair;
            DROP TABLE IF EXISTS Home;
            DROP TABLE IF EXISTS Excl
            ''')
        conn.commit()


# FUNCTION: create database
def create(curs):
    curs.executescript('''
    CREATE TABLE IF NOT EXISTS Doc (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Url_id  INTEGER,
        fetch   DATE,
        err     INTEGER,
        raw     TEXT,
        read    INTEGER
    );
    
    CREATE TABLE IF NOT EXISTS Url (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        url     TEXT UNIQUE,
        home    TEXT,
        excl    TEXT,
        crwl    INTEGER,
        fetch   INTEGER,
        path    INTEGER
    );
    
    CREATE TABLE IF NOT EXISTS Link (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        link    TEXT UNIQUE,
        anchor  TEXT,
        Doc_id  INTEGER
    );
    
    CREATE TABLE IF NOT EXISTS Pair (
        Doc_id  INTEGER,
        Link_id INTEGER,
        PRIMARY KEY (Doc_id, Link_id)
    );
    
    CREATE TABLE IF NOT EXISTS Home (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        domain  TEXT UNIQUE
    );
    
    CREATE TABLE IF NOT EXISTS Excl (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        domain  TEXT
    );
    
    ''')
    conn.commit()


# FUNCTION: user-defined parameters
def start():
    url = None; path = None ; strt = None
    print '\n\n+++++'
    print 'Enter URL / RTN (default URL) / NUM (retrieve N URLs from database) / Q (quit)'
    inp = raw_input(': ')
    if inp.lower() == 'q' : pass
    try:
        num = int(inp)
        url = None; path = None ; strt = 'no'
    except:
        if len(inp) < 1 :
            url = 'http://www.domainname.com/'          ### UPDATE DEFAULT URL HERE ###
            num = 1 ; path = 0 ; strt = 'yes'
        else:
            url = inp; num = 1 ; path = 0 ; strt = 'yes'
    return {'inp': inp, 'url': url, 'num': num, 'path': path, 'start': strt}


def valid(url):
    if url != None :
        while True:
            if re.search('^http.*://', url) : break
            print 'Please enter a valid URL in the format http://www.domainname.com'
            url = raw_input(': ')
    return url


# FUNCTION: stay in home domain only?
def stay():
    inp = raw_input('\nCrawl in home domain only? (Y/N): ')
    if inp.lower() == 'n' :
        stay = 'no'
    elif inp.lower() == 'y' :
        stay = 'yes'
    else:
        print 'Roaming freely (enter excluded domains to restrict)'
        stay = 'no'
    print 'Staying:', stay
    return stay


# FUNCTION: set home domain
def homedomain():
    inp = raw_input('Enter home domain (RTN for default): ')
    if len(inp) < 1 :
        homedomain = 'domainname.com'                   ### UPDATE DEFAULT HOME DOMAIN HERE ###
    else:
        homedomain = inp
    print 'Home domain:', homedomain
    curs.execute('''INSERT OR IGNORE INTO Home (domain) 
            VALUES ( ? )''', ( homedomain, ) )
    conn.commit()
    return homedomain


# FUNCTION: domain exclusions
def exclude(curs):
    exc = ''
    while True:
        exc = raw_input('\nEnter domain to exclude from crawl (Q to quit): ')
        if exc.lower() == 'q' : break
        if re.search('^http://', exc) : exc = exc.strip('http://')
        if re.search('^https://', exc) : exc = exc.strip('https://')
        if re.search('^www.', exc) : exc = exc[(exc.find('www.'))+4:]
        if re.search('/$', exc) : exc = exc.rstrip('/')
        curs.execute('''INSERT OR IGNORE INTO Excl (domain) 
            VALUES ( ? )''', ( exc, ) )
        print 'Cleaned domain:', exc
    conn.commit()


# FUNCTION: url error handling and clean-up
def clean(url):
    if not url.startswith('http://') and not url.startswith('https://') :
        url = 'http://'+url
    if url.endswith('/') : url = url[:-1]
    return url


# FUNCTION: crawl URL and store HTML to database
def docrawl(url):
    
    # crawl web page and parse raw HTML data
    print '\nCrawling:', url
    html = urllib.urlopen(url).read()
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%dT%H:%M')
    print 'Fetched:', timestamp

    # store raw HTML in database Table:Doc and update tracking values
    curs.execute('''INSERT OR IGNORE INTO Doc (Url_id, fetch, raw, read) 
        VALUES ( ?, ?, ?, 0 )''', ( url_id, timestamp, buffer(html) ) )
    curs.execute('SELECT id FROM Doc WHERE Url_id = ? ', (url_id, ))
    doc_id = curs.fetchone()[0]
    curs.execute('UPDATE Url SET crwl=1 WHERE url=?', (url, ) )
    curs.execute('UPDATE Url SET fetch=1 WHERE url=?', (url, ) )
    conn.commit()
    
    print 'ADDED Url_ID / DocID:', url_id, doc_id
    print 'Raw Html:'
    print html[:50]
    return doc_id


# FUNCTION: don't crawl (excluded domain or not in home domain)
def nocrawl(url):
    curs.execute('SELECT id FROM Url WHERE url = ? ', (url, ))
    url_id = curs.fetchone()[0]
    curs.execute('UPDATE Url SET crwl=1 WHERE id=?', (url_id, ) )
    curs.execute('''UPDATE Url SET home='no' WHERE id=?''', (url_id, ) )
    conn.commit()


# FUNCTION: URL Resolver
def resolve(doc_id,url_id):
    curs.execute('SELECT raw FROM Doc WHERE id = ? ', (doc_id, ))
    html = curs.fetchone()[0]
    soup = BeautifulSoup(html, 'html.parser')
    print '\nRetrieving all links...'
    links = soup('a')
    for item in links :
        if re.search('^<a href=', str(item)) :
            www = item.get('href')
            anc = re.findall('>(.+)<', str(item))
            try:
                if re.search('[<>]', anc[0]) :
                    anc = re.findall('>(.+)<', anc[0])
            except:
                pass
            if www.endswith('/') :
                www = www[:-1]
            
        # error-handling: throwing away bad links
        thrw = throw(item)
        #if thrw == 1 :
        #    print '\nThrowing away:', str(item)[:50]
            
        # add good links to database Table:Link
        if thrw == 0 :
            #print '\nGood link:', www, anc[0]
            curs.execute('''INSERT OR IGNORE INTO Link (link, anchor, Doc_id)
                VALUES (?, ?, ? )''', (www, buffer(anc[0]), doc_id) )
            curs.execute('SELECT id FROM Link WHERE link = ?', (www, ) )
            link_id = curs.fetchone()[0]
    
            # update link pairs to Junction Table:Pair
            curs.execute('''INSERT OR IGNORE INTO Pair (Doc_id, Link_id)
                VALUES (?, ? )''', (doc_id, link_id) )
            conn.commit()
            
            # calculate path
            curs.execute('SELECT path FROM Url WHERE id = ?', (url_id, ) )
            path = curs.fetchone()[0]
            
            # check and add good URLs + path to Table:Url
            curs.execute('SELECT id FROM Url WHERE url = ?', (www, ) )
            if curs.fetchall() == [] :
                path = path + 1
                print 'ADDING:', www
                curs.execute('''INSERT OR IGNORE INTO Url (url, crwl, fetch, path) 
                    VALUES ( ?, 0, 0, ? )''', ( www, path ) )
            conn.commit()


# FUNCTION: throw away bad links (URL Resolver)
def throw(item):
    if re.search('wp-content', str(item)) : thrw = 1
    elif re.search('.*class=', str(item)) : thrw = 1
    elif re.search('[#]', str(item)) : thrw = 1
    elif re.search('jpg', str(item)) : thrw = 1
    elif re.search('.*#', str(item)) : thrw = 1
    elif not re.search('http', str(item)) : thrw = 1
    else:
        thrw = 0
    return thrw


#################################################################

# create SQL database DB01 RawData
conn = sqlite3.connect('DB01RawData.db')
curs = conn.cursor()

# drop/create database
drop(curs)
create(curs)

# user-defined set-ups
stay = stay()
homedomain = homedomain()
if stay != 'yes' :
    exclude(curs)

# main program
while True:
    result = start()
    if result['inp'].lower() == 'q' : quit()
    url = result['url'] ; num = result['num'] ; path = result['path'] ; strt = result['start']
    url = valid(url)
    
    # add starting URL to database
    if strt == 'yes' :
        print 'Starting URL:', url
        
        # error handling: clean URL
        url = clean(url)
        print 'Cleaned URL:', url
        
        # set Home Domain and Excluded Domain flags
        home = 'yes' ; excl = 'no'

        # add starting URL to database Table:Url
        curs.execute('''INSERT OR IGNORE INTO Url (url, home, excl, crwl, fetch, path) 
            VALUES ( ?, ?, ?, 0, 0, ? )''', ( url, home, excl, path ) )
        curs.execute('SELECT id FROM Url WHERE url = ? ', (url, ))
        url_id = curs.fetchone()[0]
        conn.commit()

    # loop through all database additions (starting url + user-defined num)
    while True:
        if num < 1 : break
        
        # retrieve next URL from database Table:Url
        curs.execute('SELECT url FROM Url WHERE crwl = 0 ORDER BY id LIMIT 1')
        result = curs.fetchone()
        if result is None :
            print 'No uncrawled URLs found'
            break
        url = result[0]
        curs.execute('SELECT id FROM Url WHERE url = ? ', (url, ))
        url_id = curs.fetchone()[0]
        curs.execute('SELECT home FROM Url WHERE id = ? ', (url_id, ))
        home = curs.fetchone()[0]
        
        # check if URL is in Home Domain, set home flag and update to Table:Url
        if home == None :
            if re.search(str(homedomain), str(url)) :
                home = 'yes'
                curs.execute('''UPDATE Url SET home='yes' WHERE id=?''', (url_id, ) )
            else :
                home = 'no'
                curs.execute('''UPDATE Url SET home='no' WHERE id=?''', (url_id, ) )
        
        # check if URL is an Excluded Domain, set excl flag and update to Table:Url
        curs.execute('SELECT domain FROM Excl ORDER BY id')
        result = curs.fetchall()
        print '\n\n+++++Result:', result
        if result is None or result == [] :
            print 'No domains to exclude'
            excluded = None
        else:
            for item in result :
                domain = item[0]
                if re.search(str(domain), str(url)) :
                    excluded = 'yes'
                    break
                else:
                    excluded = 'no'
        print 'Exclude domain?', excluded
        
        if excluded == 'yes' :
            curs.execute('''UPDATE Url SET excl='yes' WHERE id=?''', (url_id, ) )
        if excluded == 'no' :
            curs.execute('''UPDATE Url SET excl='no' WHERE id=?''', (url_id, ) )
        
        # check user-defined parameters: stay in home domain only?
        # + excluded domains (calling function DOCRAWL or NOCRAWL)
        if excluded == 'yes' :
            print "Not crawled (excluded domain):", url_id, url
            nocrawl(url)
        else:
            if stay == 'yes' and home == 'no' :
                print "Not crawled (not in home domain):", url_id, url
                nocrawl(url)
            elif stay == 'yes' and home == 'yes' :
                print 'Crawling (in home domain):', url_id, url
                doc_id = docrawl(url)
            else:
                print 'Crawling (freedom is mine):', url_id, url
                doc_id = docrawl(url)
        
        # fetch and raw data storage completed; update num
        num = num - 1
        
        ### IMPROVEMENT: check if raw HTML is OK or err
        ### update Table:Doc.err accordingly
        ### only move onto URL Resolver where not an error
        
        # URL Resolver: parse all URLs + anchor text and write to database
        if not excluded == 'yes' :
            if stay == 'yes' and home == 'no' :
                print 'No links to resolve'
            else:
                print '\nResolving links...'
                print doc_id, url_id, url
                resolve(doc_id,url_id)

    print 'All retrieved'

curs.close()
quit()

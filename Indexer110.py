# Indexer 1.1.0
# 10 July 2016 
# Part of a simple Search Engine Application
# Parses unique words from raw HTML, analyses word frequencies
# + other attributes, and calculates word relevancy scores.


# import libraries
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
            DROP TABLE IF EXISTS Hits;
            DROP TABLE IF EXISTS Cats;
            DROP TABLE IF EXISTS Tags;
            DROP TABLE IF EXISTS Auth
            ''')
        conn.commit()

# FUNCTION: create database
def create(curs):
    curs.executescript('''
        CREATE TABLE IF NOT EXISTS Doc (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        DB1_Doc_id   INTEGER UNIQUE,
        url     TEXT UNIQUE,
        fetch   DATE,
        authy   INTEGER,
        year    INTEGER,
        mnth    INTEGER,
        ttl     TEXT
        );
        
        CREATE TABLE IF NOT EXISTS Hits (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        DB1_Doc_id  INTEGER,
        word    TEXT,
        hits    INTEGER,
        pos     INTEGER,
        size    INTEGER,
        caps    INTEGER,
        bold    INTEGER,
        inurl   INTEGER,
        inttl   INTEGER,
        inanch  INTEGER,
        relev   INTEGER
        );
    
        CREATE TABLE IF NOT EXISTS Cats (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        DB1_Doc_id  INTEGER,
        cat     TEXT UNIQUE,
        parent  TEXT,
        child   TEXT
        );
        
        CREATE TABLE IF NOT EXISTS Tags (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        DB1_Doc_id  INTEGER,
        tag     TEXT UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS Auth (
        id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        domain  TEXT UNIQUE,
        auth    INTEGER
        );
        
    ''')
    conn.commit()

# FUNCTION: fix encoding errors
Map = {u'\u2019':"'", u'\u2018':"`", u'\u2026':" ", u'\u2013':"-", u'\u201c':'"', u'\u201d':'"', u'\xa0':" " }
def unicodeToAscii(item):
    try:
        return str(item)
    except:
        pass
    cleaned = ""
    for i in item:
        try:
            cleaned = cleaned + str(i)
        except:
            if Map.has_key(i):
                cleaned = cleaned + Map[i]
            else:
                try:
                    print "unicodeToAscii: add to map:", i, repr(i), "(encoded as _)"
                except:
                    print "unicodeToAscii: unknown code (encoded as _)", repr(i)
                cleaned = cleaned + "_"
    return cleaned

# FUNCTION: extract categories
def cats(url):
    print '\nSearching for categories...'
    if re.search('/category/', url) :
        cat = re.findall('/category/(.*)', url)[0]
        cat = cat.replace('/',': ').replace('-',' ')
    else:
        cat = None
    return cat


# FUNCTION: extract tags
def tags(url):
    print '\nSearching for tags...'
    if re.search('/tag/', url) :
        tag = re.findall('/tag/(.*)', url)[0]
        tag = tag.replace('/',': ').replace('-',' ')
    else:
        tag = None
    return tag


# FUNCTION: extract title and month/year
def title(url):
    print '\nExtracting title...'
    if re.search('/201./', url) :
        ttldate = re.findall('(/201./.*)', url)[0]
        year = ttldate[1:5]
        mnth = re.findall('/201./(.*)', ttldate)[0][:2]
        try:
            ttl = re.findall('/201./'+mnth+'/(.*)', ttldate)[0].replace('-',' ')
        except:
            ttl = None
    else:
        year = None ; mnth = None; ttl = None
    return year, mnth, ttl

# FUNCTION: check and clean up word (excludes bad data and specific words)
includables = ['R', 'C#', 'I', 'a' ]
excludables = ['7/library/functions', "<type'str'>", '\rtools', '/cross', '/pagename', '/semi', '/up', "`abcdefghij'", "'xxx'", 'count1a', 'count1a2a', 'count1a2b', 'count1b', 'count2a2a', 'hdf5', "hoo!'", 'horton', 'html#stringhtml', '/css', 'html5', 'http', 'https', 'husz_r', 'ii', 'iii', 'iv', 'jre', 'jvm', 'kdd', 'l1', 'l2', 'l3', 'l4', 'l5', 'org/', 'org/2', 'org/2/library/stdtypes', 'org/web/packages/btyd/index', 'v2', 'v3', 'v6', 'val', 'vali', 'xl', 'xp', 'xxx', "</person>''", '<email', '</website>', '<website', '<person>', '<name>', '</name>', "</person>''", '</phone>', '<phone', '<name>chuck</name>', '</recipe>', '2_>leave', '1_>cook', '</instructions>', '4_>roll', '2_>beat', '</step>', '<step', '1_>cream', '<instructions', '<summary', '<summary>', '>egg</ingredient>', '>sugar</ingredient>', '>butter</ingredient>', '>flour</ingredient>', '<ingredient', 'pastry</title>', '<title>rich', '6_>', '<lname>roberts</lname>', '<fname>deb</fname>', '<lname>', '</fname>', '<fname>', '<person>', '</person>', '<p>i', 'me<h1>', '<h1', 'here}</a>', '>{some', 'href', '<span', '000080', 'color', 'style', '1</sub>', '1</sup>' ] 
charset = ["'", "`", "_", "#", "*", "{", '"', "%", "/", "}", ";", "!", "?", "/" ]
charset1 = ["!!", "//", "##", "''"]
nums = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
def check(word):
    incexc = '' ; newword = word
    exit = 0
    while True:
        if exit == 1 :
            return newword, incexc
            break
        
        # include specific words
        if word in includables :
            newword = None ; incexc = 'inc'
            exit = 1
        
        # exclude specific words
        if word.lower() in excludables :
            newword = None ; incexc = 'exc'
            exit = 1

        # trim non-alpha characters from start and end
        for char in charset :
            if word.startswith(char) :
                word = word[1:len(word)]
                newword = word ; incexc = 'inc'
            if word.endswith(char) :
                word = word[:len(word)-1]
                newword = word ; incexc = 'inc'
        for char1 in charset1 :
            if word.endswith(char1) :
                word = word[:len(word)-2]
                newword = word ; incexc = 'inc'
    
        # trim numerics where length is two or less characters
        if len(word) <= 2 :
            for num in nums :
                if word.startswith(num) :
                    word = word[1:len(word)]
                    newword = word ; incexc = 'inc'
                if word.endswith(num) :
                    word = word[:len(word)-1]
                    newword = word ; incexc = 'inc'
        
        # exclude if word is <= 1 character long
        if len(word) <= 1 :
            newword = None ; incexc = 'exc'
            exit = 1
                
        exit = 1



# FUNCTION: strip categories into parent and child
def catsplit(curs):
    inp = raw_input('\nSplit categories into parent and child? (Y/N) ')
    if inp.lower() == 'y' or len(inp) < 1 :
        curs.execute('''SELECT id, DB1_Doc_id, cat FROM Cats WHERE parent IS NULL ORDER BY id''')
        categories = curs.fetchall()
        if categories == [] :
            print 'No results found'
        else:
            print len(categories), 'results found'
            for (id, doc_id, category) in categories :
                category = str(category)
                pos = category.find(': ')
                if pos > 0 :
                    parent = category[:pos]
                    child = category[pos+2:]
                else:
                    parent = category
                    child = None
                print parent, ' - ', child
                curs.execute('''REPLACE INTO Cats (id, DB1_Doc_id, cat, parent, child )
                    VALUES (?, ?, ?, ?, ? )''', (id, doc_id, category, parent, child) )
    conn.commit()


# FUNCTION: process and update relevancy score
def relev(curs):
    inp = raw_input('\nUpdate relevancy scores? (Y/N) ')
    if inp.lower() == 'y' or len(inp) < 1 :
        curs.execute('''SELECT id, DB1_Doc_id, word, hits, pos, size, caps, bold, inurl, inttl, inanch
            FROM Hits WHERE relev IS NULL ORDER BY id''')
        records = curs.fetchall()
        if records == [] :
            print 'No results found'
        else:
            print len(records), 'results found'
            for (id, doc_id, word, hits, pos, size, caps, bold, inurl, inttl, inanch) in records :
                relev = 0 ; score = 0
            
                # hits score
                if hits <= 0 : score = 0
                elif hits > 0 and hits < 25 : score = hits
                elif hits >= 25 : score = 25
                else: score = 0
                relev = relev + score
                
                # pos score
                score = 0
                if pos <= 0 or pos > 10000 : score = 0
                elif pos > 0 and pos < 501 : score = 20
                elif pos > 500 and pos < 1001 : score = 19
                elif pos > 1000 and pos < 1501 : score = 18
                elif pos > 1500 and pos < 2001 : score = 17
                elif pos > 2000 and pos < 2501 : score = 16
                elif pos > 2500 and pos < 3001 : score = 15
                elif pos > 3000 and pos < 3501 : score = 14
                elif pos > 3500 and pos < 4001 : score = 13
                elif pos > 4000 and pos < 4501 : score = 12
                elif pos > 4500 and pos < 5001 : score = 11
                elif pos > 5000 and pos < 5501 : score = 10
                elif pos > 5500 and pos < 6001 : score = 9
                elif pos > 6000 and pos < 6501 : score = 8
                elif pos > 6500 and pos < 7001 : score = 7
                elif pos > 7000 and pos < 7501 : score = 6
                elif pos > 7500 and pos < 8001 : score = 5
                elif pos > 8000 and pos < 8501 : score = 4
                elif pos > 8500 and pos < 9001 : score = 3
                elif pos > 9000 and pos < 9501 : score = 2
                elif pos > 9500 and pos < 10001 : score = 1
                else: score = 0
                relev = relev + score
                
                # size score
                score = 0
                if size <= 0 : score = 0
                elif size == 1 : score = 5
                elif size == 2 : score = 4
                elif size == 3 : score = 3
                elif size == 4 : score = 2
                elif size >= 5 : score = 1
                else: score = 0
                relev = relev + score
            
                # caps score
                score = 0
                if caps <= 0 : score = 0
                elif caps > 0 and caps < 11 : score = caps * 0.5
                elif caps > 10 : score = 5
                else: score = 0
                relev = relev + score
            
                # bold score
                score = 0
                if bold < 0 or bold > 1 : score = 0
                elif bold == 0 : score = 0
                elif bold == 1 : score = 5
                else: score = 0
                relev = relev + score
            
                # inurl score
                score = 0
                if inurl < 0 or inurl > 1 : score = 0
                elif inurl == 0 : score = 0
                elif inurl == 1 : score = 15
                else: score = 0
                relev = relev + score
                
                # inttl score
                score = 0
                if inttl < 0 or inttl > 1 : score = 0
                elif inttl == 0 : score = 0
                elif inttl == 1 : score = 15
                else: score = 0
                relev = relev + score
                
                # inanch score
                score = 0
                if inanch < 0 or inanch > 1 : score = 0
                elif inanch == 0 : score = 0
                elif inanch == 1 : score = 10
                else: score = 0
                relev = relev + score
                
                # update relevancy score to database
                print id, word, relev
                curs.execute('''REPLACE INTO Hits (id, DB1_Doc_id, word, hits, pos, size, caps, bold, inurl, inttl, inanch, relev )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''', (id, doc_id, word, hits, pos, size, caps, bold, inurl, inttl, inanch, relev) )
        conn.commit()


# FUNCTION: user-defined authority score updated to database
def authy(curs, curs1):
    inp = raw_input('\nUpdate authority scores? (Y/N) ')
    if inp.lower() == 'y' or len(inp) < 1 :
        curs.execute('''SELECT url, authy FROM Doc WHERE authy IS NULL OR authy IS '' ORDER BY id''')
        records = curs.fetchall()
        if records == [] :
            print 'No results found'
        else:
            print len(records), 'results found'
            
            print '\nRetrieving home domain for this Search Engine...'
            curs1.execute('''SELECT domain FROM Home WHERE id=1 ''')
            homedomain = curs1.fetchone()[0]
            print '\nHome domain:', homedomain
            homeauthy = raw_input('Set Authority Score (0:low - 9:high): ')
            curs.execute('''INSERT OR IGNORE INTO Auth (domain, auth)
                VALUES (?, ? )''', (homedomain, homeauthy ) )
            ### IMPROVEMENT: ADD DATA CHECKS & ERROR-HANDLING
            
            for (url, authy) in records :
                if re.search(homedomain, url) :
                    print '\n', url, '\nIn home domain. Updating authority:', homeauthy
                    curs.execute('''UPDATE Doc SET authy=? WHERE url=?''', (homeauthy, url ) )
                    
                else:
                    print '\n', url, '\nNot in home domain.'
                    if re.search('^http.//.+/$', url) :
                        thisdomain = str(re.findall('^http.//(.+)/', url)[0]).split('/')[0]
                        print '\nDomain:', thisdomain
                    elif re.search('^http.//.+', url) and not url.endswith('/') :
                        if re.search('^http.//.+/.+', url) :
                            thisdomain = str(re.findall('^http.//(.+)/', url)[0])
                        else:
                            thisdomain = str(re.findall('^http.//(.+)', url)[0])
                        print '\nDomain:', thisdomain
                    thisauthy = raw_input('Set Authority Score (0:low - 9:high): ')
                    curs.execute('''INSERT OR IGNORE INTO Auth (domain, auth)
                        VALUES (?, ? )''', (thisdomain, thisauthy ) )
                    curs.execute('''UPDATE Doc SET authy=? WHERE url=?''', (thisauthy, url ) )
        conn.commit()


################################################################

# MAIN

# create SQL database DB02 WordHits
conn = sqlite3.connect('DB02WordHits.db')
curs = conn.cursor()

# create SQL database DB01 RawData
conn1 = sqlite3.connect('DB01RawData.db')
curs1 = conn1.cursor()

# drop/create database
drop(curs)
create(curs)

# check and update relevancy scores & parent/child categories
relev(curs)
authy(curs, curs1)
catsplit(curs)

# retrieve data from DB01 into Indexer
curs1.execute('''SELECT id, Url_id, err, raw, read FROM Doc
    WHERE read = 0 AND err IS NULL ORDER BY id''')
result = curs1.fetchall()

# how many URLs to process?
print '\nExtracting new URLs to process...'
if result == None or len(result) == 0 :
    print 'No results found'
    quit()
else:
    print len(result), 'records found'
    inp = raw_input('\nEnter NUM to process, A for All, Q to Quit: ')
    if inp.lower() == 'q' : quit()
    if inp.lower() == 'a' : num = len(result)
    else:
        try:
            num = int(inp)
        except:
            print 'Bad input'
            quit()
print '\nProcessing:', num

# processing URLs
count = 0
excl1 = ['twitter', 'linkedin', 'github', 'facebook', 'div', 'site', 'inner', 'widget', '<', '>', 'class', 'deborah']
#excl2 = ['the', 'and', 'is', 'a', 'at', 'as', 'an', 'on', 'this', 'that', 'these', 'those', 'we', 'by', 'of', 'my', 'to', 'in', 'for']
for item in result :
    if count == num : break
    doc_id = item[0] ; url_id = item[1] ; err = item[2]
    raw = str(item[3]) ; read = item[4]
    print '\n\n\n', doc_id, url_id, err, read, '\n', raw[:100]
    
    # check raw data is good or update err to DB01RawData
    if raw.startswith('<!DOCTYPE html>') :
        print 'Raw data is HTML'
    else:
        print 'Error, raw data not HTML'
        curs1.execute('''UPDATE Doc SET err='err' WHERE id=?''', (doc_id, ) )
        conn1.commit()
        continue
    
    # update (id) url, timestamp and authority score to DB02WordHits Table:Doc
    curs1.execute('''SELECT Url.id, Doc.Url_id, Url.url FROM Url JOIN Doc
        ON Url.id = Doc.Url_id WHERE Doc.id=?''', (doc_id, ) )
    url = curs1.fetchone()[2]
    print '\nURL:', url
    #authy = raw_input('Set Authority Score (0:low - 9:high): ')
    #if authy < 1 : authy = 5
    authy = ''  # HARD-CODED DEFAULT VALUE - RUN FUNCTION AT TOP OF PROGRAM TO UPDATE ALL
    
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%dT%H:%M')
    print '\nUpdated:', timestamp
    curs.execute('''INSERT OR IGNORE INTO Doc (DB1_Doc_id, url, fetch, authy)
                VALUES (?, ?, ?, ? )''', (doc_id, url, timestamp, authy) )
    curs1.execute('''UPDATE Doc SET read=1 WHERE id=?''', (doc_id, ) )
    
    # check if URL is category or tag and update to DB002
    cat = cats(url)
    if cat != None :
        print 'Updating:', cat
        curs.execute('''INSERT OR IGNORE INTO Cats (DB1_Doc_id, cat)
                VALUES (?, ? )''', (doc_id, cat) )
        print 'Going to next url'
        continue
    tag = tags(url)
    if tag != None :
        print 'Updating:', tag
        curs.execute('''INSERT OR IGNORE INTO Tags (DB1_Doc_id, tag)
                VALUES (?, ? )''', (doc_id, tag) )
        print 'Going to next url'
        continue
    
    # extract title and month/year and update to DB002
    year, mnth, ttl = title(url)
    if year != None or mnth != None or ttl != None :
        print 'Updating:', year, mnth, ttl
        curs.execute('''UPDATE Doc SET year=? WHERE url=?''', (year, url ) )
        curs.execute('''UPDATE Doc SET mnth=? WHERE url=?''', (mnth, url ) )
        curs.execute('''UPDATE Doc SET ttl=? WHERE url=?''', (ttl, url ) )
    
    conn.commit()
    
    print '\nProcessing text...'
    
    # strip out body text only
    pos = raw.find('</header>')
    body = raw[pos+10:]
    pos1 = body.find('<footer ')
    body = body[:pos1]
    
    # parse content from raw HTML with beautiful soup
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.findAll(text=True)
    
    # list all word occurrences and their attributes
    
    # first, listing and updating all words + word hits
    textstr = ''
    for item in text :
        cleaned = unicodeToAscii(item)
        cleaned = cleaned.rstrip()
    
        # clean punctuation (minimal)
        cleaned = cleaned.replace('(', ' ').replace(')', ' ').replace('[', ' ').replace(']', ' ').replace('-', ' ').replace('*', ' ')
        cleaned = cleaned.replace('.', ' ').replace(',', ' ').replace(':', ' ').replace('"', ' ').replace('+', ' ').replace('=', ' ')
        ### IMPROVEMENT: ADD USER-CALLABLE FUNCTION TO CLEAN PUNCTUATION
        
        # update words data to database
        words = cleaned.split()
        if words == [] : continue
        
        for word in words :
            newword, incexc = check(word)
            
            # calculate and store unique words (cleaned, lowercase) + word hits for each URL
            
            # is word a single character or an excluded word?
            if len(word.lower()) == 1 :
                excluded = 'yes'
            elif word.lower() in excl1 :
                excluded = 'yes'
            #elif word.lower() in excl2 :
            #    excluded = 'yes'
            ### IMPROVEMENT: ADD USER-CALLABLE FUNCTION TO EXCLUDE INSIGNIFICANT WORDS
            elif incexc == 'exc' :
                excluded = 'yes'
            else:
                excluded = 'no'
            
            if excluded == 'yes' : continue

            # is word already in database for this url?
            curs.execute('''SELECT word FROM Hits WHERE DB1_Doc_id = ? AND word = ? ''', (doc_id, newword.lower()))
            select = curs.fetchone()

            # if no, add to database
            if select is None :
                curs.execute('''INSERT INTO Hits (DB1_Doc_id, word, hits )
                    VALUES (?, ?, 1 )''', (doc_id, newword.lower()) )
                curs.execute('''SELECT id FROM Hits WHERE word = ? ''', (newword.lower(), ))
                hits_id = curs.fetchone()[0]

            # if yes, update hits count
            else:
                curs.execute('''SELECT id FROM Hits WHERE DB1_Doc_id = ? AND word = ? ''', (doc_id, newword.lower()))
                hits_id = curs.fetchone()[0]
                curs.execute('''SELECT hits FROM Hits WHERE DB1_Doc_id = ? AND word = ? ''', (doc_id, newword.lower()))
                hits = curs.fetchone()[0]
                hits = hits + 1
                curs.execute('''REPLACE INTO Hits (id, DB1_Doc_id, word, hits )
                    VALUES (?, ?, ?, ? )''', (hits_id, doc_id, newword.lower(), hits) )

        textstr = textstr + ' ' + cleaned        
    
    conn.commit()
    
    # second, analysing and updating remaining word attributes 
    textstrL = textstr.lower()
    curs.execute('''SELECT word FROM Hits WHERE DB1_Doc_id = ? ''', (doc_id, ))
    words = curs.fetchall()
    for item in words :
        word = item[0]
        
        # (a) finding first position of word in text 
        pos = textstrL.find(' '+word+' ')
        curs.execute('''SELECT id FROM Hits WHERE DB1_Doc_id = ? AND word = ? ''', (doc_id, word))
        hits_id = curs.fetchone()[0]
        curs.execute('''SELECT hits FROM Hits WHERE id = ? ''', (hits_id, ))
        hits = curs.fetchone()[0]
        curs.execute('''REPLACE INTO Hits (id, DB1_Doc_id, word, hits, pos )
            VALUES (?, ?, ?, ?, ? )''', (hits_id, doc_id, word, hits, pos+1) )
        ### IMPROVEMENT: NEED TO DEBUG WHERE POS == 0

        # (b) updating size score
        h1 = re.search('<h1>.*'+word+'.*</h1>', raw)
        h2 = re.search('<h2>.*'+word+'.*</h2>', raw)
        h3 = re.search('<h3>.*'+word+'.*</h3>', raw)
        h4 = re.search('<h4>.*'+word+'.*</h4>', raw)
        h5 = re.search('<h5>.*'+word+'.*</h5>', raw)
        h6 = re.search('<h6>.*'+word+'.*</h6>', raw)
        if h1 == None :
            if h2 == None :
                if h3 == None :
                    if h4 == None :
                        if h5 == None :
                            if h6 == None : size = 0
                            else: size = 6
                        else: size = 5
                    else: size = 4
                else: size = 3
            else: size = 2
        else: size = 1
        curs.execute('''UPDATE Hits SET size=? WHERE id=?''', (size, hits_id ) )

        # (c) updating capitalisation count
        initial = word[:1]
        if not re.search('[0-9]', initial) :
            wordC = initial.upper()+word[1:]
            caps = textstr.count(wordC)
        else:
            caps = 0
        curs.execute('''UPDATE Hits SET caps=? WHERE id=?''', (caps, hits_id ) )
    
        # (d) updating bold score
        bold = re.search('<strong>.'+word[1:]+'.*</strong>', raw)
        if bold == None :
            curs.execute('''UPDATE Hits SET bold=0 WHERE id=?''', (hits_id, ) )
        else:
            curs.execute('''UPDATE Hits SET bold=1 WHERE id=?''', (hits_id, ) )

        # (e) updating whether in url or not
        inurl = url.count(word)
        if inurl > 0 :
            curs.execute('''UPDATE Hits SET inurl=1 WHERE id=?''', (hits_id, ) )
        else:
            curs.execute('''UPDATE Hits SET inurl=0 WHERE id=?''', (hits_id, ) )
    
        # (f) updating whether in title or not
        if ttl == None :
            curs.execute('''UPDATE Hits SET inttl=0 WHERE id=?''', (hits_id, ) )
        else:
            inttl = ttl.count(word)
            if inttl > 0 :
                curs.execute('''UPDATE Hits SET inttl=1 WHERE id=?''', (hits_id, ) )
            else:
                curs.execute('''UPDATE Hits SET inttl=0 WHERE id=?''', (hits_id, ) )

        # (g) updating whether in incoming anchor text or not (refer back to DB001)
        curs1.execute('''SELECT anchor FROM Link WHERE link=?''', (url, ) )
        anchortext = str(curs1.fetchone()[0]).lower()
        if anchortext == None :
            curs.execute('''UPDATE Hits SET inanch=0 WHERE id=?''', (hits_id, ) )
        else:
            try:
                anch = anchortext.count(word)
            except:
                anch = 0
            if anch > 0 :
                curs.execute('''UPDATE Hits SET inanch=1 WHERE id=?''', (hits_id, ) )
            elif anch == 0 :
                curs.execute('''UPDATE Hits SET inanch=0 WHERE id=?''', (hits_id, ) )

    # after processing URL, update count and save databases
    conn.commit()
    conn1.commit()
    count = count + 1
    print count, num


curs.close()
curs1.close()
quit()


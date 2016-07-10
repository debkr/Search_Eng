# Search Engine Application
Simple search engine application in Python with SQLite database


###Description
Here I build a suite of Python programs to replicate a simplified search engine process.

#####<em>Process flow chart:</em><br>
Diagrams mapping out the processes involved in application, and forming the basis for the suite of application programs, can be found on my blog here: http://deborahroberts.info/2016/06/simple-search-engine-in-python/

#####<em>Program walk-throughs:</em><br>

**1A. CRAWL (Crawler110.py)**
* import libraries
* create SQL database DB01 RawData
* user-defined URL (start)
* crawl first web page
* parse raw HTML data
* store in database (DB01) ordered by URL (docID)
* URL Resolver lists URLs with attributes and writes to DB01
* URL Server retrieves URLs
* (OPTIONAL) access criteria to cap and/or prioritise URLs
* feed URLs back into Crawler and repeat
* (INTERMITANTLY) check links for link pairings and update data back to DB01
* kill-switch built in to allow program shutdown as required

**2A. INDEX (Indexer110.py)**
* import libraries
* create SQL database DB02 WordHits
* retrieve data from DB01 into Indexer
* parse content from raw HTML data
* list all word occurrences and their attributes
* store in database (DB02) ordered by URL (docID) [ONE docID contains MANY wordIDs]
* for each docID, read data, process Relevancy Score and write back to DB02
* for each docID, read data, process Authority Score and write back to DB02

**2B. SORT**
* import libraries
* create SQL database DB03 Lexicon (if not already exists)
* create SQL database DB04 OrderedWords
* retrieve data from DB02 into Sorter
* for each docID, read data, check for new (relevant) words not already in DB03 Lexicon (add if new)
* reorder data by wordID not docID [ONE wordID is contained in MANY docIDs]
* store data (ordered by wordID) with URLs and word lists + attributes + relevancy and authority scores

**3A. SEARCH**
* import libraries
* user-defined search criteria entered through command line interface
* or (IDEALLY) web browser > saved as JSON file
* (OPTIONAL) allow for advanced search criteria in above
* read JSON file and build query as SQL command
* query SQL databases (DB03 Lexion JOIN DB02 OrderedWords JOIN DB01 WordHits)
* extract short text summary for inclusion with results
* (IDEALLY) review returned results for broken links before reporting
* order results based on relevancy and authority scores
* return ordered results onscreen or (IDEALLY) via JSON file format to web browser
* (OPTIONAL) add data visualisation dashboard element on web browser reporting
* (OPTIONAL) add mechanism for user feedback on quality/relevancy of returned results and write to database DB02 WordHits (plus feedback into adaptation of Authority algorithm employed by Indexer

#####<em>SQLite data models:</em><br>
 The following data model assumes four databases but in practice fewer would be needed if searching a well-bounded, hence smaller, part of the web. For simplicity, points specified as 'optional' in the above process walk-throughs have not been reflected in these data models.

**DB01: RawData**

Table: Doc  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 Url_id  INTEGER,  
 fetch   DATE,  
 err     INTEGER,  
 raw     TEXT,  
 read    INTEGER  

Table: Url  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 url     TEXT UNIQUE,  
 home    TEXT,  
 excl    TEXT,  
 crwl    INTEGER,  
 fetch   INTEGER,  
 path    INTEGER  

Table: Link  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 link    TEXT UNIQUE,  
 anchor  TEXT,  
 Doc_id  INTEGER  

Junction Table: Pair  
 Doc_id  INTEGER,  
 Link_id INTEGER,  
 PRIMARY KEY (Doc_id, Link_id)  

Table: Home  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 domain  TEXT UNIQUE  

Table: Excl  
 id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 domain TEXT  

Crawler: (1) The starting URL is added to Table: Url and fields Url.crwl and Url.fetch are set to 0 to indicate these actions have not yet occurred; (2) Url.path is set to 0 to indicate this is the Crawler's starting point (level zero) in the link pathway; (3) When the URL is crawled, Url.id is added to Doc.url_id and Url.crawl is updated to 1; (4) When data is fetched from the URL, it's stored in Doc.raw, a timestamp is added to Doc.fetch and Url.fetch is updated to 1; (5) (DEVELOPMENT TO BE ADDED) Check all raw HTML data parsed from URLs - where error, update err flag to Table: Doc.

URL Resolver: (1) Raw data from Doc.raw is parsed and all links resolved; (2) Each new link is added to Table: Link along with its anchor text; (3) Because there are MANY links and each link may appear on MANY web pages/docs, the JunctionTable: Pair is also updated to reflect the MANY-MANY relationship: Doc.id is updated to Pair.Doc_id and Link.id is updated to Pair.Link_id; (4) Each new link URL is checked to see if already in Table: Url. If not, each new URL is added to Table: Url and fields Url.crwl and Url.fetch are set to 0 to indicate these actions have not yet occurred; (5) Url.path is set to ('Url.path of referencing doc' + 1) to indicate that the Crawler has progressed one level deeper into the link pathway.

Link Server: (1) Reviews the list of URLs in Table: Url and, where crwl = 0, returns the next URL on the list, feeds it into the Crawler and updates Url.crwl to 1. The process then repeats as before, starting from Crawler step (2) above.

Link Pairing: Link pairings (i.e. cross-citations) can be handled by querying the Junction Table: Pair, therefore a separate attribute or database field has not been created. Link pairings were updated by the URL Resolver.

**DB02: WordHits**

Table: Doc  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
 DB1_Doc_id   INTEGER UNIQUE,  
 url     TEXT UNIQUE,  
 fetch   DATE,  
 authy   INTEGER,  
 year    INTEGER,  
 mnth    INTEGER,  
 ttl     TEXT  

Table: Hits  
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
 
 Table: Cats  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 DB1_Doc_id  INTEGER,  
 cat     TEXT UNIQUE,  
 parent  TEXT,  
 child   TEXT  

Table: Tags  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 DB1_Doc_id  INTEGER,  
 tag     TEXT UNIQUE  

Table: Auth  
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,  
 domain  TEXT UNIQUE,  
 auth    INTEGER  

Indexer: (1) Extract a new document from DB01: RawData (where DB01:Doc.read = 0 or null), update fields Doc.id, Doc.url and Doc.fetch from DB01 for that document, and update DB01:Doc.read to 1 to indicate that doc has now been read/processed by the Indexer; (2) If URL relates to categories or tags, extract and update categories/tags to database then proceed to next URL, else (for blog posts) extract year/month and title and update to database; (3) (Blog posts only) read and parse content in the doc, collating all words and their total hits; (4) Update DB01:Doc.id to Hits.DB1_Doc_id, add each of the found words and their total number of hits to Hits.word and Hits.hits respectively; (5) Count the hits of each word in various key positions in the doc (position, font size (as per header tags), capitalised, bold, within URL (or domain name if preferred), within doc title, within anchor text of referring URL) and update counts/scores to relevant fields in Table: Hits.

Relevancy Scoring: (1) For each word hit within the web page or document, calculate relevancy score based on weighted averages (with all hit attributes scored at pre-defined weightings, and with total hits (field Hits.hits) capped at a pre-defined level); (2) Update relevancy score to Hits.relev for each of the words in the document.

Authority Scoring: (1) Set authority scoring of the web page or document based on user-entry for that domain; (2) Update authority score to Doc.authy and update domain and authority score to Auth.domain and Auth.auth respectively. (3) Alternatively, user may enter authority score manually for each URL (currently hard-coded into program but commented out). (Program may be updated at a later date to calculate authority score based on a pre-defined scoring system.)

**DB03: Lexicon**

Table: Lex
 id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
 word    TEXT UNIQUE

The Lexicon is maintained as a full list of unique words relevant to the area of web, or knowledge domain, being indexed for searching. New words found by the Indexer are added to the Lexicon by the Sorter. The unique word ID (Lex.id) will be mirrored across from DB03 to DB04:OrderedWords (see below).

**DB04: OrderedWords**

Table: Word
 id      INTEGER NOT NULL PRIMARY KEY UNIQUE,
 word    TEXT UNIQUE

Table: Doc
 id      INTEGER NOT NULL PRIMARY KEY UNIQUE,
 url     TEXT UNIQUE,
 fetch   DATE

Junction Table: Score
 Doc_id  INTEGER,
 Word_id  INTEGER,
 relev   INTEGER,
 authy   INTEGER,
 PRIMARY KEY (Doc_id, Word_id)

Sorting: (1) For each document in DB02:WordHits, all fields in Table: Doc are updated (straight copy). Note that Doc.id is a unique integer field but is not auto-incrementing - instead the same doc ID as used in DB02:WordHits is updated here; (2) For each word in DB02:Hits, the word is checked to see if already contained in DB03:Lexicon. If not, the new word is added to DB03:Lexicon and the value of DB03:Lex.id is returned and updated to Word.id. Note this is a unique integer field but is not auto-incrementing - instead the same word ID as used in Lexicon (DB03:Lex.id) is updated here; (3) For each instance of a word appearing in a document, Doc.id and Word.id are added to the Junction Table: Score, to fields Score.Doc_id and Score.Word_id respectively, together with the relevancy and authority scores from DB02:WordHits for that word and doc; (4) The Junction Table: Score is kept sorted based on document authority scoring AND word relevancy scoring. This sorted database will form the basic database for search queries (although search functions can also be modified as required by the user, resulting in modified select commands to this database).

###Ways to Improve:
* There are many ways to develop or enhance a simple and well-bounded search engine so I won't list them all here. Key things I think should be included initially (for the kind of application I have in mind to build) would be:
* Include advanced searching functionality. This should be relatively simple, based on Boolean operators within an SQL database SELECT query. This could be extended to include dynamic user-specified ranking on screen (e.g. order by relevancy or by authority or by relevancy+authority);
* Return some kind of summary of the resulting page or document along with the link. This could be quite simple (returning a simple text summary, restricted to the first 100 characters, say) or could be far more complex (synthesising and summarising the most important points within the page or document - obviously this is far more advanced, and well beyond the scope of the initial search engine application);
* Review options for including more advanced forms of data visualisation of returned search results - effectively creating a data visualisation dashboard to help display the top n search results in a more relevant, engaging and easily-accessible format;
* Build in the Tagging Engine functionality so the application can double up as a word tagger for blog posts, etc. In practice this would probably mean adding a refined version of the Tagging Engine as a stand-alone web-based application executable through the same web portal as the main search engine application.

###Future Developments:
Data Visualisations: An obvious improvement on the current search engine application is to add user-configurable visualisation options to the web browser displaying the user's search results, in the manner of a dashboard rather than just an ordered list of links with text snippets. One possibility is to make use of, D3.js - a powerful yet easy-to-use and free visualisation tool in JavaScript - pulling in data dumped from Python to a JSON file. At this point I haven't worked with D3.js and the visualisation aspect of my search engine application is out of scope for the time being, but will be revisited later when time (and skill level) allows. But here's a simple description of the process: the D3.js website gives a number of visualisation tools one can use; download the relevant JavaScript program to create that data visualisation; ensure your JSON data file matches the same required data input format; within your HTML for your web page, load in the D3.js library in HTML, load in the JSON data file then run the relevant JavaScript program to activate your visualisation in-browser. Note there appear to be compatibility issues with some versions of Internet Explorer, although running in FireFox gave me no problems; this will need to be ironed out in future.

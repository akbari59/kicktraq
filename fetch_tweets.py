from Queue import Queue
from threading import Thread
from lxml import html
import datetime
import ujson, time
import urllib2

num_fetch_threads = 4
topsy_per_page = 100
queue = Queue(4)

def get_kickstarter_short_url(project):
  raw_html = urlopen(project['project_url']).read()
  page = html.fromstring(raw_html)
  return page.xpath("//link[@rel='shorturl']/@href")

def process_tweet(tweet_url):
  raw_html = opener.open(tweet_url).read()
  page = html.fromstring(raw_html)
  if page.xpath("//div[contains(@class, 'permalink-tweet')]"):
    tweet = {}
    tweet_div = page.xpath("//div[contains(@class, 'permalink-tweet')]")[0]
    tweet['screen_name'] = tweet_div.xpath(".//@data-screen-name")[0]
    tweet['content'] = tweet_div.xpath(".//p[@class='js-tweet-text tweet-text']")[0].text_content()
    tweet['url'] = tweet_url
    tweet['timestamp'] = int(tweet_div.xpath(".//span[contains(@class, 'js-short-timestamp')]/@data-time")[0])
    if tweet_div.xpath(".//li[contains(@class,'js-stat-retweets')]"):
      tweet['retweets'] = int(tweet_div.xpath(".//li[contains(@class,'js-stat-retweets')]/a/strong/text()")[0])
    else:
      tweet['retweets'] = 0
    # print tweet
    #print "{0}\t{1}\t{2}\t{3}\t{4}".format(tweet['url'], tweet['timestamp'], tweet['screen_name'], tweet['retweets'], tweet['content'].encode('utf-8'))

def fetch_tweets(query, cursor=None):
  base_url = "https://twitter.com/search?f=realtime&q={0}&src=typd".format(query)
  if cursor:
    base_url += "&scroll_cursor={0}".format(cursor)
  opener = urllib2.build_opener()
  opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36')]
  raw_html = opener.open(base_url).read()
  page = html.fromstring(raw_html)
  tweets = page.xpath("//div[contains(@class, 'stream')]/div/ol[contains(@class, 'stream-items')]/li")
  _cursor = page.xpath("//div[contains(@class, 'stream-container')]/@data-scroll-cursor")

  for tweet_div in tweets:
    if tweet_div.xpath(".//a[contains(@class, 'js-permalink')]/@href"):
      tweet_permalink = "https://twitter.com{0}".format(tweet_div.xpath(".//a[contains(@class, 'js-permalink')]/@href")[0])
      print "{0},{1}".format(query, tweet_permalink)

  if _cursor and len(tweets) > 0:
    fetch_tweets(query, _cursor[0])

def fetch_tweets2(project):
  project_name = quote(project['project_name']+" site:kickstarter.com")
  start_period = str(project['project_funding_days'][0])
  end_period = str(project['project_funding_days'][1])
  topsy_start_url = "http://otter.topsy.com/search.js?q={0}&mintime={1}&maxtime={2}&offset=0&perpage=20&apikey=09C43A9B270A470B8EB8F2946A9369F3".format(project_name, start_period, end_period)
  mintime, maxtime = project['project_funding_days'][0], project['project_funding_days'][1]
  while mintime < maxtime:
    finaltime = mintime+86400*2
    mintime += 86400
    mindate = datetime.datetime.fromtimestamp(mintime)
    finaldate = datetime.datetime.fromtimestamp(finaltime)
    new_date = time.strptime(mindate.strftime('%d/%m/%y'), '%d/%m/%y')
    new_timestamp = int(time.mktime(new_date))
    final_date = time.strptime(finaldate.strftime('%d/%m/%y'), '%d/%m/%y')
    final_timestamp = int(time.mktime(final_date))
    # print datetime.datetime.fromtimestamp(new_timestamp).strftime('%d/%m/%Y'), " - ",  datetime.datetime.fromtimestamp(final_timestamp).strftime('%d/%m/%y')
    follow_pagination, page = True, 80
    topsy_start_url = "http://otter.topsy.com/search.js?q={0}&mintime={1}&maxtime={2}perpage=10&apikey=09C43A9B270A470B8EB8F2946A9369F3".format(project_name, new_timestamp, final_timestamp)
    while follow_pagination:
      try:
        final_url = "{0}&page={1}".format(topsy_start_url, str(page))
        raw_json = urlopen(final_url).read()
        output = ujson.loads(raw_json)
        total_tweets = output['response']['total']
        page_tweets = output['response']['list']
        # print page_tweets
        if( len(page_tweets) == 0 ):
          follow_pagination = False
        # print 'Page tweets: ', len(page_tweets)
        for tweet_element in page_tweets:
          if 'http://twitter.com/' in tweet_element['url']:
            tweet_content = tweet_element['content'].encode('utf-8').replace("\t", " ").replace("\n", " ")
            screen_name = tweet_element['trackback_author_nick'].encode('utf-8')
            ln = "{0}\t{1}\t{2}\t{3}\t{4}".format(project['project_id'], int(tweet_element['firstpost_date']), tweet_element['url'], screen_name, tweet_content)
            print ln
      except Exception, e:
        with open("error.log", "a") as f:
          f.write("{0}, error: {1}\n".format(project['project_url'], e))
        # print "Page: ", page
      page += 1
  return []


def fetch(i, q):
  while True:
    ln = q.get()

    try:
      fetch_tweets(ln)
    except Exception, e:
      with open("error.log", "a") as f:
        f.write("{0}, error: {1}\n".format(ln, e))

    q.task_done()

for i in range(num_fetch_threads):
  worker = Thread(target=fetch, args=(i, queue,))
  worker.setDaemon(True)
  worker.start()

f = open('kickstarter_urls_sample'); lines = f.readlines(); f.close()

for line in lines:
  queue.put(line.rstrip())

queue.join()

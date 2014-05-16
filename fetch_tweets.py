from Queue import Queue
from threading import Thread
from lxml import html
import urllib2, socket

num_fetch_threads = 4
topsy_per_page = 100
queue = Queue(4)
r = redis.StrictRedis(host='107.170.253.33')

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

def fetch(i, q):
  while True:
    try:
      ln = q.get()
      fetch_tweets(ln)
    except Exception, e:
      with open("error.log", "a") as f:
        f.write("{0}, error: {1}\n".format(ln, e))

    q.task_done()

for i in range(num_fetch_threads):
  worker = Thread(target=fetch, args=(i, queue,))
  worker.setDaemon(True)
  worker.start()

hostname = socket.gethostname()
f = open(hostname); lines = f.readlines(); f.close()

for line in lines:
  queue.put(line.rstrip())

queue.join()

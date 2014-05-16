from Queue import Queue
from threading import Thread
from lxml import html
import urllib2, socket

num_fetch_threads = 4
topsy_per_page = 100
queue = Queue(4)

def fetch_tweet(ln):
  splits = ln.split(',')
  project_url = splits[0]
  tweet_url = splits[1]
  opener = urllib2.build_opener()
  opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36')]
  raw_html = opener.open(tweet_url).read()
  page = html.fromstring(raw_html)
  if page.xpath("//span[contains(@class, 'js-action-profile-name')]/b/text()"):
    screen_name = page.xpath("//span[contains(@class, 'js-action-profile-name')]/b/text()")[0]
    tweet_texts = page.xpath("//p[contains(@class, 'js-tweet-text')]")[0].xpath(".//text()")
    tweet_text = ''.join(tweet_texts).encode('utf-8').replace("\n", " ").replace("\t", " ")
    ts = 0
    if page.xpath("//small[contains(@class, 'time')]")[0].xpath(".//a")[0].xpath(".//@data-time"):
      ts = page.xpath("//small[contains(@class, 'time')]")[0].xpath(".//a")[0].xpath(".//@data-time")[0]
    retweets = 0
    favs = 0
    if page.xpath("//li[contains(@class, 'js-stat-retweets')]"):
      if page.xpath("//li[contains(@class, 'js-stat-retweets')]/a/strong/text()"):
        retweets = int(page.xpath("//li[contains(@class, 'js-stat-retweets')]/a/strong/text()")[0])

    if page.xpath("//li[contains(@class, 'js-stat-favorites')]"):
      if page.xpath("//li[contains(@class, 'js-stat-favorites')]/a/strong/text()"):
        favs = int(page.xpath("//li[contains(@class, 'js-stat-favorites')]/a/strong/text()")[0])

    output_ln = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(project_url, tweet_url, ts, screen_name, tweet_text, retweets, favs)
    print output_ln

def fetch(i, q):
  while True:
    try:
      ln = q.get()
      fetch_tweet(ln)
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

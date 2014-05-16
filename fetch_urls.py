from threading import Thread
from urllib2 import urlopen, quote
import urllib2
from lxml import html

tweet_ids = set([])

def get_kickstarter_short_url(project):
  raw_html = urlopen(project['project_url']).read()
  page = html.fromstring(raw_html)
  return page.xpath("//link[@rel='shorturl']/@href")

def process_tweet(tweet_url):
  opener = urllib2.build_opener()
  opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36')]
  raw_html = opener.open(tweet_url).read()
  page = html.fromstring(raw_html)
  if page.xpath("//div[contains(@class, 'permalink-tweet')]"):
    tweet = {}
    tweet_div = page.xpath("//div[contains(@class, 'permalink-tweet')]")[0]
    tweet['screen_name'] = tweet_div.xpath(".//@data-screen-name")[0]

    tweet['content'] = tweet_div.xpath(".//p[@class='js-tweet-text tweet-text']")[0].text_content()
    tweet['content'] = tweet['content'].replace(u'\xa0', u' ').encode('utf-8')
    tweet['content'] = tweet['content'].replace("\n", " ").replace("\r", "").replace("\t", " ")
    tweet['content'] = unicode(tweet['content'], 'ascii', 'ignore')

    tweet['url'] = page.xpath("//link[@rel='canonical']/@href")[0]

    tweet_id = get_tweet_id(tweet['url'])
    if tweet_id not in tweet_ids:
      tweet_ids.add(tweet_id)
      tweet['timestamp'] = int(tweet_div.xpath(".//span[contains(@class, 'js-short-timestamp')]/@data-time")[0])
      if tweet_div.xpath(".//li[contains(@class,'js-stat-retweets')]"):
        tweet['retweets'] = int(tweet_div.xpath(".//li[contains(@class,'js-stat-retweets')]/a/strong/text()")[0])
      else:
        tweet['retweets'] = 0

      if tweet_div.xpath(".//li[contains(@class,'js-stat-favorites')]"):
        tweet['favs'] = int(tweet_div.xpath(".//li[contains(@class,'js-stat-favorites')]/a/strong/text()")[0])
      else:
        tweet['favs'] = 0

      followers_count = None

      profile_links = page.xpath("//a[contains(@class, 'js-user-profile')]/@href")
      if profile_links:
        profile_link = "https://twitter.com{0}".format(profile_links[0])
        profile_raw_html = opener.open(profile_link).read()
        profile_page = html.fromstring(profile_raw_html)
        followers_anchor = profile_page.xpath("//a[@data-nav='followers']/@title")
        if followers_anchor:
          followers_title = followers_anchor[0].replace(u'\xa0', u'').replace(u'Seguidores', u'').replace(u'Followers', u'').replace(",", "")
          followers_count = int(followers_title)
          tweet['followers_count'] = followers_count

        if not followers_count:
          followers_count = profile_page.xpath("//strong[contains(@class, 'js-mini-profile-stat')]/text()")[2].replace(",", "")
          if 'K' in followers_count:
            followers_count = profile_page.xpath("//strong[contains(@class, 'js-mini-profile-stat')]/@title")[2].replace(",", "")
            tweet['followers_count'] = int(followers_count)
          else:
            tweet['followers_count'] = int(followers_count)
      #print tweet
      print "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(tweet['screen_name'], tweet['url'], str(tweet['timestamp']), tweet['content'], tweet['followers_count'], str(tweet['retweets']), str(tweet['favs']) )

f = open('urls_unique.tsv'); lines = f.readlines(); f.close()

for line in lines:
  line = line.rstrip()
  try:
    fetch_url(line)
  except Exception, e:
    with open("error.log", "a") as f:
      f.write("{0}, error: {1}\n".format(line, e))

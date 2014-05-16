from Queue import Queue
from threading import Thread
from lxml import html
import urllib2

num_fetch_threads = 6
queue = Queue()

def fetch(i, q):
  while True:
    data = q.get()

    try:
      opener = urllib2.build_opener()
      opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36')]
      raw_html = opener.open(data).read()
      page = html.fromstring(raw_html)
      project_anchor = page.xpath("//a[@id='button-backthis']/@href")
      if project_anchor:
        project_link = project_anchor[0].replace('https://www.', '').replace('http://www.', '').replace('?ref=kicktraq', '')
        print "{0}".format(project_link)
    except Exception, e:
      with open("error.log", "a") as f:
        f.write("{0}, error: {1}\n".format(data, e))

    q.task_done()

for i in range(num_fetch_threads):
  worker = Thread(target=fetch, args=(i, queue,))
  worker.setDaemon(True)
  worker.start()

f = open('urls_unique.tsv'); lines = f.readlines(); f.close()

for line in lines:
  queue.put(line.rstrip())

queue.join()

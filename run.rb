require 'net/ssh/multi'

$hosts = 'kickstarter3', 'kickstarter4', 'kickstarter5'

Net::SSH::Multi.start do |session|
  $hosts.each do |h|
    session.use "root@#{h}"
  end
  session.exec "apt-get install python-lxml -y"
end

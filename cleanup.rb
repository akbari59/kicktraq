File.read(ARGV[0]).split("\n").each do |ln|
  if ln.size > 30
    puts ln
  end
end

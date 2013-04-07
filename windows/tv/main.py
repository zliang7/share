#! N:\Python27\python.exe
# -*- coding: utf-8 -*- 

import urllib2
import re
import os
import commands
from sgmllib import SGMLParser
from httplib import BadStatusLine
import time
import datetime
import sys

# define each line of history
NAME = 0
FORMAT = 1
ID = 2
HISTORY = 3

PAUSE_STR = 'PAUSE'
END_STR = 'END'

URL_PREFIX = 'http://www.yyets.com/php/resource/'

# Enable debug mode
debug = 0


def get_time():
	return time.strftime('%Y-%m-%d %X', time.localtime(time.time()))
        
def update_line(lines, records, record_index):
    records_number = len(records)
    line_index = records[record_index]
    line = lines[line_index]
    fields = line.split(',')
    
    print str(record_index + 1) + "/" + str(records_number) + "    Processing " + fields[NAME] + " ..."
    
    # get the html
    if debug:
        file = open(fields[ID] + '.htm')
        html = file.read()
    else:
        url = URL_PREFIX + fields[ID]
        try:
            u = urllib2.urlopen(url)
        except BadStatusLine:
            print "Check failed"
            lines.append("== " + fields[NAME] + ",Check failed," + get_time() + " ==\n")
            return
        html = u.read()
    
    # Check if it has update
    xl_pattern = re.compile("thunderrestitle.*?迅")
    urls = xl_pattern.findall(html)
    
    format_pattern = re.compile(fields[FORMAT])
    episodePattern = re.compile("(" + fields[HISTORY][0:4] + "\d\d)")
    thunderPattern = re.compile("(thunder\:.*)\"")
    new = []
    for url in urls:
        # find all with relative format
        if format_pattern.search(url):
            # find all suitable episode
            episodeMatch = episodePattern.search(url)
            if not episodeMatch:
                continue
            currentEpisode = int(episodeMatch.group(0)[4:6])
            historyEpisode = int(fields[HISTORY][4:6])
            if currentEpisode <= historyEpisode:
                continue
                
            # get the link    
            thunderMatch = thunderPattern.search(url)
            if not thunderMatch:
                continue
            r = []
            r.append(episodeMatch.group(0))
            r.append(thunderMatch.group(1))
            new.append(r)

    # Handle update
    if len(new) > 0:
        print '^_^ There is an update'
        
        lines[line_index] = line.replace(fields[HISTORY], new[len(new)-1][0]) + '\n'
        
        lines.append("== " + fields[NAME] + "," + new[0][0] + "-" + new[len(new)-1][0] + "," + get_time() + " ==\n")
        for new_index in range(0, len(new)):
            lines.append(new[new_index][1] + "\n")
        lines.append("\n")
        
        return True
    else:
        return False
                
def update_history():
    # each item is the index of line to be checked
    records = []
    
    has_update = False

    # Get lines
    if debug:
        lines = ["Spar,人人影视.mp4,11176,S03E00"]
    else:
        file = open('history.txt')
        lines = file.readlines()
        file.close()

    # Update records
    for line_index in range(0, len(lines)):
        # Skip blank line
        if not lines[line_index].strip():
            continue

        # Check if pause meets
        m = re.match(PAUSE_STR + ' (\d+-\d+-\d+ \d+:\d+:\d+)', lines[line_index])
        if m:
            diff = datetime.datetime.today() - datetime.datetime.strptime(m.group(1), '%Y-%m-%d %X')
            lines[line_index] = PAUSE_STR + ' ' + get_time() + '\n'
            if diff.days < 30:
                break
            else:
                continue

        # Check if end meets    
        if re.search(END_STR, lines[line_index]):
            break
            
        # Append to records
        records.append(line_index)

    # Update line
    for record_index in range(0, len(records)):
        if update_line(lines, records, record_index):
            has_update = True
        
    # Handle no update
    if not has_update:
        print "There is no update at all!"
        lines.append("== All,No update," + get_time() + " ==\n")

    # Update history file
    if debug:
        print lines
    else:
        os.chdir(sys.path[0])
        if os.path.exists("history_old.txt"):    
            os.remove("history_old.txt")
            
        os.rename("history.txt", "history_old.txt")   

        f = open("history.txt", "w")
        for line in lines:
            f.write(line)
        f.close()        

def sleep(seconds):
    print 'Wait ' + str(seconds) + ' seconds and quit...'
    time.sleep(seconds)

if __name__ == "__main__":
    update_history()
    sleep(5)

    
    
  
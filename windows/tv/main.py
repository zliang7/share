#! N:\Python27\python.exe
# -*- coding: utf-8 -*- 

import urllib2;
import re;
import os;
import commands;
from sgmllib import SGMLParser;
from httplib import BadStatusLine;
import time;

# define each line of history
NAME = 0;
FORMAT = 1;
ID = 2;
HISTORY = 3;

urlPrefix = "http://www.yyets.com/php/resource/";
history = [];
lines = "";
debug = 0;
hasUpdate = False;

def updateHistory():
    global debug;
    global hasUpdate;
    
    if debug:
        print lines;
    else:
        os.chdir(os.getcwd());
        if os.path.exists("history_old.txt"):    
            os.remove("history_old.txt");
            
        os.rename("history.txt", "history_old.txt");    

        f = open("history.txt", "w");
        for line in lines:
            f.write(line);

        if not hasUpdate:
            f.write("== All,No update," + time.strftime('%Y-%m-%d %X', time.localtime(time.time())) + " ==\n");

        f.close();    
            
def getNew():
    global debug;
    global hasUpdate;
    
    historyLen = len(history);
    
    for historyIndex in range(0, historyLen):
        print str(historyIndex + 1) + "/" + str(historyLen) + "    Processing " + history[historyIndex][NAME] + " ...";
    
        # get the html
        if debug:
            file = open(history[historyIndex][ID] + '.htm');
            html = file.read();
        else:
            url = urlPrefix + history[historyIndex][ID];
            try:
                u = urllib2.urlopen(url);
            except BadStatusLine:
                print "Check failed";
                lines.append("== " + history[historyIndex][NAME] + ",Check failed," + time.strftime('%Y-%m-%d %X', time.localtime(time.time())) + " ==\n");
                continue;
            html = u.read();
        
        # find all links to xunlei
        xlPattern = re.compile("thunderrestitle.*?迅");
        urls = xlPattern.findall(html);
        
        formatPattern = re.compile(history[historyIndex][FORMAT]);
        # history[historyIndex][0];
        episodePattern = re.compile("(" + history[historyIndex][HISTORY][0:4] + "\d\d)");
        thunderPattern = re.compile("(thunder\:.*)\"");
        new = [];
        for url in urls:
            # find all with relative format
            if formatPattern.search(url):
                # find all suitable episode
                episodeMatch = episodePattern.search(url);
                if not episodeMatch:
                    continue;
                currentEpisode = int(episodeMatch.group(0)[4:6]);
                historyEpisode = int(history[historyIndex][HISTORY][4:6]);
                if currentEpisode <= historyEpisode:
                    continue;
                    
                # get the link    
                thunderMatch = thunderPattern.search(url);
                if not thunderMatch:
                    continue;
                record = [];
                record.append(episodeMatch.group(0));
                record.append(thunderMatch.group(1));
                new.append(record);

        if len(new) == 0:
            continue;
        else:
            print "^_^ There is an update for " + history[historyIndex][NAME];
            hasUpdate = True;
   
        endPattern = re.compile('END');
        for lineIndex in range(0, len(lines)):
            line = lines[lineIndex];
            if not line.strip():
                continue;
            if endPattern.search(line):
                break;
            if line.find(history[historyIndex][NAME]) <> -1:
                lines[lineIndex] = line.replace(history[historyIndex][HISTORY], new[len(new)-1][0]);
                lines[lineIndex] = lines[lineIndex] + "\n";

        lines.append("== " + history[historyIndex][NAME] + "," + new[0][0] + "-" + new[len(new)-1][0] + "," + time.strftime('%Y-%m-%d %X', time.localtime(time.time())) + " ==\n");
        for newIndex in range(0, len(new)):
            lines.append(new[newIndex][1] + "\n");
        lines.append("\n");    
                
    if not hasUpdate:
        print "There is no update at all!";
                
def getHistory():
    global history;
    global lines;
    global debug;

    if debug:
        lines = ["Spar,人人影视.mp4,11176,S03E00"];
    else:
        file = open('history.txt');
        lines = file.readlines();
        file.close();
   
    endPattern = re.compile('END');
    for line in lines:
        if not line.strip():
            continue;
        if endPattern.search(line):
            break;
        fields = line.split(',');
        record = [];
        for field in fields:
            record.append(field);
        history.append(record);
    
if __name__ == "__main__":
    getHistory();
    getNew();
    updateHistory();
    
    print "Wait 5 seconds and quit...";
    time.sleep(5);
    
    
  
#! N:\Python27\python.exe
# -*- coding: utf-8 -*- 

import urllib2;
import re;
import os;
import commands;
from sgmllib import SGMLParser;
import time;

# define each line of history
NAME = 0;
ID = 1;
HISTORY = 2;

urlPrefix = "http://www.yyets.com/php/resource/";
history = [];
lines = "";
debug = 0;

def updateHistory():
    global debug;
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
        f.close();    
            
def getNew():
    global debug;
    for historyIndex in range(0, len(history)):
        # get the html
        if debug:
            file = open('11088.htm');
            html = file.read();
        else:
            url = urlPrefix + history[historyIndex][ID];
            u = urllib2.urlopen(url);
            html = u.read();
        
        # find all links to xunlei
        xlPattern = re.compile("thunderrestitle.*?迅");
        urls = xlPattern.findall(html);
        
        formatPattern = re.compile("rmvb");
        history[historyIndex][0];
        episodePattern = re.compile("(" + history[historyIndex][HISTORY][0:4] + "\d\d)");
        thunderPattern = re.compile("(thunder\:.*)\"");
        new = [];
        for url in urls:
            # find all rmvb format
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
            print ":( There is no update for " + history[historyIndex][NAME];
            continue;
        else:
            print ":) There is an update for " + history[historyIndex][NAME];
   
        todoPattern = re.compile('TODO');
        for lineIndex in range(0, len(lines)):
            line = lines[lineIndex];
            if not line.strip():
                continue;
            if todoPattern.search(line):
                break;
            if line.find(history[historyIndex][NAME]) <> -1:
                lines[lineIndex] = line.replace(history[historyIndex][HISTORY], new[len(new)-1][0]);

        lines.append("== " + history[historyIndex][NAME] + "," + new[0][0] + "-" + new[len(new)-1][0] + "," + time.strftime('%Y-%m-%d %X', time.localtime(time.time())) + " ==\n");
        for newIndex in range(0, len(new)):
            lines.append(new[newIndex][1]);
        lines.append("\n");    
                

def getHistory():
    global history;
    global lines;
    global debug;

    if debug:
        lines = ["homeland,11088,S02E03"];
    else:
        file = open('history.txt');
        lines = file.readlines();
        file.close();
   
    todoPattern = re.compile('TODO');
    for line in lines:
        if not line.strip():
            continue;
        if todoPattern.search(line):
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
    time.sleep(3);
    
    
  
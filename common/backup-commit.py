#!/usr/bin/env python

# Backup the modified files of a commit

import warnings
from optparse import OptionParser
import commands
import os

def main():
    parser = OptionParser()
    parser.add_option("-c", "--commit-hash", dest="commitHash", help="hash of commit");
    parser.add_option("-s", "--src-dir", dest="srcDir", help="src directory of project");
    parser.add_option("-d", "--dest-dir", dest="destDir", help="dest directory to backup");
    (options, args) = parser.parse_args();
    
    if options.srcDir is None:
        print("You need to designate src directory of project")
        exit -1
        
    if options.srcDir is None:
        print("You need to designate dest directory to backup")
        exit -1
        
    os.chdir(options.srcDir)
    if options.commitHash is None:
        commitHash = commands.getoutput("git log -1 --pretty=\"format:%H\"")
        
    files = str.split(str.strip(commands.getoutput("git show --pretty=\"format:\" --name-only")), "\n")
    
    for file in files:
        command = " cp --parent " + file + " " + "/workspace/gytemp"
        commands.getstatusoutput(command)
    
if __name__ == '__main__':
    main()

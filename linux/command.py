# -*- coding: utf-8 -*- 

# Usage:
# t .*
#

import re
import os
from subprocess import Popen, PIPE, STDOUT

GREEN = '\033[0;32m'
RED = '\033[0;31m'
WHITE = '\033[1;37m'


# Below are related to commands
INDEX_TAG = 0
INDEX_COMMAND = 1
INDEX_DESCRIPTION = 2
INDEX_TYPE = 3


TYPE_NULL = 0 # command is not runnable
POS = 0
TYPE_RUNNABLE = 2 << POS
POS = POS + 1
TYPE_BUILTIN = 2 << POS # command is shell built-in
POS = POS + 1

commands = [
    ('basic', r'find /tmp -type f -printf "%f\n"', 'Only print the file name', TYPE_RUNNABLE),
    ('basic', r'grep -r "str" ./', 'Search string in directory recursively', TYPE_RUNNABLE),
    ('basic', 'find ./ -type f | wc -l', 'Calculate number of files, including sub directory', TYPE_RUNNABLE),
    ('basic', 'sudo !!', 'Execute last command with sudo', TYPE_NULL),
    ('basic', r'^foo^bar', 'Replace str "foo" in last command with "bar"', TYPE_NULL),
    ('basic', r'!!:s/foo/bar', r'Replace str "foo" in last command with "bar"', TYPE_NULL),
    ('basic', 'cp filename{,.bk}', 'Backup file', TYPE_NULL),
    ('basic', r'history -r; history | awk \'{a[$2]++}END{for(i in a){print a[i] " " i}}\' | sort -rn | head', 'List 10 most used commands', TYPE_NULL),
    ('basic', r'history -r; history |grep cd', 'Test shell built-in command', TYPE_BUILTIN),
    ('upgrade', 'do-release-upgrade', 'Upgrade system', TYPE_NULL),
    ('info', 'cat /etc/os-release', 'List distribution info', TYPE_RUNNABLE),
    ('vi', ':w !sudo tee %', 'Write a readonly file in vi', TYPE_NULL),
    ('git', r'git log --summary 223286b.. | grep "Author:" | wc -l', 'count git commits since specific commit', TYPE_RUNNABLE),
    ('', '', ''),
]

commands_cache = []

options = [
    ('t tag', 'Search command by tag'),
    ('d description', 'Search command by description'),
    ('r number', 'Run command with number'),
    ('c command', 'Run command directly'),
    ('q', 'Quit'),
]

def run_command(command, command_type):
    if not command_type & TYPE_RUNNABLE:
        print 'This is not a runnable command!'
        return

    # Need special handle for shell builtin command
    if command_type & TYPE_BUILTIN:
        command = 'bash -i -c "' + command + '"'
        print command
        event = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        print event.communicate()
    else:
        print command
        os.system(command)

def search(string, index_field):
    global commands_cache
    commands_cache = []

    for index_commands in range(0, len(commands)):
        if re.search(string, commands[index_commands][index_field], re.IGNORECASE):
            commands_cache.append(index_commands)

    for command_cache in commands_cache:
        command = commands[command_cache]
        print '[' + str(command_cache) + ']->' + ','.join(command)

if __name__ == '__main__':
    prompt = GREEN + 'Please choose an option:\n'
    for o in options:
        prompt = prompt + o[0] + ': ' + o[1] + '\n'
    prompt = prompt + '\n' + RED

    while True:
        string = raw_input(prompt)
        if string == 'q':
            quit()

        print WHITE
        m = re.match('(t|d|r|c) (.+)', string)
        if not m:
            print 'Wrong input!'
            continue

        option_type = m.group(1)
        option_content = m.group(2).strip()
        if option_type == 't':
            search(option_content, INDEX_TAG)
        elif option_type == 'd':
            search(option_content, INDEX_DESCRIPTION)
        elif option_type == 'r':
            command_record = commands[int(option_content)]
            run_command(command_record[INDEX_COMMAND], command_record[INDEX_TYPE])
        elif option_type == 'c':
            run_command(option_content, TYPE_RUNNABLE)
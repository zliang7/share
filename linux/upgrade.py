#/usr/bin/python

import os
from optparse import OptionParser
    
if __name__ == "__main__":
    # Handle options
    parser = OptionParser(description='Description: Script to upgrade system',
                          epilog="""
Examples:
  python chromium_build.py -t socks
""")
    parser.add_option("-p", "--proxy", dest="proxy", help="What kind of proxy to use", default='http')
    (options, args) = parser.parse_args()
    
    if options.proxy == "http":
        os.system('sudo cp apt.conf /etc/apt')
        os.system('sudo rm /etc/apt/sources.list.d/google.list')
        os.system('sudo apt-get update && sudo apt-get dist-upgrade')
    elif options.proxy == "socks":
        os.system('sudo rm /etc/apt/apt.conf')
        os.system('sudo cp google.list /etc/apt/sources.list.d/google.list')
        os.system('sudo tsocks apt-get update && sudo tsocks apt-get dist-upgrade')
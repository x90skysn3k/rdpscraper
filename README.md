# RDP Scraper

Created by: Steven Laura/@steven1664 && Jacob Robles/@shellfail && Shane Young/@x90skysn3k

#### Version - 0.1

# Installation

```pip install -r requirements.txt```

# Usage

First do an nmap scan with ```-oG nmap.gnmap``` or ```-oX nmap.xml```.

Command: ```./rdpscraper.py --file nmap.gnmap```

Command: ```./rdpscraper.py --file nmap.xml```

# Changelog
* v0.3
    * write usernames to files (wip)
    * added output option
    * added verbosity option
* v0.2
    * reading and writing through temp directories
    * output text to directory
    * tune image taking
* v0.1
    * initial commit and code for screenshot and reading images

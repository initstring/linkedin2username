# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn.
This is a pure web-scraper, no API key required.
```
usage: linkedin2username.py username company [-p PASSWORD] [-d DEPTH] [-s SLEEP]

positional arguments:
  username              A valid LinkedIn username.
  company               Numerical company ID assigned by LinkedIn 
                        (company employees and look at URL on website to find)

optional arguments:
  -h, --help            show this help message and exit
  -p PASSWORD, --password PASSWORD
                        Optionally specific password on the command line. If
                        not specified, will prompt and not display on screen.
  -d DEPTH, --depth DEPTH
                        Search depth. Defaults to 5 pages.
  -s SLEEP, --sleep SLEEP
                        Seconds to sleep between pages. defaults to 1
```

# Progress
I could use some help fixing the regex - right now, it will pull names of shared connections as well. Annoying but still works for my pentesting needs.

It will create a few files in your local directory:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe


# Planned Enhancements
- Automatically find and assign company ID
- General error checking
- A cool banner, of course
- Adding nice comments (sorry, I was in a hurry!)
- Adding additional filters (location, job title, etc)

# Credits
I'm a shit coder, but here are some better coders I ~~stole from~~ was inspired by:
- **garromark** in [this thread](https://stackoverflow.com/questions/18907503/logging-in-to-linkedin-with-python-requests-sessions).

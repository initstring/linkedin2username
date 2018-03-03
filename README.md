# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn.

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of possible username formats for all employees of a company you point it at.

The scraping hits only the search pages, so it shouldn't notify everyone you've looked at their profiles if you have that nasty setting enabled.

Use an account with a lot of connections, otherwise you'll get crappy results.

Here's what you get:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe

# Example
Here's an example to pull 100 pages of employees of Google:
```
$ python linkedin2username.py myname@email.com 1441 -d 100
```

# Full Help
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
  -r REGION, --region REGION
                        Limit search to region. Try a country code like 'AU'
                        or 'US' here.
```

# Progress
I could use some help fixing the regex - right now, it will pull names of shared connections as well. Annoying but still works for my pentesting needs.


# Planned Enhancements
- Automatically find and assign company ID
- General error checking
- A cool banner, of course
- Adding nice comments (sorry, I was in a hurry!)
- Adding additional search filters (like job title)

# Credits
I'm a shit coder, but here are some better coders I ~~stole from~~ was inspired by:
- **garromark** in [this thread](https://stackoverflow.com/questions/18907503/logging-in-to-linkedin-with-python-requests-sessions).

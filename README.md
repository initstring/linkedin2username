# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn.

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of possible username formats for all employees of a company you point it at.

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
                        (search company employees and look at URL on website to find)

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
Finally fixed the issue where it would grab mutual connections. Sending a mobile user agents gives an easier to parse response, so this is what the script does now.


# Planned Enhancements
- Automatically find and assign company ID
- General error checking
- A cool banner, of course
- Adding nice comments (sorry, I was in a hurry!)
- Adding additional search filters (like job title)

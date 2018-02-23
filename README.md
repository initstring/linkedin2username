# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn

# Progress
This is a very early version as I needed something to work right away. It sucks. It works but it also pulls the names of mutual connections - I need to work through a bit of regex hell to fix that.

Right now, you need to edit the file with your username and password, as well as the numerical identifier that LinkedIn assigns to companies. You can find it in the URL when you search for employees of a given company.

It will create a few files in your local directory:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe


# Planned Enhancements
- Pass arguments for username, password, and company
- General error checking
- A cool banner, of course
- Adding nice comments (sorry, I was in a hurry!)

# Credits
I'm a shit coder, but here are some better coders I ~~stole from~~ was inspired by:
- **garromark** in [this thread](https://stackoverflow.com/questions/18907503/logging-in-to-linkedin-with-python-requests-sessions).

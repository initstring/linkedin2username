# linkedin2username
OSINT Tool: Generate username lists from companies on LinkedIn

# Progress
Not pretty, but it works. Works better if you use an account with a lot of contacts - some people have privacy settings to return their name as "LinkedIn Member" if you are not in their network.

Currently it also pulls the names of mutual connections - I need to work through a bit of regex hell to fix that.

Edit the file (in between the ############## sections) with your username and password, as well as the numerical identifier that LinkedIn assigns to companies. You can find it in the URL when you search for employees of a given company.

It will create a few files in your local directory:
- first.last.txt: Usernames like Joe.Schmoe
- flast.txt:      Usernames like JSchmoe
- firstl.txt:     Usernames like JoeS
- rawnames.txt:   Full name like Joe Schmoe


# Planned Enhancements
- Pass arguments for username, password, and company
- Automatically find and assign company ID
- General error checking
- A cool banner, of course
- Adding nice comments (sorry, I was in a hurry!)

# Credits
I'm a shit coder, but here are some better coders I ~~stole from~~ was inspired by:
- **garromark** in [this thread](https://stackoverflow.com/questions/18907503/logging-in-to-linkedin-with-python-requests-sessions).

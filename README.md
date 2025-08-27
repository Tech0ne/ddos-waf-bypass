# EPITECH DDoS WAF bypass

Bypass the new anoying DDoS WAF on https://intra.epitech.eu

## How to use:

First, manually login to https://intra.epitech.eu/

Once logged in, grab your `user` cookie.

You can then make scripts using ddos_waf_bypass as a module:

```py
from ddos_waf_bypass import login
from getpass import getpass

session = login(getpass("user cookie: "))

# session is now an authenticated intra session
# from here, you can freely interact with the poorly designed and awefully documented "API"
```

Note: install requirements using `python3 -m pip install -r requirements.txt`

> tokens usually last around 7 days. you might need to change it after a week.
> you can also setup a browser extension to retreive the token. see [here](https://github.com/Tech0ne/epi-notify/tree/main/web-extention/) for ideas

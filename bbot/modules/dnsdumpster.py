import re
from bs4 import BeautifulSoup

from .crobat import crobat


class dnsdumpster(crobat):
    flags = ["subdomain-enum", "passive"]
    watched_events = ["DNS_NAME"]
    produced_events = ["DNS_NAME"]

    deps_pip = ["beautifulsoup4", "lxml"]

    base_url = "https://dnsdumpster.com"

    def query(self, domain):
        ret = []
        # first, get the CSRF tokens
        res1 = self.helpers.request(self.base_url)
        status_code = getattr(res1, "status_code", 0)
        if status_code in [429]:
            self.warning(f'Too many requests "{status_code}"')
            return ret
        elif status_code not in [200]:
            self.warning(f'Bad response code "{status_code}" from DNSDumpster')
            return ret
        else:
            self.debug(f'Valid response code "{status_code}" from DNSDumpster')
        html = BeautifulSoup(res1.content, features="lxml")
        csrftoken = None
        csrfmiddlewaretoken = None
        try:
            for cookie in res1.headers.get("set-cookie", "").split(";"):
                try:
                    k, v = cookie.split("=", 1)
                except ValueError:
                    self.warning("Error retrieving cookie")
                    return ret
                if k == "csrftoken":
                    csrftoken = str(v)
            csrfmiddlewaretoken = html.find("input", {"name": "csrfmiddlewaretoken"}).attrs.get("value", None)
        except AttributeError:
            pass

        # Abort if we didn't get the tokens
        if not csrftoken or not csrfmiddlewaretoken:
            self.verbose("Error obtaining CSRF tokens")
            self.errorState = True
            return ret
        else:
            self.debug("Successfully obtained CSRF tokens")

        # Otherwise, do the needful
        subdomains = set()
        res2 = self.helpers.request(
            f"{self.base_url}/",
            method="POST",
            cookies={"csrftoken": csrftoken},
            data={
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "targetip": str(domain).lower(),
                "user": "free",
            },
            headers={
                "origin": "https://dnsdumpster.com",
                "referer": "https://dnsdumpster.com/",
            },
        )
        status_code = getattr(res2, "status_code", 0)
        if status_code not in [200]:
            self.warning(f'Bad response code "{status_code}" from DNSDumpster')
            return ret

        html = BeautifulSoup(res2.content, features="lxml")
        escaped_domain = re.escape(domain)
        match_pattern = re.compile(r"^[\w\.-]+\." + escaped_domain + r"$")
        for subdomain in html.findAll(text=match_pattern):
            subdomains.add(str(subdomain).strip().lower())

        return list(subdomains)

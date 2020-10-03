import requests
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter

DEFAULT_TIMEOUT = 5 # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    """Borrowed from https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#setting-default-timeouts"""
    def __init__(self, *args, **kwargs): # type: ignore
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request: PreparedRequest, **kwargs) -> Response:  # type: ignore
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def make_session() -> requests.Session:
    session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=2.5)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # TODO: use https://toolbelt.readthedocs.io/en/latest/dumputils.html to dump info about
    #  requests and responses?

    return session


requests = make_session()  # type: ignore

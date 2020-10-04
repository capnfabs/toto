import os
import pathlib
from datetime import datetime
from typing import Any

import requests
from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter
from requests_toolbelt.utils import dump

from utils import continue_on_error

DEFAULT_TIMEOUT = 5 # seconds

REQUEST_LOG_DIR = './request-log/'

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

def dump_response(resp: requests.Response, *_args: Any, **_kwargs: Any) -> None:
    with continue_on_error():
        pathlib.Path(REQUEST_LOG_DIR).mkdir(parents=True, exist_ok=True)
        data = dump.dump_all(resp)
        formatted_date = datetime.utcnow().isoformat().replace(':', '_')
        # Just something unique to avoid collisions
        suffix = os.urandom(4).hex()
        filename = f'{formatted_date}_{suffix}.txt'
        with open(pathlib.Path(REQUEST_LOG_DIR, filename), 'wb') as file:
            file.write(data)
        print(f'📬 Wrote request/response to {filename}')


def make_session() -> requests.Session:
    session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=2.5)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.hooks['response'] = dump_response

    return session


requests = make_session()  # type: ignore

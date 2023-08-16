from unittest import mock
from urllib.parse import parse_qs, urlparse

from mylar import cv


FAKE_CV_ROOT = "http://cv/"
FAKE_CV_API_KEY = "kraventhehunter2"


def _unwrapping_parse_qs(query):
    ret = {}
    for key, value in parse_qs(query).items():
        assert len(value) == 1
        ret[key] = value[0]
    return ret


class FakeConfigModule:
    COMICVINE_API = FAKE_CV_API_KEY
    CVAPI_RATE = 2
    CV_VERIFY = False


@mock.patch("mylar.cv.time.sleep", lambda _: None)
@mock.patch("mylar.cv.mylar.CONFIG", FakeConfigModule())
@mock.patch("mylar.cv.mylar.CVURL", FAKE_CV_ROOT)
class TestPullDetails:

    @staticmethod
    def _get_validated_parts(m_get):
        assert 1 == m_get.call_count
        get_args, _get_kwargs = m_get.call_args

        url_parts = urlparse(get_args[0])
        assert url_parts.scheme == "http"
        assert url_parts.netloc == "cv"

        query_parts = _unwrapping_parse_qs(url_parts.query)
        assert query_parts["api_key"] == FAKE_CV_API_KEY

        return url_parts, query_parts

    def test_comic(self):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails("1234", "comic")

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/volume/4050-1234/"

        assert query_parts["format"] == "xml"
        assert query_parts["field_list"] == "name,count_of_issues,issues,start_year,site_detail_url,image,publisher,description,first_issue,deck,aliases"

from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest

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
    CV_ONLY = False
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

    def test_issue_cv_only_no_arclist(self):
        cv.mylar.CONFIG.CV_ONLY = True
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails("1234", "issue", offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issues/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "volume:1234"
        assert query_parts["field_list"] == "cover_date,description,id,image,issue_number,name,date_last_updated,store_date"
        assert query_parts["offset"] == "4"

    def test_issue_cv_only_arclist(self):
        cv.mylar.CONFIG.CV_ONLY = True
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, "issue", arclist="1|2|3|4", offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issues/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "id:1|2|3|4"
        assert query_parts["field_list"] == "cover_date,id,issue_number,name,date_last_updated,store_date,volume"
        assert query_parts["offset"] == "4"

    def test_issue_not_cv_only(self):
        cv.mylar.CONFIG.CV_ONLY = False
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails("1234", "issue", offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        # This is what the code currently does, it should be 4050-1234 like 'comic'
        assert url_parts.path == "/volume/1234/"

        # The code currently doesn't prepend `field_list=` to its field list,
        # so the fields aren't honoured
        assert query_parts["format"] == "xml"
        assert query_parts["offset"] == "4"

    @pytest.mark.parametrize("rtype", ("image", "firstissue", "imprints_first"))
    def test_frontmatter(self, rtype):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, rtype, issueid="4321")

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issues/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "id:4321"
        assert query_parts["field_list"] == "cover_date,store_date,image"

    def test_storyarc(self):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, "storyarc", issueid="4321")

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/story_arcs/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "name:4321"
        assert query_parts["field_list"] == "cover_date"

    def test_comicyears(self):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, "comicyears", comicidlist="1|2|3|4", offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/volumes/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "id:1|2|3|4"
        assert query_parts["field_list"] == "name,id,start_year,publisher,description,deck,aliases,count_of_issues"
        assert query_parts["offset"] == "4"

    def test_import(self):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, "import", comicidlist="1|2|3|4", offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issues/"

        assert query_parts["format"] == "xml"
        assert query_parts["filter"] == "id:1|2|3|4"
        assert query_parts["field_list"] == "cover_date,id,issue_number,name,date_last_updated,store_date,volume"
        assert query_parts["offset"] == "4"

    def test_single_issue(self):
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'{}'
            cv.pulldetails(None, "single_issue", issueid="1234")

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issue/4000-1234"

        assert query_parts["format"] == "json"

    def test_db_updater(self):
        date_info = {"start_date": "SD", "end_date": "ED"}
        with mock.patch("mylar.cv.requests.get") as m_get:
            m_get.return_value.content = b'<?xml version="1.0" encoding="utf-8"?><response/>'
            cv.pulldetails(None, "db_updater", dateinfo=date_info, offset=4)

        url_parts, query_parts = self._get_validated_parts(m_get)
        assert url_parts.path == "/issues/"

        assert query_parts["format"] == "json"
        assert query_parts["filter"] == f"date_last_updated:{date_info['start_date']}|{date_info['end_date']}"
        assert query_parts["field_list"] == "date_last_updated,id,volume,issue_number"
        assert query_parts["sort"] == "date_last_updated:asc"
        assert query_parts["offset"] == "4"

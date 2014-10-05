from bs4 import BeautifulSoup
import unittest
import mock
import re

from source.lib import to_unicode, to_str, get_counters, check_for_meta, GOOGLE_MARKET_PREFIX, GOOGLE_PLAY_PREFIX, \
    fix_market_url, make_pycurl_request, get_url, REDIRECT_META, REDIRECT_HTTP, get_redirect_history, prepare_url


__author__ = 'warprobot'


class InitTestCase(unittest.TestCase):
    def test_to_unicode_with_unicode(self):
        """
        Test to_unicode with already unicode string in input.
        """
        value = u'unicodeText'
        result = to_unicode(value)
        assert isinstance(result, unicode) is True

    def test_to_unicode_with_ascii(self):
        """
        Test to_unicode with ascii input
        """
        value = 'ASCII_TEXT'
        result = to_unicode(value)
        assert isinstance(result, unicode) is True

    def test_to_str_with_unicode(self):
        """
        Test to_str with unicode input
        """
        value = u'unicodeee'
        result = to_str(value)
        assert isinstance(result, str) is True

    def test_to_str_with_ascii(self):
        """
        Test to_str with ascii input
        """
        value = 'ascii'
        result = to_str(value)
        assert isinstance(result, str) is True

    def test_get_counters(self):
        """
        Detect counters in content
        """
        counter_name = 'RAMBLER_TOP100'
        content = "<html><head></head><body><img src=\"http://counter.rambler.ru/top100.cnt?264737\"" \
                  + " alt=\"\" width=\"1\" height=\"1\" style=\"border:0;position:absolute;" \
                  + "left:-10000px;\" /></body></html>"
        self.assertEquals(get_counters(content), [counter_name])

    def test_get_counters_dummy_content(self):
        """
        Content doesn't contain counters // for more branch coverage
        """
        content = 'Some dummy content without counters'
        assert get_counters(content) == []

    def test_check_for_meta_dfs(self):
        """
        DFS -> 100% line coverage, but bad branch cov.
        """
        result = mock.MagicMock(name="result")
        result.attrs = {
            "content": "wat;url=",
            "http-equiv": "refresh",
        }
        url = 'example.com/hell.php?what=123'
        result.__getitem__ = mock.Mock(return_value=result.attrs["content"] + url)
        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            check = check_for_meta("content", "url")
            self.assertEquals(check, url)

    def test_check_for_meta_no_meta(self):
        """
        Result is None
        """
        result = None
        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            self.assertIsNone(check_for_meta("content", "url"))

    def test_check_for_meta_no_content(self):
        """
        No content in meta
        """
        result = mock.MagicMock(name="result")
        result.attrs = {
            "abc": "contentDummy",
        }
        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            self.assertIsNone(check_for_meta("content", "url"))


    def test_check_for_meta_no_http_equiv(self):
        """
        No http_equiv in result
        """
        result = mock.MagicMock(name="result")
        result.attrs = {
            "content": "contentDummy",
        }
        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            self.assertIsNone(check_for_meta("content", "url"))

    def test_check_for_meta_wrong_length(self):
        """
        Splitted content length is wrong
        """
        result = mock.MagicMock(name="result")
        result.attrs = {
            "content": "dummy;dummy;dummy",
            "http-equiv": "refresh"
        }
        result.__getitem__ = mock.Mock(return_value=result.attrs["content"])
        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            self.assertIsNone(check_for_meta("content", "url"))

    @mock.patch.object(re, 'search', mock.Mock(return_value=None))
    def test_check_for_meta_wrong_search(self):
        """
        re.search returned none
        """
        result = mock.MagicMock(name="result")
        result.attrs = {
            "content": "wat;url=",
            "http-equiv": "refresh",
        }
        url = 'example.com/hell.php?what=123'
        result.__getitem__ = mock.Mock(return_value=result.attrs["content"] + url)

        with mock.patch.object(BeautifulSoup, "find", return_value=result):
            with mock.patch("source.lib.urljoin", mock.Mock()):
                self.assertIsNone(check_for_meta("content", "url"))

    def test_fix_market_url(self):
        """
        Market url -> http:/:
        """
        market_url = GOOGLE_MARKET_PREFIX + "details?id=air.com.terrypaton.tc2"
        http_url = GOOGLE_PLAY_PREFIX + "details?id=air.com.terrypaton.tc2"
        self.assertEqual(fix_market_url(market_url), http_url)

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_pycurl_request_dfs(self):
        """
        DFS -> 100% line cov

        """
        content = "this is original content"
        my_curl = mock.Mock()
        my_buffer = mock.Mock()
        redirect_url = "ya.ru"
        useragent = "ua"
        with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=my_curl)), \
             mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)), \
             mock.patch('source.lib.to_str', mock.Mock()), \
             mock.patch('source.lib.StringIO', mock.Mock(return_value=my_buffer)):
            my_buffer.getvalue.return_value = content
            self.assertEquals(make_pycurl_request(url="url", timeout=1, useragent=useragent),
                              (content, redirect_url))
            my_curl.setopt.assert_any_call(my_curl.USERAGENT, useragent)

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_pycurl_request_without_agent(self):
        """
        without agent
        """
        content = "this is original content"
        my_curl = mock.Mock()
        my_buffer = mock.Mock()
        with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=my_curl)), \
             mock.patch('source.lib.to_unicode', mock.Mock()), \
             mock.patch('source.lib.to_str', mock.Mock()), \
             mock.patch('source.lib.StringIO', mock.Mock(return_value=my_buffer)):
            my_buffer.getvalue.return_value = content
            my_curl.getinfo.return_value = None
            self.assertEquals(make_pycurl_request(url="url", timeout=1),
                              (content, None))

    def test_get_url_ignore_ok_login_redirects(self):
        """
        ignoring ok login redirects
        """
        content = "dummy content"
        new_redirect_url = "http://odnoklassniki.ru/123.123st.redirect"

        with mock.patch("source.lib.make_pycurl_request",
                        mock.Mock(return_value=(content, new_redirect_url))):
            self.assertEquals(get_url("url", timeout=1), (None, None, content))

    def test_get_url_wrong_url(self):
        """
        error in url
        """
        url = "wrong url"
        with mock.patch("source.lib.make_pycurl_request", mock.Mock(side_effect=ValueError('Value Error'))):
            self.assertEquals(get_url(url, timeout=1), (url, 'ERROR', None))

    def test_get_url_market_url_http_redirect_type(self):
        """
        Input market_url
        """
        with mock.patch('source.lib.fix_market_url', mock.Mock()):
            redirect_url = "market://details"
            prepare_url_return = 'become after prepare'
            content = 'dummyContent'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, redirect_url))):
                with mock.patch('source.lib.prepare_url', mock.Mock(return_value=prepare_url_return)):
                    self.assertEquals(get_url(redirect_url, timeout=1), (prepare_url_return, REDIRECT_HTTP, content))

    def test_get_url_none_redirect_url_none_redirect_type(self):
        """
        redirect_url is none
        None redirect_type
        """
        with mock.patch('source.lib.fix_market_url', mock.Mock()):
            redirect_url = None
            final_url = None
            content = 'this is original content'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, redirect_url))), \
                 mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)), \
                 mock.patch('source.lib.prepare_url', mock.Mock(return_value=final_url)):
                self.assertEquals(get_url('dummyurl', timeout=1), (final_url, None, content))

    def test_get_url_none_redirect_url_meta_redirect_type(self):
        """
        redirect url is none pri make_pycurl_request
        return meta redirect type
        """
        with mock.patch('source.lib.fix_market_url', mock.Mock()):
            redirect_url = "not none redirect url"
            content = 'this is original content'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, None))):
                with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=redirect_url)):
                    with mock.patch('source.lib.prepare_url',
                                    mock.Mock(return_value=redirect_url)):
                        self.assertEquals(get_url('dummyurl', timeout=1), (redirect_url, REDIRECT_META, content))

    def test_redirect_history_match_ok(self):
        """
        ok matching
        """
        ok_url = u'https://odnoklassniki.ru/'
        with mock.patch("source.lib.prepare_url", mock.Mock(return_value=ok_url)):
            self.assertEquals(([], [ok_url], []), get_redirect_history(url=ok_url, timeout=1))

    def test_redirect_history_match_mm(self):
        """
        mm matching
        """
        mm_url = u'https://my.mail.ru/apps/'
        with mock.patch("source.lib.prepare_url", mock.Mock(return_value=mm_url)):
            self.assertEquals(([], [mm_url], []), get_redirect_history(url=mm_url, timeout=1))

    def test_redirect_history_no_redirect_url(self):
        url = "http://example.ru"
        redirect_url = None
        redirect_type = None
        content = None
        with mock.patch("source.lib.prepare_url", mock.Mock(return_value=u'http://example.ru')), \
             mock.patch("source.lib.get_url", mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals(([], [url], []),
                              get_redirect_history(url=url, timeout=1))

    def test_get_redirect_history_error_redirect_type(self):
        """
        break with redirect_type = ERROR
        """
        url = "http://example.ru"
        redirect_url = "http://r.ru"
        redirect_type = 'ERROR'
        content = "<html><head></head><body><img src=\"http://counter.rambler.ru/top100.cnt?264737\"" \
                  + " alt=\"\" width=\"1\" height=\"1\" style=\"border:0;position:absolute;" \
                  + "left:-10000px;\" /></body></html>"
        rambler_counter = "RAMBLER_TOP100"
        history_types = [redirect_type]
        history_urls = [url, redirect_url]
        counters = [rambler_counter]
        with mock.patch("source.lib.prepare_url", mock.Mock(return_value=u'http://example.ru')), \
             mock.patch("source.lib.get_url", mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, counters), get_redirect_history(url=url, timeout=1))

    def test_get_redirect_history_max_redirect_break(self):
        """
        only 1 redirect
        """
        url = "http://example.ru"
        redirect_url = "http://r.ru"
        redirect_type = "http_status"
        content = None
        history_types = [redirect_type]
        history_urls = [url, redirect_url]
        with mock.patch('source.lib.get_url', mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, []),
                              get_redirect_history(url=url, timeout=1, max_redirects=1))

    def test_get_redirect_history_url_multiple_iterations(self):
        """
        More than 1 time while
        """
        url = 'http://example2.com/'
        redirect_type = 'http_status'
        content = None
        with mock.patch("source.lib.get_url", mock.Mock(return_value=(url, redirect_type, content))):
            self.assertEqual((['http_status', 'http_status'],
                              [u'http://example.com/', 'http://example2.com/', 'http://example2.com/'], []),
                             get_redirect_history(url='http://example.com/', timeout=1))

    def test_prepare_url_none_url(self):
        """
        Url is None
        """
        self.assertIsNone(prepare_url(None))

    def test_prepare_url_exception(self):
        """
        raise exception
        """
        my_mock = mock.MagicMock()
        my_mock.encode.side_effect = UnicodeError("UnicodeError")
        with mock.patch('source.lib.urlparse', mock.Mock(return_value=[my_mock] * 6)),\
                mock.patch('source.lib.logger', mock.MagicMock()) as logger:
            prepare_url('url')
            assert logger.error.called

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from pysolr import (Solr, Results, SolrError, unescape_html, safe_urlencode,
                   force_unicode, force_bytes, sanitize, json, ET, IS_PY3)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

if IS_PY3:
    from io import StringIO
else:
    from StringIO import StringIO


class UtilsTestCase(unittest.TestCase):
    def test_unescape_html(self):
        self.assertEqual(unescape_html('Hello &#149; world'), 'Hello \x95 world')
        self.assertEqual(unescape_html('Hello &#x64; world'), 'Hello d world')
        self.assertEqual(unescape_html('Hello &amp; ☃'), 'Hello & ☃')
        self.assertEqual(unescape_html('Hello &doesnotexist; world'), 'Hello &doesnotexist; world')

    def test_safe_urlencode(self):
        self.assertEqual(force_unicode(unquote_plus(safe_urlencode({'test': 'Hello ☃! Helllo world!'}))), 'test=Hello ☃! Helllo world!')
        self.assertEqual(force_unicode(unquote_plus(safe_urlencode({'test': ['Hello ☃!', 'Helllo world!']}, True))), "test=Hello \u2603!&test=Helllo world!")
        self.assertEqual(force_unicode(unquote_plus(safe_urlencode({'test': ('Hello ☃!', 'Helllo world!')}, True))), "test=Hello \u2603!&test=Helllo world!")

    def test_sanitize(self):
        self.assertEqual(sanitize('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19h\x1ae\x1bl\x1cl\x1do\x1e\x1f'), 'hello'),

    def test_force_unicode(self):
        self.assertEqual(force_unicode(b'Hello \xe2\x98\x83'), 'Hello ☃')
        # Don't mangle, it's already Unicode.
        self.assertEqual(force_unicode('Hello ☃'), 'Hello ☃')

        self.assertEqual(force_unicode(1), '1', "force_unicode() should convert ints")
        self.assertEqual(force_unicode(1.0), '1.0', "force_unicode() should convert floats")
        self.assertEqual(force_unicode(None), 'None', 'force_unicode() should convert None')

    def test_force_bytes(self):
        self.assertEqual(force_bytes('Hello ☃'), b'Hello \xe2\x98\x83')
        # Don't mangle, it's already a bytestring.
        self.assertEqual(force_bytes(b'Hello \xe2\x98\x83'), b'Hello \xe2\x98\x83')


class ResultsTestCase(unittest.TestCase):
    def test_init(self):
        default_results = Results([{'id': 1}, {'id': 2}], 2)
        self.assertEqual(default_results.docs, [{'id': 1}, {'id': 2}])
        self.assertEqual(default_results.hits, 2)
        self.assertEqual(default_results.highlighting, {})
        self.assertEqual(default_results.facets, {})
        self.assertEqual(default_results.spellcheck, {})
        self.assertEqual(default_results.stats, {})
        self.assertEqual(default_results.qtime, None)
        self.assertEqual(default_results.debug, {})
        self.assertEqual(default_results.grouped, {})

        full_results = Results(
            docs=[{'id': 1}, {'id': 2}, {'id': 3}],
            hits=3,
            # Fake data just to check assignments.
            highlighting='hi',
            facets='fa',
            spellcheck='sp',
            stats='st',
            qtime='0.001',
            debug=True,
            grouped=['a']
        )
        self.assertEqual(full_results.docs, [{'id': 1}, {'id': 2}, {'id': 3}])
        self.assertEqual(full_results.hits, 3)
        self.assertEqual(full_results.highlighting, 'hi')
        self.assertEqual(full_results.facets, 'fa')
        self.assertEqual(full_results.spellcheck, 'sp')
        self.assertEqual(full_results.stats, 'st')
        self.assertEqual(full_results.qtime, '0.001')
        self.assertEqual(full_results.debug, True)
        self.assertEqual(full_results.grouped, ['a'])

    def test_len(self):
        small_results = Results([{'id': 1}, {'id': 2}], 2)
        self.assertEqual(len(small_results), 2)

        wrong_hits_results = Results([{'id': 1}, {'id': 2}, {'id': 3}], 7)
        self.assertEqual(len(wrong_hits_results), 3)

    def test_iter(self):
        long_results = Results([{'id': 1}, {'id': 2}, {'id': 3}], 3)

        to_iter = list(long_results)
        self.assertEqual(to_iter[0], {'id': 1})
        self.assertEqual(to_iter[1], {'id': 2})
        self.assertEqual(to_iter[2], {'id': 3})


class SolrTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrTestCase, self).setUp()
        self.default_solr = Solr('http://localhost:8983/solr/core0')
        # Short timeouts.
        self.solr = Solr('http://localhost:8983/solr/core0', timeout=2)
        self.docs = [
            {
                'id': 'doc_1',
                'title': 'Example doc 1',
                'price': 12.59,
                'popularity': 10,
            },
            {
                'id': 'doc_2',
                'title': 'Another example ☃ doc 2',
                'price': 13.69,
                'popularity': 7,
            },
            {
                'id': 'doc_3',
                'title': 'Another thing',
                'price': 2.35,
                'popularity': 8,
            },
            {
                'id': 'doc_4',
                'title': 'doc rock',
                'price': 99.99,
                'popularity': 10,
            },
            {
                'id': 'doc_5',
                'title': 'Boring',
                'price': 1.12,
                'popularity': 2,
            },
        ]

        # Clear it.
        self.solr.delete(q='*:*')

        # Index our docs. Yes, this leans on functionality we're going to test
        # later & if it's broken, everything will catastrophically fail.
        # Such is life.
        self.solr.add(self.docs)

    def tearDown(self):
        self.solr.delete(q='*:*')
        super(SolrTestCase, self).tearDown()

    def test_init(self):
        self.assertEqual(self.default_solr.url, 'http://localhost:8983/solr/core0')
        self.assertTrue(isinstance(self.default_solr.decoder, json.JSONDecoder))
        self.assertEqual(self.default_solr.timeout, 60)

        self.assertEqual(self.solr.url, 'http://localhost:8983/solr/core0')
        self.assertTrue(isinstance(self.solr.decoder, json.JSONDecoder))
        self.assertEqual(self.solr.timeout, 2)

    def test__create_full_url(self):
        # Nada.
        self.assertEqual(self.solr._create_full_url(path=''), 'http://localhost:8983/solr/core0')
        # Basic path.
        self.assertEqual(self.solr._create_full_url(path='pysolr_tests'), 'http://localhost:8983/solr/core0/pysolr_tests')
        # Leading slash (& making sure we don't touch the trailing slash).
        self.assertEqual(self.solr._create_full_url(path='/pysolr_tests/select/?whatever=/'), 'http://localhost:8983/solr/core0/pysolr_tests/select/?whatever=/')

    def test__send_request(self):
        # Test a valid request.
        resp_body = self.solr._send_request('GET', 'select/?q=doc&wt=json')
        self.assertTrue('"numFound":3' in resp_body)

        # Test a lowercase method & a body.
        xml_body = '<add><doc><field name="id">doc_12</field><field name="title">Whee!</field></doc></add>'
        resp_body = self.solr._send_request('POST', 'update/?commit=true', body=xml_body, headers={
            'Content-type': 'text/xml; charset=utf-8',
        })
        self.assertTrue('<int name="status">0</int>' in resp_body)

        # Test a non-existent URL.
        old_url = self.solr.url
        self.solr.url = 'http://127.0.0.1:567898/wahtever'
        self.assertRaises(SolrError, self.solr._send_request, 'get', 'select/?q=doc&wt=json')
        self.solr.url = old_url

    def test__select(self):
        # Short params.
        resp_body = self.solr._select({'q': 'doc'})
        resp_data = json.loads(resp_body)
        self.assertEqual(resp_data['response']['numFound'], 3)

        # Long params.
        resp_body = self.solr._select({'q': 'doc' * 1024})
        resp_data = json.loads(resp_body)
        self.assertEqual(resp_data['response']['numFound'], 0)
        self.assertEqual(len(resp_data['responseHeader']['params']['q']), 3 * 1024)

    def test__mlt(self):
        resp_body = self.solr._mlt({'q': 'id:doc_1', 'mlt.fl': 'title'})
        resp_data = json.loads(resp_body)
        self.assertEqual(resp_data['response']['numFound'], 0)

    def test__suggest_terms(self):
        resp_body = self.solr._select({'terms.fl': 'title'})
        resp_data = json.loads(resp_body)
        self.assertEqual(resp_data['response']['numFound'], 0)

    def test__update(self):
        xml_body = '<add><doc><field name="id">doc_12</field><field name="title">Whee!</field></doc></add>'
        resp_body = self.solr._update(xml_body)
        self.assertTrue('<int name="status">0</int>' in resp_body)

    def test__extract_error(self):
        class RubbishResponse(object):
            def __init__(self, content, headers=None):
                self.content = content
                self.headers = headers

                if self.headers is None:
                    self.headers = {}

        # Just the reason.
        resp_1 = RubbishResponse("We don't care.", {'reason': 'Something went wrong.'})
        self.assertEqual(self.solr._extract_error(resp_1), "[Reason: Something went wrong.]")

        # Empty reason.
        resp_2 = RubbishResponse("We don't care.", {'reason': None})
        self.assertEqual(self.solr._extract_error(resp_2), "[Reason: None]\nWe don't care.")

        # No reason. Time to scrape.
        resp_3 = RubbishResponse('<html><body><pre>Something is broke.</pre></body></html>', {'server': 'jetty'})
        self.assertEqual(self.solr._extract_error(resp_3), "[Reason: Something is broke.]")

    def test__scrape_response(self):
        # Tomcat.
        resp_1 = self.solr._scrape_response({'server': 'coyote'}, '<html><body><p><span>Error message</span><span>messed up.</span></p></body></html>')
        self.assertEqual(resp_1, ('messed up.', ''))

        # Jetty.
        resp_2 = self.solr._scrape_response({'server': 'jetty'}, '<html><body><pre>Something is broke.</pre></body></html>')
        self.assertEqual(resp_2, ('Something is broke.', u''))

        # Broken Tomcat.
        resp_3 = self.solr._scrape_response({'server': 'coyote'}, '<html><body><p>Really broken. Scraping Java-generated HTML sucks.</pre></body></html>')
        self.assertEqual(resp_3, (None, u'<div><body><p>Really broken. Scraping Java-generated HTML sucks.</p></body></div>'))

        # Other.
        resp_4 = self.solr._scrape_response({'server': 'crapzilla'}, '<html><head><title>Wow. Seriously weird.</title></head><body><pre>Something is broke.</pre></body></html>')
        self.assertEqual(resp_4, ('Wow. Seriously weird.', u''))

    def test__from_python(self):
        self.assertEqual(self.solr._from_python(datetime.date(2013, 1, 18)), '2013-01-18T00:00:00Z')
        self.assertEqual(self.solr._from_python(datetime.datetime(2013, 1, 18, 0, 30, 28)), '2013-01-18T00:30:28Z')
        self.assertEqual(self.solr._from_python(True), 'true')
        self.assertEqual(self.solr._from_python(False), 'false')
        self.assertEqual(self.solr._from_python(1), '1')
        self.assertEqual(self.solr._from_python(1.2), '1.2')
        self.assertEqual(self.solr._from_python(b'hello'), 'hello')
        self.assertEqual(self.solr._from_python('hello ☃'), 'hello ☃')

    def test__to_python(self):
        self.assertEqual(self.solr._to_python('2013-01-18T00:00:00Z'), datetime.datetime(2013, 1, 18))
        self.assertEqual(self.solr._to_python('2013-01-18T00:30:28Z'), datetime.datetime(2013, 1, 18, 0, 30, 28))
        self.assertEqual(self.solr._to_python('true'), True)
        self.assertEqual(self.solr._to_python('false'), False)
        self.assertEqual(self.solr._to_python(1), 1)
        self.assertEqual(self.solr._to_python(1.2), 1.2)
        self.assertEqual(self.solr._to_python(b'hello'), 'hello')
        self.assertEqual(self.solr._to_python('hello ☃'), 'hello ☃')
        self.assertEqual(self.solr._to_python(['foo', 'bar']), 'foo')
        self.assertEqual(self.solr._to_python(('foo', 'bar')), 'foo')

    def test__is_null_value(self):
        self.assertTrue(self.solr._is_null_value(None))
        self.assertTrue(self.solr._is_null_value(''))

        self.assertFalse(self.solr._is_null_value('Hello'))
        self.assertFalse(self.solr._is_null_value(1))

    def test_search(self):
        results = self.solr.search('doc')
        self.assertEqual(len(results), 3)

        results = self.solr.search('example')
        self.assertEqual(len(results), 2)

        results = self.solr.search('nothing')
        self.assertEqual(len(results), 0)

        # Advanced options.
        results = self.solr.search('doc', **{
            'debug': 'true',
            'hl': 'true',
            'hl.fragsize': 8,
            'facet': 'on',
            'facet.field': 'popularity',
            'spellcheck': 'true',
            'spellcheck.collate': 'true',
            'spellcheck.count': 1,
            # TODO: Can't get these working in my test setup.
            # 'group': 'true',
            # 'group.field': 'id',
        })
        self.assertEqual(len(results), 3)
        self.assertTrue('explain' in results.debug)
        self.assertEqual(results.highlighting, {u'doc_4': {}, u'doc_2': {}, u'doc_1': {}})
        self.assertEqual(results.spellcheck, {})
        self.assertEqual(results.facets['facet_fields']['popularity'], ['10', 2, '7', 1, '2', 0, '8', 0])
        self.assertTrue(results.qtime is not None)
        # TODO: Can't get these working in my test setup.
        # self.assertEqual(results.grouped, '')

    def test_more_like_this(self):
        results = self.solr.more_like_this('id:doc_1', 'text')
        self.assertEqual(len(results), 0)

    def test_suggest_terms(self):
        results = self.solr.suggest_terms('title', '')
        self.assertEqual(len(results), 1)
        self.assertEqual(results, {'title': [('doc', 3), ('another', 2), ('example', 2), ('1', 1), ('2', 1), ('boring', 1), ('rock', 1), ('thing', 1)]})

    def test__build_doc(self):
        doc = {
            'id': 'doc_1',
            'title': 'Example doc ☃ 1',
            'price': 12.59,
            'popularity': 10,
        }
        doc_xml = force_unicode(ET.tostring(self.solr._build_doc(doc), encoding='utf-8'))
        self.assertTrue('<field name="title">Example doc ☃ 1</field>' in doc_xml)
        self.assertTrue('<field name="id">doc_1</field>' in doc_xml)
        self.assertEqual(len(doc_xml), 152)

    def test_add(self):
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.assertEqual(len(self.solr.search('example')), 2)

        self.solr.add([
            {
                'id': 'doc_6',
                'title': 'Newly added doc',
            },
            {
                'id': 'doc_7',
                'title': 'Another example doc',
            },
        ])

        self.assertEqual(len(self.solr.search('doc')), 5)
        self.assertEqual(len(self.solr.search('example')), 3)

    def test_add_with_boost(self):
        self.assertEqual(len(self.solr.search('doc')), 3)

        self.solr.add([{'id': 'doc_6', 'title': 'Important doc'}],
                      boost={'title': 10.0})

        self.solr.add([{'id': 'doc_7', 'title': 'Spam doc doc'}],
                      boost={'title': 0})

        res = self.solr.search('doc')
        self.assertEqual(len(res), 5)
        self.assertEqual('doc_6', res.docs[0]['id'])

    def test_delete(self):
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.solr.delete(id='doc_1')
        self.assertEqual(len(self.solr.search('doc')), 2)
        self.solr.delete(q='price:[0 TO 15]')
        self.assertEqual(len(self.solr.search('doc')), 1)

        self.assertEqual(len(self.solr.search('*:*')), 1)
        self.solr.delete(q='*:*')
        self.assertEqual(len(self.solr.search('*:*')), 0)

        # Need at least one.
        self.assertRaises(ValueError, self.solr.delete)
        # Can't have both.
        self.assertRaises(ValueError, self.solr.delete, id='foo', q='bar')

    def test_commit(self):
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.solr.add([
            {
                'id': 'doc_6',
                'title': 'Newly added doc',
            }
        ], commit=False)
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.solr.commit()
        self.assertEqual(len(self.solr.search('doc')), 4)

    def test_optimize(self):
        # Make sure it doesn't blow up. Side effects are hard to measure. :/
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.solr.add([
            {
                'id': 'doc_6',
                'title': 'Newly added doc',
            }
        ], commit=False)
        self.assertEqual(len(self.solr.search('doc')), 3)
        self.solr.optimize()
        self.assertEqual(len(self.solr.search('doc')), 4)

    def test_extract(self):
        fake_f = StringIO("""
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="haystack-test" content="test 1234">
                    <title>Test Title ☃&#x2603;</title>
                </head>
                    <body>foobar</body>
            </html>
        """)
        fake_f.name = "test.html"
        extracted = self.solr.extract(fake_f)

        # Verify documented response structure:
        self.assertIn('contents', extracted)
        self.assertIn('metadata', extracted)

        self.assertIn('foobar', extracted['contents'])

        m = extracted['metadata']

        self.assertEqual([fake_f.name], m['stream_name'])

        self.assertIn('haystack-test', m, "HTML metadata should have been extracted!")
        self.assertEqual(['test 1234'], m['haystack-test'])

        # Note the underhanded use of a double snowman to verify both that Tika
        # correctly decoded entities and that our UTF-8 characters survived the
        # round-trip:
        self.assertEqual(['Test Title ☃☃'], m['title'])

    def test_full_url(self):
        self.solr.url = 'http://localhost:8983/solr/'
        full_url = self.solr._create_full_url(path='/update')

        # Make sure trailing and leading slashes do not collide:
        self.assertEqual(full_url, 'http://localhost:8983/solr/update')

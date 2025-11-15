import ast
import datetime
import logging
import os
import random
import re
import time
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version
from xml.etree import ElementTree  # noqa: ICN001

import requests

try:
    from kazoo.client import KazooClient, KazooState
except ImportError:
    KazooClient = KazooState = None

try:
    # Prefer simplejson, if installed.
    import simplejson as json
except ImportError:
    import json


import html.entities as htmlentities
from http.client import HTTPException
from urllib.parse import quote, urlencode

__author__ = "Daniel Lindsley, Joseph Kocherhans, Jacob Kaplan-Moss, Thomas Rieder"
__all__ = ["Solr"]

try:
    __version__ = _get_version(__name__)
except PackageNotFoundError:
    __version__ = "0.0.dev0"


def get_version():
    return __version__


DATETIME_REGEX = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.\d+)?Z$"  # NOQA: E501
)
# dict key used to add nested documents to a document
NESTED_DOC_KEY = "_childDocuments_"

VALID_XML_CHARS_REGEX = re.compile(
    "[^\u0020-\ud7ff\u0009\u000a\u000d\ue000-\ufffd\U00010000-\U0010ffff]+"
)


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


# Add the ``NullHandler`` to avoid logging by default while still allowing
# others to attach their own handlers.
LOG = logging.getLogger("pysolr")
h = NullHandler()
LOG.addHandler(h)

# For debugging...
if os.environ.get("DEBUG_PYSOLR", "").lower() in ("true", "1"):
    LOG.setLevel(logging.DEBUG)
    stream = logging.StreamHandler()
    LOG.addHandler(stream)


def force_unicode(value):
    """
    Forces a bytestring to become a Unicode string.
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    elif not isinstance(value, str):
        value = str(value)

    return value


def force_bytes(value):
    """
    Forces a Unicode string to become a bytestring.
    """
    if isinstance(value, str):
        value = value.encode("utf-8", "backslashreplace")

    return value


def unescape_html(text):
    """
    Removes HTML or XML character references and entities from a text string.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.

    Source: http://effbot.org/zone/re-sub.htm#unescape-html
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(htmlentities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub(r"&#?\w+;", fixup, text)


def safe_urlencode(params, doseq=False):
    """
    URL-encode parameters using UTF-8 encoding.

    This is a wrapper around `urllib.parse.urlencode` that ensures
    consistent UTF-8 handling for all parameter values.
    """
    return urlencode(params, doseq)


def clean_xml_string(s):
    """
    Cleans string from invalid xml chars

    Solution was found there::

    http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
    """
    return VALID_XML_CHARS_REGEX.sub("", s)


class SolrError(Exception):
    pass


class Results(object):
    """
    Default results class for wrapping decoded (from JSON) solr responses.

    Required ``decoded`` argument must be a Solr response dictionary.
    Individual documents can be retrieved either through ``docs`` attribute
    or by iterating over results instance.

    Optional ``next_page_query`` argument is a callable to be invoked when
    iterating over the documents from the result.

    Example::

        results = Results({
            'response': {
                'docs': [{'id': 1}, {'id': 2}, {'id': 3}],
                'numFound': 3,
            }
        })

        # this:
        for doc in results:
            print doc

        # ... is equivalent to:
        for doc in results.docs:
            print doc

        # also:
        list(results) == results.docs

    Note that ``Results`` object does not support indexing and slicing. If you
    need to retrieve documents by index just use ``docs`` attribute.

    Other common response metadata (debug, highlighting, qtime, etc.) are
    available as attributes.

    The full response from Solr is provided as the `raw_response` dictionary for
    use with features which change the response format.
    """

    def __init__(self, decoded, next_page_query=None):
        self.raw_response = decoded

        # main response part of decoded Solr response
        response_part = decoded.get("response") or {}
        self.docs = response_part.get("docs", ())
        self.hits = response_part.get("numFound", 0)

        # other response metadata
        self.debug = decoded.get("debug", {})
        self.highlighting = decoded.get("highlighting", {})
        self.facets = decoded.get("facet_counts", {})
        self.spellcheck = decoded.get("spellcheck", {})
        self.stats = decoded.get("stats", {})
        self.qtime = decoded.get("responseHeader", {}).get("QTime", None)
        self.grouped = decoded.get("grouped", {})
        self.nextCursorMark = decoded.get("nextCursorMark", None)
        self._next_page_query = (
            self.nextCursorMark is not None and next_page_query
        ) or None

    def __len__(self):
        if self._next_page_query:
            return self.hits
        else:
            return len(self.docs)

    def __iter__(self):
        result = self
        while result:
            for d in result.docs:
                yield d
            result = result._next_page_query and result._next_page_query()


class Solr(object):
    """
    The main object for working with Solr.

    Optionally accepts ``decoder`` for an alternate JSON decoder instance.
    Default is ``json.JSONDecoder()``.

    Optionally accepts ``encoder`` for an alternate JSON Encoder instance.
    Default is ``json.JSONEncoder()``.

    Optionally accepts ``timeout`` for wait seconds until giving up on a
    request. Default is ``60`` seconds.

    Optionally accepts ``results_cls`` that specifies class of results object
    returned by ``.search()`` and ``.more_like_this()`` methods.
    Default is ``pysolr.Results``.

    Usage::

        solr = pysolr.Solr('http://localhost:8983/solr')
        # With a 10 second timeout.
        solr = pysolr.Solr('http://localhost:8983/solr', timeout=10)

        # with a dict as a default results class instead of pysolr.Results
        solr = pysolr.Solr('http://localhost:8983/solr', results_cls=dict)

    """

    def __init__(
        self,
        url,
        decoder=None,
        encoder=None,
        timeout=60,
        results_cls=Results,
        search_handler="select",
        use_qt_param=False,
        always_commit=False,
        auth=None,
        verify=True,
        session=None,
    ):
        self.decoder = decoder or json.JSONDecoder()
        self.encoder = encoder or json.JSONEncoder()
        self.url = url
        self.timeout = timeout
        self.log = self._get_log()
        self.session = session
        self.results_cls = results_cls
        self.search_handler = search_handler
        self.use_qt_param = use_qt_param
        self.auth = auth
        self.verify = verify
        self.always_commit = always_commit

    def get_session(self):
        if self.session is None:
            self.session = requests.Session()
            self.session.stream = False
            self.session.verify = self.verify
        return self.session

    def _get_log(self):
        return LOG

    def _create_full_url(self, path=""):
        if len(path):
            return "/".join([self.url.rstrip("/"), path.lstrip("/")])

        # No path? No problem.
        return self.url

    def _send_request(self, method, path="", body=None, headers=None, files=None):
        url = self._create_full_url(path)
        method = method.lower()
        log_body = body

        if headers is None:
            headers = {}

        if log_body is None:
            log_body = ""
        elif not isinstance(log_body, str):
            log_body = repr(body)

        self.log.debug(
            "Starting request to '%s' (%s) with body '%s'...",
            url,
            method,
            log_body[:10],
        )
        start_time = time.time()

        session = self.get_session()

        try:
            requests_method = getattr(session, method)
        except AttributeError:
            raise SolrError("Unable to use unknown HTTP method '{0}.".format(method))

        # Everything except the body can be Unicode. The body must be
        # encoded to bytes to work properly on Py3.
        bytes_body = body

        if bytes_body is not None:
            bytes_body = force_bytes(body)
        try:
            resp = requests_method(
                url,
                data=bytes_body,
                headers=headers,
                files=files,
                timeout=self.timeout,
                auth=self.auth,
            )
        except requests.exceptions.Timeout as err:
            error_message = "Connection to server '%s' timed out: %s"
            self.log.exception(error_message, url, err)  # NOQA: G200
            raise SolrError(error_message % (url, err))
        except requests.exceptions.ConnectionError as err:
            error_message = "Failed to connect to server at %s: %s"
            self.log.exception(error_message, url, err)  # NOQA: G200
            raise SolrError(error_message % (url, err))
        except HTTPException as err:
            error_message = "Unhandled error: %s %s: %s"
            self.log.exception(error_message, method, url, err)  # NOQA: G200
            raise SolrError(error_message % (method, url, err))

        end_time = time.time()
        self.log.info(
            "Finished '%s' (%s) with body '%s' in %0.3f seconds, with status %s",
            url,
            method,
            log_body[:10],
            end_time - start_time,
            resp.status_code,
        )

        if int(resp.status_code) != 200:
            error_message = "Solr responded with an error (HTTP %s): %s"
            solr_message = self._extract_error(resp)
            self.log.error(
                error_message,
                resp.status_code,
                solr_message,
                extra={
                    "data": {
                        "headers": resp.headers,
                        "response": resp.content,
                        "request_body": bytes_body,
                        "request_headers": headers,
                    }
                },
            )
            raise SolrError(error_message % (resp.status_code, solr_message))

        return force_unicode(resp.content)

    def _select(self, params, handler=None):
        """
        :param params:
        :param handler: defaults to self.search_handler (fallback to 'select')
        :return:
        """
        # Returns json docs unless otherwise specified
        params.setdefault("wt", "json")
        custom_handler = handler or self.search_handler
        handler = "select"
        if custom_handler:
            if self.use_qt_param:
                params["qt"] = custom_handler
            else:
                handler = custom_handler

        params_encoded = safe_urlencode(params, True)

        if len(params_encoded) < 1024:
            # Typical case.
            path = "%s/?%s" % (handler, params_encoded)
            return self._send_request("get", path)
        else:
            # Handles very long queries by submitting as a POST.
            path = "%s/" % handler
            headers = {
                "Content-type": "application/x-www-form-urlencoded; charset=utf-8"
            }
            return self._send_request(
                "post", path, body=params_encoded, headers=headers
            )

    def _mlt(self, params, handler="mlt"):
        return self._select(params, handler)

    def _suggest_terms(self, params, handler="terms"):
        return self._select(params, handler)

    def _update(
        self,
        message,
        clean_ctrl_chars=True,
        commit=None,
        softCommit=False,
        commitWithin=None,
        waitFlush=None,
        waitSearcher=None,
        overwrite=None,
        handler="update",
        solrapi="XML",
        min_rf=None,
    ):
        """
        Posts the given xml or json message to http://<self.url>/update and
        returns the result.

        Passing `clean_ctrl_chars` as False will prevent the message from being cleaned
        of control characters (default True). This is done by default because
        these characters would cause Solr to fail to parse the XML. Only pass
        False if you're positive your data is clean.
        """

        # Per http://wiki.apache.org/solr/UpdateXmlMessages, we can append a
        # ``commit=true`` to the URL and have the commit happen without a
        # second request.
        query_vars = []

        path_handler = handler
        if self.use_qt_param:
            path_handler = "select"
            query_vars.append("qt=%s" % safe_urlencode(handler, True))

        path = "%s/" % path_handler

        if commit is None:
            commit = self.always_commit

        if min_rf:
            query_vars.append("min_rf=%i" % min_rf)
        if commit:
            query_vars.append("commit=%s" % str(bool(commit)).lower())
        elif softCommit:
            query_vars.append("softCommit=%s" % str(bool(softCommit)).lower())
        elif commitWithin is not None:
            query_vars.append("commitWithin=%s" % str(int(commitWithin)))

        if waitFlush is not None:
            query_vars.append("waitFlush=%s" % str(bool(waitFlush)).lower())

        if overwrite is not None:
            query_vars.append("overwrite=%s" % str(bool(overwrite)).lower())

        if waitSearcher is not None:
            query_vars.append("waitSearcher=%s" % str(bool(waitSearcher)).lower())

        if query_vars:
            path = "%s?%s" % (path, "&".join(query_vars))

        # Clean the message of ctrl characters.
        if clean_ctrl_chars:
            message = sanitize(message)

        if solrapi == "XML":
            return self._send_request(
                "post", path, message, {"Content-type": "text/xml; charset=utf-8"}
            )
        elif solrapi == "JSON":
            return self._send_request(
                "post",
                path,
                message,
                {"Content-type": "application/json; charset=utf-8"},
            )
        else:
            raise ValueError("unknown solrapi {}".format(solrapi))

    def _extract_error(self, resp):
        """
        Extract the actual error message from a solr response.
        """
        reason = resp.headers.get("reason", None)
        full_response = None

        if reason is None:
            try:
                # if response is in json format
                reason = resp.json()["error"]["msg"]
            except KeyError:
                # if json response has unexpected structure
                full_response = resp.content
            except ValueError:
                # otherwise we assume it's html
                reason, full_html = self._scrape_response(resp.headers, resp.content)
                full_response = unescape_html(full_html)

        msg = "[Reason: %s]" % reason

        if reason is None:
            msg += "\n%s" % full_response

        return msg

    def _scrape_response(self, headers, response):
        """
        Scrape the html response.
        """
        # identify the responding server
        server_type = None
        server_string = headers.get("server", "")

        if server_string and "jetty" in server_string.lower():
            server_type = "jetty"

        if server_string and "coyote" in server_string.lower():
            server_type = "tomcat"

        reason = None
        full_html = ""
        dom_tree = None

        if hasattr(response, "decode"):
            response = response.decode()

        if response.startswith("<?xml"):
            # Try a strict XML parse
            try:
                soup = ElementTree.fromstring(response)

                reason_node = soup.find('lst[@name="error"]/str[@name="msg"]')
                tb_node = soup.find('lst[@name="error"]/str[@name="trace"]')
                if reason_node is not None:
                    full_html = reason = reason_node.text.strip()
                if tb_node is not None:
                    full_html = tb_node.text.strip()
                    if reason is None:
                        reason = full_html

                # Since we had a precise match, we'll return the results now:
                if reason and full_html:
                    return reason, full_html
            except ElementTree.ParseError:
                # XML parsing error, so we'll let the more liberal code handle it.
                pass

        if server_type == "tomcat":
            # Tomcat doesn't produce a valid XML response or consistent HTML:
            m = re.search(r"<(h1)[^>]*>\s*(.+?)\s*</\1>", response, re.IGNORECASE)
            if m:
                reason = m.group(2)
            else:
                full_html = "%s" % response
        else:
            # Let's assume others do produce a valid XML response
            try:
                dom_tree = ElementTree.fromstring(response)
                reason_node = None

                # html page might be different for every server
                if server_type == "jetty":
                    reason_node = dom_tree.find("body/pre")
                else:
                    reason_node = dom_tree.find("head/title")

                if reason_node is not None:
                    reason = reason_node.text

                if reason is None:
                    full_html = ElementTree.tostring(dom_tree)
            except SyntaxError as err:
                LOG.warning(  # NOQA: G200
                    "Unable to extract error message from invalid XML: %s",
                    err,
                    extra={"data": {"response": response}},
                )
                full_html = "%s" % response

        full_html = force_unicode(full_html)
        full_html = full_html.replace("\n", "")
        full_html = full_html.replace("\r", "")
        full_html = full_html.replace("<br/>", "")
        full_html = full_html.replace("<br />", "")
        full_html = full_html.strip()
        return reason, full_html

    # Conversion #############################################################

    def _from_python(self, value):
        """
        Converts python values to a form suitable for insertion into the xml
        we send to solr.
        """
        if hasattr(value, "strftime"):
            if hasattr(value, "hour"):
                offset = value.utcoffset()
                if offset:
                    value = value - offset
                value = value.replace(tzinfo=None).isoformat() + "Z"
            else:
                value = "%sT00:00:00Z" % value.isoformat()
        elif isinstance(value, bool):
            if value:
                value = "true"
            else:
                value = "false"
        else:
            if isinstance(value, bytes):
                value = str(value, errors="replace")  # NOQA: F821

            value = "{0}".format(value)

        return clean_xml_string(value)

    def _to_python(self, value):
        """
        Converts values from Solr to native Python values.
        """
        if isinstance(value, (int, float, complex)):
            return value

        if isinstance(value, (list, tuple)):
            result = [self._to_python(v) for v in value]
            if isinstance(value, tuple):
                result = tuple(result)
            return result

        if value == "true":
            return True
        elif value == "false":
            return False

        is_string = False

        if isinstance(value, bytes):
            value = force_unicode(value)

        if isinstance(value, str):
            is_string = True

        if is_string:
            possible_datetime = DATETIME_REGEX.search(value)

            if possible_datetime:
                date_values = possible_datetime.groupdict()

                for dk, dv in date_values.items():
                    date_values[dk] = int(dv)

                return datetime.datetime(
                    date_values["year"],
                    date_values["month"],
                    date_values["day"],
                    date_values["hour"],
                    date_values["minute"],
                    date_values["second"],
                )

        try:
            # This is slightly gross but it's hard to tell otherwise what the
            # string's original type might have been.
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If it fails, continue on.
            pass

        return value

    def _is_null_value(self, value):
        """
        Check if a given value is ``null``.

        Criteria for this is based on values that shouldn't be included
        in the Solr ``add`` request at all.
        """
        if value is None:
            return True

        if isinstance(value, str) and len(value) == 0:
            return True

        # TODO: This should probably be removed when solved in core Solr level?
        return False

    # API Methods ############################################################

    def search(self, q, search_handler=None, **kwargs):
        """
        Performs a search and returns the results.

        Requires a ``q`` for a string version of the query to run.

        Optionally accepts ``**kwargs`` for additional options to be passed
        through the Solr URL.

        Returns ``self.results_cls`` class object (defaults to
        ``pysolr.Results``)

        Usage::

            # All docs.
            results = solr.search('*:*')

            # Search with highlighting.
            results = solr.search('ponies', **{
                'hl': 'true',
                'hl.fragsize': 10,
            })

        """
        params = {"q": q}
        params.update(kwargs)
        response = self._select(params, handler=search_handler)
        decoded = self.decoder.decode(response)

        self.log.debug(
            "Found '%s' search results.",
            # cover both cases: there is no response key or value is None
            (decoded.get("response", {}) or {}).get("numFound", 0),
        )

        cursorMark = params.get("cursorMark", None)
        if cursorMark != decoded.get("nextCursorMark", cursorMark):

            def next_page_query():
                nextParams = params.copy()
                nextParams["cursorMark"] = decoded["nextCursorMark"]
                return self.search(search_handler=search_handler, **nextParams)

            return self.results_cls(decoded, next_page_query)
        else:
            return self.results_cls(decoded)

    def more_like_this(self, q, mltfl, handler="mlt", **kwargs):
        """
        Finds and returns results similar to the provided query.

        Returns ``self.results_cls`` class object (defaults to
        ``pysolr.Results``)

        Requires Solr 1.3+.

        Usage::

            similar = solr.more_like_this('id:doc_234', 'text')

        """
        params = {"q": q, "mlt.fl": mltfl}
        params.update(kwargs)
        response = self._mlt(params, handler=handler)
        decoded = self.decoder.decode(response)

        self.log.debug(
            "Found '%s' MLT results.",
            # cover both cases: there is no response key or value is None
            (decoded.get("response", {}) or {}).get("numFound", 0),
        )
        return self.results_cls(decoded)

    def suggest_terms(self, fields, prefix, handler="terms", **kwargs):
        """
        Accepts a list of field names and a prefix

        Returns a dictionary keyed on field name containing a list of
        ``(term, count)`` pairs

        Requires Solr 1.4+.
        """
        params = {"terms.fl": fields, "terms.prefix": prefix}
        params.update(kwargs)
        response = self._suggest_terms(params, handler=handler)
        result = self.decoder.decode(response)
        terms = result.get("terms", {})
        res = {}

        # in Solr 1.x the value of terms is list of elements with the field name
        # and a flat list of value, count pairs:
        # ["field_name", ["dance", 23, "dancers", 10, …]]
        #
        # in Solr 3+ the value of terms is a dict of field name and a flat list of
        # value, count pairs: {"field_name": ["dance", 23, "dancers", 10, …]}
        if isinstance(terms, (list, tuple)):
            terms = dict(zip(terms[0::2], terms[1::2]))

        for field, values in terms.items():
            tmp = []

            while values:
                tmp.append((values.pop(0), values.pop(0)))

            res[field] = tmp

        self.log.debug(
            "Found '%d' Term suggestions results.", sum(len(j) for i, j in res.items())
        )
        return res

    def _build_docs(self, docs, boost=None, fieldUpdates=None):
        # if no boost needed use json multidocument api
        #   The JSON API skips the XML conversion and speedup load from 15 to 20 times.
        #   CPU Usage is drastically lower.
        if boost is None:
            solrapi = "JSON"
            message = docs
            # single doc convert to array of docs
            if isinstance(message, dict):
                # convert dict to list
                message = [message]
                # json array of docs
            if isinstance(message, list):
                # convert to string
                cleaned_message = [
                    self._build_json_doc(doc, fieldUpdates=fieldUpdates)
                    for doc in message
                ]
                m = self.encoder.encode(cleaned_message).encode("utf-8")
            else:
                raise ValueError("wrong message type")
        else:
            solrapi = "XML"
            message = ElementTree.Element("add")

            for doc in docs:
                el = self._build_xml_doc(doc, boost=boost, fieldUpdates=fieldUpdates)
                message.append(el)

            # This returns a bytestring. Ugh.
            m = ElementTree.tostring(message, encoding="utf-8")
            # Convert back to Unicode please.
            m = force_unicode(m)

        return (solrapi, m, len(message))

    def _build_json_doc(self, doc, fieldUpdates=None):
        if fieldUpdates is None:
            cleaned_doc = {k: v for k, v in doc.items() if not self._is_null_value(v)}
        else:
            # id must be added without a modifier
            # if using field updates, all other fields should have a modifier
            cleaned_doc = {
                k: {fieldUpdates[k]: v} if k in fieldUpdates else v
                for k, v in doc.items()
            }

        return cleaned_doc

    def _build_xml_doc(self, doc, boost=None, fieldUpdates=None):
        doc_elem = ElementTree.Element("doc")

        for key, value in doc.items():
            if key == NESTED_DOC_KEY:
                for child in value:
                    doc_elem.append(self._build_xml_doc(child, boost, fieldUpdates))
                continue

            if key == "boost":
                doc_elem.set("boost", force_unicode(value))
                continue

            # To avoid multiple code-paths we'd like to treat all of our values
            # as iterables:
            if isinstance(value, (list, tuple, set)):
                values = value
            else:
                values = (value,)

            use_field_updates = fieldUpdates and key in fieldUpdates
            if use_field_updates and not values:
                values = ("",)
            for bit in values:
                attrs = {"name": key}

                if self._is_null_value(bit):
                    if use_field_updates:
                        bit = ""
                        attrs["null"] = "true"
                    else:
                        continue

                if key == "_doc":
                    child = self._build_xml_doc(bit, boost)
                    doc_elem.append(child)
                    continue

                if use_field_updates:
                    attrs["update"] = fieldUpdates[key]

                if boost and key in boost:
                    attrs["boost"] = force_unicode(boost[key])

                field = ElementTree.Element("field", **attrs)
                field.text = self._from_python(bit)

                doc_elem.append(field)

        return doc_elem

    def add(
        self,
        docs,
        boost=None,
        fieldUpdates=None,
        commit=None,
        softCommit=False,
        commitWithin=None,
        waitFlush=None,
        waitSearcher=None,
        overwrite=None,
        handler="update",
        min_rf=None,
    ):
        """
        Adds or updates documents.

        Requires ``docs``, which is a list of dictionaries. Each key is the
        field name and each value is the value to index.

        Optionally accepts ``commit``. Default is ``None``. None signals to use default

        Optionally accepts ``softCommit``. Default is ``False``.

        Optionally accepts ``boost``. Default is ``None``.

        Optionally accepts ``fieldUpdates``. Default is ``None``.

        Optionally accepts ``commitWithin``. Default is ``None``.

        Optionally accepts ``waitFlush``. Default is ``None``.

        Optionally accepts ``waitSearcher``. Default is ``None``.

        Optionally accepts ``overwrite``. Default is ``None``.

        Optionally accepts ``min_rf``. Default is ``None``.

        Usage::

            solr.add([
                {
                    "id": "doc_1",
                    "title": "A test document",
                },
                {
                    "id": "doc_2",
                    "title": "The Banana: Tasty or Dangerous?",
                },
            ])
        """
        start_time = time.time()
        self.log.debug("Starting to build add request...")
        solrapi, m, len_message = self._build_docs(
            docs,
            boost,
            fieldUpdates,
        )
        end_time = time.time()
        self.log.debug(
            "Built add request of %s docs in %0.2f seconds.",
            len_message,
            end_time - start_time,
        )
        return self._update(
            m,
            commit=commit,
            softCommit=softCommit,
            commitWithin=commitWithin,
            waitFlush=waitFlush,
            waitSearcher=waitSearcher,
            overwrite=overwrite,
            handler=handler,
            solrapi=solrapi,
            min_rf=min_rf,
        )

    def delete(
        self,
        id=None,  # NOQA: A002
        q=None,
        commit=None,
        softCommit=False,
        waitFlush=None,
        waitSearcher=None,
        handler="update",
    ):  # NOQA: A002
        """
        Deletes documents.

        Requires *either* ``id`` or ``query``. ``id`` is if you know the
        specific document id to remove. Note that ``id`` can also be a list of
        document ids to be deleted. ``query`` is a Lucene-style query
        indicating a collection of documents to delete.

        Optionally accepts ``commit``. Default is ``True``.

        Optionally accepts ``softCommit``. Default is ``False``.

        Optionally accepts ``waitFlush``. Default is ``None``.

        Optionally accepts ``waitSearcher``. Default is ``None``.

        Usage::

            solr.delete(id='doc_12')
            solr.delete(id=['doc_1', 'doc_3'])
            solr.delete(q='*:*')

        """
        if id is None and q is None:
            raise ValueError('You must specify "id" or "q".')
        elif id is not None and q is not None:
            raise ValueError('You many only specify "id" OR "q", not both.')
        elif id is not None:
            if not isinstance(id, (list, set, tuple)):
                doc_id = [id]
            else:
                doc_id = list(filter(None, id))
            if doc_id:
                et = ElementTree.Element("delete")
                for one_doc_id in doc_id:
                    subelem = ElementTree.SubElement(et, "id")
                    subelem.text = one_doc_id
                m = ElementTree.tostring(et)
            else:
                raise ValueError("The list of documents to delete was empty.")
        elif q is not None:
            et = ElementTree.Element("delete")
            subelem = ElementTree.SubElement(et, "query")
            subelem.text = q
            m = ElementTree.tostring(et)

        return self._update(
            m,
            commit=commit,
            softCommit=softCommit,
            waitFlush=waitFlush,
            waitSearcher=waitSearcher,
            handler=handler,
        )

    def commit(
        self,
        softCommit=False,
        waitFlush=None,
        waitSearcher=None,
        expungeDeletes=None,
        handler="update",
    ):
        """
        Forces Solr to write the index data to disk.

        Optionally accepts ``expungeDeletes``. Default is ``None``.

        Optionally accepts ``waitFlush``. Default is ``None``.

        Optionally accepts ``waitSearcher``. Default is ``None``.

        Optionally accepts ``softCommit``. Default is ``False``.

        Usage::

            solr.commit()

        """
        if expungeDeletes is not None:
            msg = '<commit expungeDeletes="%s" />' % str(bool(expungeDeletes)).lower()
        else:
            msg = "<commit />"

        return self._update(
            msg,
            commit=not softCommit,
            softCommit=softCommit,
            waitFlush=waitFlush,
            waitSearcher=waitSearcher,
            handler=handler,
        )

    def optimize(
        self,
        commit=True,
        waitFlush=None,
        waitSearcher=None,
        maxSegments=None,
        handler="update",
    ):
        """
        Tells Solr to streamline the number of segments used, essentially a
        defragmentation operation.

        Optionally accepts ``maxSegments``. Default is ``None``.

        Optionally accepts ``waitFlush``. Default is ``None``.

        Optionally accepts ``waitSearcher``. Default is ``None``.

        Usage::

            solr.optimize()

        """
        if maxSegments:
            msg = '<optimize maxSegments="%d" />' % maxSegments
        else:
            msg = "<optimize />"

        return self._update(
            msg,
            commit=commit,
            waitFlush=waitFlush,
            waitSearcher=waitSearcher,
            handler=handler,
        )

    def extract(self, file_obj, extractOnly=True, handler="update/extract", **kwargs):
        """
        POSTs a file to the Solr ExtractingRequestHandler so rich content can
        be processed using Apache Tika. See the Solr wiki for details:

            http://wiki.apache.org/solr/ExtractingRequestHandler

        The ExtractingRequestHandler has a very simple model: it extracts
        contents and metadata from the uploaded file and inserts it directly
        into the index. This is rarely useful as it allows no way to store
        additional data or otherwise customize the record. Instead, by default
        we'll use the extract-only mode to extract the data without indexing it
        so the caller has the opportunity to process it as appropriate; call
        with ``extractOnly=False`` if you want to insert with no additional
        processing.

        Returns None if metadata cannot be extracted; otherwise returns a
        dictionary containing at least two keys:

            :contents:
                        Extracted full-text content, if applicable
            :metadata:
                        key:value pairs of text strings
        """
        if not hasattr(file_obj, "name"):
            raise ValueError(
                "extract() requires file-like objects which have a defined name"
            )

        params = {
            "extractOnly": "true" if extractOnly else "false",
            "lowernames": "true",
            "wt": "json",
        }
        params.update(kwargs)
        filename = quote(file_obj.name.encode("utf-8"))
        try:
            # We'll provide the file using its true name as Tika may use that
            # as a file type hint:
            resp = self._send_request(
                "post", handler, body=params, files={"file": (filename, file_obj)}
            )
        except (IOError, SolrError):
            self.log.exception("Failed to extract document metadata")
            raise

        try:
            data = self.decoder.decode(resp)
        except ValueError:
            self.log.exception("Failed to load JSON response")
            raise

        data["contents"] = data.pop(filename, None)
        data["metadata"] = metadata = {}

        raw_metadata = data.pop("%s_metadata" % filename, None)

        if raw_metadata:
            # The raw format is somewhat annoying: it's a flat list of
            # alternating keys and value lists
            while raw_metadata:
                metadata[raw_metadata.pop()] = raw_metadata.pop()

        return data

    def ping(self, handler="admin/ping", **kwargs):
        """
        Sends a ping request.

        Usage::

            solr.ping()

        """
        params = kwargs
        params_encoded = safe_urlencode(params, True)

        if len(params_encoded) < 1024:
            # Typical case.
            path = "%s/?%s" % (handler, params_encoded)
            return self._send_request("get", path)
        else:
            # Handles very long queries by submitting as a POST.
            path = "%s/" % handler
            headers = {
                "Content-type": "application/x-www-form-urlencoded; charset=utf-8"
            }
            return self._send_request(
                "post", path, body=params_encoded, headers=headers
            )


class SolrCoreAdmin(object):
    """
    Handles core admin operations: see http://wiki.apache.org/solr/CoreAdmin

    This must be initialized with the full admin cores URL::

        solr_admin = SolrCoreAdmin('http://localhost:8983/solr/admin/cores')
        status = solr_admin.status()

    Operations offered by Solr are:
       1. STATUS
       2. CREATE
       3. RELOAD
       4. RENAME
       5. ALIAS
       6. SWAP
       7. UNLOAD
       8. LOAD (not currently implemented)
    """

    def __init__(self, url, *args, **kwargs):
        super(SolrCoreAdmin, self).__init__(*args, **kwargs)
        self.url = url

    def _get_url(self, url, params=None, headers=None):
        if params is None:
            params = {}
        if headers is None:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.get(url, data=safe_urlencode(params), headers=headers)
        return force_unicode(resp.content)

    def status(self, core=None):
        """
        Get core status information

        See https://wiki.apache.org/solr/CoreAdmin#STATUS
        """
        params = {"action": "STATUS"}

        if core is not None:
            params.update(core=core)

        return self._get_url(self.url, params=params)

    def create(
        self, name, instance_dir=None, config="solrconfig.xml", schema="schema.xml"
    ):
        """
        Create a new core

        See https://wiki.apache.org/solr/CoreAdmin#CREATE
        """
        params = {"action": "CREATE", "name": name, "config": config, "schema": schema}

        if instance_dir is None:
            params.update(instanceDir=name)
        else:
            params.update(instanceDir=instance_dir)

        return self._get_url(self.url, params=params)

    def reload(self, core):  # NOQA: A003
        """
        Reload a core

        See https://wiki.apache.org/solr/CoreAdmin#RELOAD
        """
        params = {"action": "RELOAD", "core": core}
        return self._get_url(self.url, params=params)

    def rename(self, core, other):
        """
        Rename a core

        See http://wiki.apache.org/solr/CoreAdmin#RENAME
        """
        params = {"action": "RENAME", "core": core, "other": other}
        return self._get_url(self.url, params=params)

    def swap(self, core, other):
        """
        Swap a core

        See http://wiki.apache.org/solr/CoreAdmin#SWAP
        """
        params = {"action": "SWAP", "core": core, "other": other}
        return self._get_url(self.url, params=params)

    def unload(self, core):
        """
        Unload a core

        See http://wiki.apache.org/solr/CoreAdmin#UNLOAD
        """
        params = {"action": "UNLOAD", "core": core}
        return self._get_url(self.url, params=params)

    def load(self, core):
        raise NotImplementedError("Solr 1.4 and below do not support this operation.")


# Using two-tuples to preserve order.
REPLACEMENTS = (
    # Nuke nasty control characters.
    (b"\x00", b""),  # Start of heading
    (b"\x01", b""),  # Start of heading
    (b"\x02", b""),  # Start of text
    (b"\x03", b""),  # End of text
    (b"\x04", b""),  # End of transmission
    (b"\x05", b""),  # Enquiry
    (b"\x06", b""),  # Acknowledge
    (b"\x07", b""),  # Ring terminal bell
    (b"\x08", b""),  # Backspace
    (b"\x0b", b""),  # Vertical tab
    (b"\x0c", b""),  # Form feed
    (b"\x0e", b""),  # Shift out
    (b"\x0f", b""),  # Shift in
    (b"\x10", b""),  # Data link escape
    (b"\x11", b""),  # Device control 1
    (b"\x12", b""),  # Device control 2
    (b"\x13", b""),  # Device control 3
    (b"\x14", b""),  # Device control 4
    (b"\x15", b""),  # Negative acknowledge
    (b"\x16", b""),  # Synchronous idle
    (b"\x17", b""),  # End of transmission block
    (b"\x18", b""),  # Cancel
    (b"\x19", b""),  # End of medium
    (b"\x1a", b""),  # Substitute character
    (b"\x1b", b""),  # Escape
    (b"\x1c", b""),  # File separator
    (b"\x1d", b""),  # Group separator
    (b"\x1e", b""),  # Record separator
    (b"\x1f", b""),  # Unit separator
)


def sanitize(data):
    fixed_string = force_bytes(data)

    for bad, good in REPLACEMENTS:
        fixed_string = fixed_string.replace(bad, good)

    return force_unicode(fixed_string)


class SolrCloud(Solr):
    def __init__(
        self,
        zookeeper,
        collection,
        decoder=None,
        encoder=None,
        timeout=60,
        retry_count=5,
        retry_timeout=0.2,
        auth=None,
        verify=True,
        *args,
        **kwargs,
    ):
        url = zookeeper.getRandomURL(collection)
        self.auth = auth
        self.collection = collection
        self.retry_count = retry_count
        self.retry_timeout = retry_timeout
        self.verify = verify
        self.zookeeper = zookeeper

        super(SolrCloud, self).__init__(
            url,
            decoder=decoder,
            encoder=encoder,
            timeout=timeout,
            auth=self.auth,
            verify=self.verify,
            *args,
            **kwargs,
        )

    def _send_request(self, method, path="", body=None, headers=None, files=None):
        for retry_number in range(self.retry_count):
            try:
                self.url = self.zookeeper.getRandomURL(self.collection)
                return Solr._send_request(self, method, path, body, headers, files)
            except (SolrError, requests.exceptions.RequestException):
                LOG.exception(
                    "%s %s failed on retry %s, will retry after %0.1fs",
                    method,
                    self.url,
                    retry_number,
                    self.retry_timeout,
                )
                time.sleep(self.retry_timeout)

        raise SolrError(
            "Request %s %s failed after %d attempts" % (method, path, self.retry_count)
        )

    def _update(self, *args, **kwargs):
        self.url = self.zookeeper.getLeaderURL(self.collection)
        LOG.debug("Using leader URL: %s", self.url)
        return Solr._update(self, *args, **kwargs)


class ZooKeeper(object):
    # Constants used by the REST API:
    LIVE_NODES_ZKNODE = "/live_nodes"
    ALIASES = "/aliases.json"
    CLUSTER_STATE = "/clusterstate.json"
    COLLECTION_STATUS = "/collections"
    COLLECTION_STATE = "/collections/%s/state.json"
    SHARDS = "shards"
    REPLICAS = "replicas"
    STATE = "state"
    ACTIVE = "active"
    LEADER = "leader"
    BASE_URL = "base_url"
    TRUE = "true"
    FALSE = "false"
    COLLECTION = "collection"

    def __init__(self, zkServerAddress, timeout=15, max_retries=-1, kazoo_client=None):
        if KazooClient is None:
            logging.error("ZooKeeper requires the `kazoo` library to be installed")
            raise RuntimeError

        self.collections = {}
        self.liveNodes = {}
        self.aliases = {}
        self.state = None

        if kazoo_client is None:
            self.zk = KazooClient(
                zkServerAddress,
                read_only=True,
                timeout=timeout,
                command_retry={"max_tries": max_retries},
                connection_retry={"max_tries": max_retries},
            )
        else:
            self.zk = kazoo_client

        self.zk.start()

        def connectionListener(state):
            if state == KazooState.LOST:
                self.state = state
            elif state == KazooState.SUSPENDED:
                self.state = state

        self.zk.add_listener(connectionListener)

        @self.zk.DataWatch(ZooKeeper.CLUSTER_STATE)
        def watchClusterState(data, *args, **kwargs):
            if not data:
                LOG.warning("No cluster state available: no collections defined?")
            else:
                self.collections = json.loads(data.decode("utf-8"))
                LOG.info("Updated collections: %s", self.collections)

        @self.zk.ChildrenWatch(ZooKeeper.LIVE_NODES_ZKNODE)
        def watchLiveNodes(children):
            self.liveNodes = children
            LOG.info("Updated live nodes: %s", children)

        @self.zk.DataWatch(ZooKeeper.ALIASES)
        def watchAliases(data, stat):
            if data:
                json_data = json.loads(data.decode("utf-8"))
                if ZooKeeper.COLLECTION in json_data:
                    self.aliases = json_data[ZooKeeper.COLLECTION]
                else:
                    LOG.warning(
                        "Expected to find %s in alias update %s",
                        ZooKeeper.COLLECTION,
                        json_data.keys(),
                    )
            else:
                self.aliases = None
            LOG.info("Updated aliases: %s", self.aliases)

        def watchCollectionState(data, *args, **kwargs):
            if not data:
                LOG.warning("No cluster state available: no collections defined?")
            else:
                self.collections.update(json.loads(data.decode("utf-8")))
                LOG.info("Updated collections: %s", self.collections)

        @self.zk.ChildrenWatch(ZooKeeper.COLLECTION_STATUS)
        def watchCollectionStatus(children):
            LOG.info("Updated collection: %s", children)
            for c in children:
                self.zk.DataWatch(self.COLLECTION_STATE % c, watchCollectionState)

    def getHosts(self, collname, only_leader=False, seen_aliases=None):
        if self.aliases and collname in self.aliases:
            return self.getAliasHosts(collname, only_leader, seen_aliases)

        hosts = []
        if collname not in self.collections:
            raise SolrError("Unknown collection: %s" % collname)
        collection = self.collections[collname]
        shards = collection[ZooKeeper.SHARDS]
        for shardname in shards.keys():
            shard = shards[shardname]
            if shard[ZooKeeper.STATE] == ZooKeeper.ACTIVE:
                replicas = shard[ZooKeeper.REPLICAS]
                for replicaname in replicas.keys():
                    replica = replicas[replicaname]

                    if replica[ZooKeeper.STATE] == ZooKeeper.ACTIVE:
                        if not only_leader or (
                            replica.get(ZooKeeper.LEADER, None) == ZooKeeper.TRUE
                        ):
                            base_url = replica[ZooKeeper.BASE_URL]
                            if base_url not in hosts:
                                hosts.append(base_url)
        return hosts

    def getAliasHosts(self, collname, only_leader, seen_aliases):
        if seen_aliases:
            if collname in seen_aliases:
                LOG.warning("%s in circular alias definition - ignored", collname)
                return []
        else:
            seen_aliases = []
        seen_aliases.append(collname)
        collections = self.aliases[collname].split(",")
        hosts = []
        for collection in collections:
            for host in self.getHosts(collection, only_leader, seen_aliases):
                if host not in hosts:
                    hosts.append(host)
        return hosts

    def getRandomURL(self, collname, only_leader=False):
        hosts = self.getHosts(collname, only_leader=only_leader)
        if not hosts:
            raise SolrError("ZooKeeper returned no active shards!")
        return "%s/%s" % (random.choice(hosts), collname)  # NOQA: S311

    def getLeaderURL(self, collname):
        return self.getRandomURL(collname, only_leader=True)

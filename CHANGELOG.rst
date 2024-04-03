Changelog
=========

%%version%% (unreleased)
------------------------

New
~~~

- Support for nested documents (closes #170) [Chris Adams]

  This adds support for Solr's nested documents in `Solr.add`

  Thanks to @skirsdeda for the patch

- ZooKeeper can receive an existing KazooClient instance. [Chris Adams]

  This simplifies advanced customization by allowing you to pass in an existing instance which is configured in whatever manner necessary.

Changes
~~~~~~~

- Logging: pass full request body + headers as extra data. [Chris Adams]

  This doesn't affect the normal logging output but is helpful for
  aggregation systems such as Sentry where the full request information
  may be displayed for debugging purposes

- Basic max_retries for ZooKeeper. [Chris Adams]

  Kazoo sets the default to hang forever which is frequently not the desired error-handling behavior. This makes it easier to set a limit on the number of retries and we use it in testing to avoid the suite hanging endlessly.

- Better error message for Solr failures. [Chris Adams]

  Previously when ZooKeeper had no active shards pysolr
  would return an error when `random.shuffle` received
  an empty list. Now it will raise an exception which
  will hopefully indicate just how bad the situation is.

- Remove __del__ methods. [Chris Adams]

  The __del__ methods were added in an attempt to avoid Kazoo-related
  failures as part of the SolrCloud support but can cause other problems
  on different versions of Python (see #193).

  Since the errors in question were observed during testing this commit
  removes the __del__ methods and we will have to find an alternative for
  making tests fail safely.

- Custom Commit Policy .  [Evan Fagerberg]

  Previously a ``Solr`` object assumed that an operation should commit by default.
  It is generally good practice to limit the amount of commits to solr.
  Excessive commits risk opening too many searcher or using too many system resources.
  Therefore the commit policy is configurable via the ``always_commit`` attribute of
  the ``Solr`` object.

  Most solr configurations should already have an interval that defines how long to wait
  before doing a commit to solr anyway. (Measured either in time or number of documents)

  IMPORTANT: If you are upgrading to this version and need to keep committing by default,
  change the Solr objects to have ``always_commit=True``.

- `pysolr.version_info` and `pysolr.pkg_distribution` have been removed. [Craig de Stigter]

- Added dependency on `importlib_metadata` for Python < 3.8 [Craig de Stigter]

Fix
~~~

- Set KazooClient timeout. [Chris Adams]

  `__init__` was not actually passing this to the ZooKeeper client

Other
~~~~~

- Better docstring for SolrCoreAdmin. [Chris Adams]

  Thanks to Patricio Del Boca (@pdelboca) for the patch.

  Closes #185

- Require requests >= 2.9.1 (closes #177) [Chris Adams]

  This will avoid compatibility issues on Python 3 which can produce
  confusing errors.

- Merge pull request #203 from bendemott/documentation. [Chris Adams]

  updated typo in documentation example

- Updated typo in documentation example. [Ben DeMott]

  "Zookeeper" should be "ZooKeeper" on line 104 in README.rst

- Docs: note that add has commit=True by default (see #46) [Chris Adams]

  Thanks to @mlissner

- Adds note about commit=True being the default. [Mike Lissner]

- Correctly handle time-zone aware dates (#201) [Andrew Kuchling]

  Thanks to Andrew Kuchling (@akuchling) for the patch.

  Closes #197, #198

- Oops.. Add a missing assert in tests. [Tadas Dailyda]

- Refactor _build_doc to be recursive and allow deeper document nesting,
  fix tests accordingly. [Tadas Dailyda]

- Add some block join queries to test_search. [Tadas Dailyda]

- Add some nested docs to the tests. [Tadas Dailyda]

- Implement nested documents functionality. [Tadas Dailyda]

- ZooKeeper: by default use the same timeout for commands and
  connections. [Chris Adams]

- Tox: run SolrCloud tests (parity with Travis CI) [Chris Adams]

- Update project URL. [Chris Adams]

- Fixed DeprecationWarning from `pkg_resources` on Python 3.10+ [Craig de Stigter]

  Closes #464

v3.5.0 (2016-05-24)
-------------------

New
~~~

- Expose the full Solr response in `Results` [Chris Adams]

  This makes life easier for anyone using custom extensions by
  removing the need to create a `Results` subclass just to get
  access to an extra dictionary key.

- More flexible control of request handlers. [nuarhu]

  This allows configuring the default search handler and overriding it for every query method

  Thanks to @nuarhu for the patch

- Start maintaining a changelog from gitchangelog. [Chris Adams]

- Overwrite flag for Solr.add (closes #182) [Chris Adams]

  Thanks to @robinsonkwame for the patch

- SolrCloud support (see #138) [Chris Adams]

  This optionally adds support for SolrCloud using the Kazoo client
  library.

  Thanks to @upayavira

Other
~~~~~

- V3.5.0. [Chris Adams]

- Merge pull request #192 from dhruvpathak/optimize_commit_flag. [Chris
  Adams]

  chg: `optimize()` also accepts `commit` flag

- Included commit flag in optimize() to let optimize call run with or
  without commit. [dhruv.pathak]

- Merge pull request #188 from TigorC/master. [Chris Adams]

  Removed py26 from tox.ini

- Removed py26 from tox.ini. [Igor Tokarev]

- Tests: avoid timeout-based CI failures. [Chris Adams]

  These caused sporadic CI build failures and weren’t
  otherwise testing actual functionality since we don’t have a
  test which does something like SIGSTOP the test Solr server
  long enough to confirm a timeout.

  We’ll confirm that the timeout is passed through but
  otherwise use the defaults.

- Update Travis CI badge in the README. [Chris Adams]

- Merge pull request #184 from atuljangra/master. [Chris Adams]

  Correct documentation for `_update`

  Thanks to @atuljangra for the patch!

- Merge branch 'master' of https://github.com/atuljangra/pysolr.
  [atuljangra]

- Misleading comments. [atuljangra]

- Travis: use build matrix for regular and SolrCloud tests. [Chris
  Adams]

- Test_cloud: remove dead code. [Chris Adams]

  The first instance of test_custom_results_class was broken because it
  used the wrong port but this wasn’t failing because the same method name
  was redefined further down in the file and that used the updated port
  config.

- PEP-8. [Chris Adams]

- ZooKeeper: log unexpected format changes to watched aliases. [Chris
  Adams]

- ZooKeeper: restore JSON blob decoding. [Chris Adams]

- PEP-8. [Chris Adams]

- PEP-8 unused imports. [Chris Adams]

- PEP-8. [Chris Adams]

- PEP-8. [Chris Adams]

- PEP-8. [Chris Adams]

- Setup.cfg: add pep8 and isort config. [Chris Adams]

- Tear down requests.Session instance at close. [Chris Adams]

  This avoids log-spew on modern unittest implementations
  which report unclosed file handles at the end of a run.

- Remove Python 2.6 from Travis test matrix. [Chris Adams]

- Add __future__ absolute_import. [Chris Adams]

  This is currently moot but avoids any chance of regression
  between Python 2.x and 3.x.

- PEP-8. [Chris Adams]

- Drop support for Python 2.6. [Chris Adams]

  We have some old import dances and other overhead for Python
  2.6 support, which the CPython developers dropped support
  for in 2013:

  http://www.curiousefficiency.org/posts/2015/04/stop-supporting-python26.html

- Allow queries to be directed to different search handlers. [Chris
  Adams]

  The `search` method now allows you override the default `select` handler
  when your Solr instance has multiple search handlers.

  Thanks to @k-patel for the patch.

  Closes #174
  Closes #175

v3.4.0 (2016-02-02)
-------------------

- Update version numbers for v3.4.0. [Chris Adams]

- Logging: better message for HTTP status != 200. [Chris Adams]

  We already extract error message from Solr responses and that is
  great. Unfortunately it can contain the data that may change with
  every request (like document id).

  This creates an issue when user uses Sentry or other solution
  that captures logging or exceptions. Previous implementation
  causes many duplicated events in Sentry if message extracted
  using `self._extract_error(resp)` contained such variable data.

  This change uses 'non-mutable' message that is complemented
  with extracted data that using string formatting option supplied
  by Python logging. Thanks to this, Sentry and other solutions
  can perform better grouping of logging messages (by status code).

  This is approach that is already used in handling other errors.

- Fix response error handling on Python 3 (closes #162) [Chris Adams]

  Previously the error handling did not work correctly on Python 3 because
  a byte-string response wasn't decoded before processing.

  Thanks to Emmanuel Leblond (@touilleMan) for the patch.

- Merge pull request #167 from swistakm/master. [Chris Adams]

  Refactor common response processing to Results class

- Move response manipulation responsibility to Results class and allow
  custom results classes. [mjaworski]

- Add Python 3.5 to automated test matrix. [Chris Adams]

v3.3.3 (2015-10-24)
-------------------

- V3.3.3. [Chris Adams]

- Fix response error handling on Python 3 (closes #162) [Chris Adams]

  Previously the error handling did not work correctly on Python 3 because
  a byte-string response wasn't decoded before processing.

  Thanks to Emmanuel Leblond (@touilleMan) for the patch.

- Tests: upgrade Solr to 4.10.4. [Chris Adams]

  * Resync test Solar script with django-haystack
    These are still not quite the same; at some point it would be nice to
    look into a common tool which both projects could use
  * Update Solr configuration script to set correct libpath for solr-cell
    to avoid lazy-load failures during testing as was reported on e.g. #162

- Tests: update Solr download script for recent API change. [Chris
  Adams]

- Merge pull request #142 from yspanchal/master. [Chris Adams]

  Add support for cursormark pagination

- Added cursormark deep pagination support. [Yogesh Panchal]

v3.3.2 (2015-05-26)
-------------------

- Version 3.3.2. [Chris Adams]

- Python 2.6 backwards compatibility. [Chris Adams]

  Python 2.6 shipped with ElementTree 1.2.x. Among other differences, it
  lacks support for the attribute selectors used to process valid XML
  error messages, which was added in ElementTree 1.3.

- Merge pull request #155 from domenkozar/solr4/exceptions. [Chris
  Adams]

  Support Solr 4 XML error format parsing

  Thanks @domenkozar for the patch

- Overhaul Travis config. [Chris Adams]

  * Sidestep use of Tox in favor of Travis-managed Python versions
  * Enable container-based builds
  * Enable caching for Solr server downloads

- Use builtin unittest2 runner on Python 2.7 as well. [Chris Adams]

- Simple error extraction. [Chris Adams]

  Previously pysolr depended on lxml and cssselect to extract
  text from Tomcat’s error messages, which was unreliable.

  This change uses regular expressions to deal with invalid
  XML rather than lxml’s salvaging parser and avoids having
  to maintain the code which attempted to find the main error
  message in tag soup

  Closes #149

- Update test Solr download script to work with default Python 3. [Chris
  Adams]

v3.3.1 (2015-05-12)
-------------------

- Version 3.3.1. [Chris Adams]

- Prepare for 3.3.1 release. [Chris Adams]

- Convert all HTTP client errors to SolrError. [Chris Adams]

  This commit ensures that an outside caller can handle all HTTP-related errors by catching SolrError without knowing whether the exception class is owned by requests, urllib3, or httplib.

- Merge pull request #146 from gryphius/fix_doc_typo. [Chris Adams]

  Fix typo in ExtractingRequestHandler documentation

  Thanks @gryphius

- Doc fix: a very simply model -> a very simple model. [Oli]

- Merge pull request #139 from upayavira/feature/no-optimize. [Daniel
  Lindsley]

  Optimize is no longer recommended

- Optimize is no longer recommended. [Upayavira]

  Since Solr 3.6, Solr has used the TieredMergePolicy which makes,
  in most scenarios, optimization a harmful rather than beneficial
  step.

v3.3.0 (2015-02-03)
-------------------

- Bumped to v3.3.0! [Daniel Lindsley]

- Added @acdha to primaries for all his hard work. [Daniel Lindsley]

- Support Solr 4+ individual field updates (closes #129) [Chris Adams]

  Now fields can be updated individually:

       conn.add(docs, fieldUpdates={'myfield1_ss': 'add',
                                    'myfield2_s': 'set',
                                    'myfield3_i': 'inc'})

  Thanks to Çağatay Çallı (@faraday) for the patch.

- Merge pull request #137 from LuRsT/patch-1. [Chris Adams]

  Fixed syntax error in README.rst example (thanks @LuRsT)

- Fixed syntax error in README.rst example. [Gil Gonçalves]

- Add softCommit support (closes #98) [Chris Adams]

  add() and commit() may now be called with softCommit=True

  Thanks to @sicarrots for the patch

- Merge pull request #123 from ulivedit/master. [Chris Adams]

  Python 3 compatibility for error message extraction (thanks @ulivedit)

- Fix python 3.4 error with forcing unicode strings. [Eric Hagman]

- Merge pull request #135 from Grokzen/master. [Chris Adams]

  Use DEBUG_PYSOLR environmental variable to configure logging

  This offers an alternative to editing pysolr.py or reconfiguring logging elsewhere

- Make it easier to debug pysolr via environment variable. [Johan
  Andersson]

- Merge pull request #131 from andreif/highlighted-readme. [Chris Adams]

  Highlight Python code in README.rst (thanks @andreif)

- Highlight Python code in README.rst. [Andrei Fokau]

- Add support for error responses in JSON format (closes #113) [Chris
  Adams]

  Thanks to @andreif for the patch and tests

- Merge pull request #125 from phill-tornroth/patch-1. [Chris Adams]

  Fix get-solr-download-url.py for Python 2.6

- Fixes 'zero field length' error from `format()` [Phill Tornroth]

  Unless I'm missing something... :)

- Travis: download Solr before starting tests. [Chris Adams]

  This should avoid download errors being presented as test failures

- Tests: increase Solr startup timeout. [Chris Adams]

- Add test Solr tarball downloads to .gitignore. [Chris Adams]

- Tests: add Python 3.4 targets. [Chris Adams]

- Tests: use Solr 4.7.2 from nearest mirror (closes #115) [Chris Adams]

- Tests: add a script to retrieve the closest Apache mirror. [Chris
  Adams]

  See #115

- Merge pull request #111 from redjack/py26-tests. [Chris Adams]

  Update 'run-tests.py' to invoke unittest2 correctly on Python 2.6

- Update 'run-tests.py' to invoke unittest2 correctly on Python 2.6.
  [Andy Freeland]

- Expanded testing section of the README. [Chris Adams]

- Merge pull request #36 from glenbot/master. [Chris Adams]

  Update to SolrCoreAdmin.create to use correct action

- Updated create command in SolrCoreAdmin to use correct action.
  [glenbot]

- Fix type in SolrAdmin.create default parameter. [Chris Adams]

  See #36

- Updated ignores. [Daniel Lindsley]

v3.2.0 (2014-01-27)
-------------------

- Bumped to v3.2.0! [Daniel Lindsley]

- Merge pull request #104 from tongwang/master. [Chris Adams]

  Fix content extraction (thanks @tongwang)

- Remove unnecessary comment. [Tong Wang]

- Fixed both issues https://github.com/toastdriven/pysolr/issues/96 and
  https://github.com/toastdriven/pysolr/issues/90 and updated test solr
  sever from 4.1.0 to 4.6.0. All tests pass. [Tong Wang]

- Tests: set Tox basepython versions for tomcat tests. [Chris Adams]

- Tests: update test_full_url for multi-core config. [Chris Adams]

- Tests: expect content extraction to fail. [Chris Adams]

  Once https://github.com/toastdriven/pysolr/issues/90 is fixed we can
  re-enable this test

- Skip tomcat error tests when lxml is unavailable. [Chris Adams]

  Until _scrap_response has a Tomcat path which doesn't depend on
  lxml.html there's no point in running these tests on a different config

- Enable Travis CI. [Chris Adams]

- Use tox for testing multiple versions. [Chris Adams]

  * Add a simple test-runner which handles starting and stopping Solr
  * Added a basic tox.ini for Python 2.6, 2.7 and 3.3 with and without
    Tomcat to keep us honest about extra_requires…

- Move test setup to script & update README. [Chris Adams]

  This avoids the README drifting out of sync

- Bump requests dependency to 2.x for Unicode handling. [Chris Adams]

- Update testing instructions in the README after the Solr mirror went
  away. [Chris Adams]

  This uses the canonical Apache archive which should be more stable than the mirror we were using

- Merge remote-tracking branch 'anti-social/clean_xml' [Daniel Lindsley]

- Fixed error when invalid xml chars present in document. [Alexander
  Koval]

- Merge remote-tracking branch 'anti-social/absolute_import' [Daniel
  Lindsley]

- Added absolute_import. [Alexander Koval]

- Ignored env3. [Daniel Lindsley]

v3.1.0 (2013-07-17)
-------------------

- Bumped to v3.1.0! [Daniel Lindsley]

- Better Unicode behavior under Python 3. [Daniel Lindsley]

- Merge pull request #69 from zyegfryed/patch-1. [Daniel Lindsley]

  Added MoreLikeThis handler to solrconfig.xml test cores.

- Added MoreLikeThis handler to solrconfig.xml test cores. [Sébastien
  Fievet]

- README tweaks. Thanks to @msabramo for the original patch! [Daniel
  Lindsley]

- Slightly better tomcat errors. [Daniel Lindsley]

- Improved scraping of tomcat error. [Dougal Matthews]

  When scraping for the HTML error message include
  the description if found.

- Merge pull request #86 from anti-social/fix_eval. [Chris Adams]

  Fixed eval in the _to_python method (thanks @anti-social)

  Ah, nice: since we no longer support Python 2.5 this is a great move.

- Fixed eval in the _to_python method. [Alexander Koval]

- Solr.add generator expression support (closes #81) [Chris Adams]

  The only compatibility issue before was a logging statement using len()
  on the input docs variable, which fails on generator expressions. Thanks
  to @timsavage for a patch changing this to measuring the message which
  is actually sent to Solr instead

- Enable request's session pooling (closes #82) [Chris Adams]

  Performing requests using a session enables urllib3's connection
  pooling, reducing connection latency.

  Thanks @cody-young for the patch

  Closes #83

v3.0.6 (2013-04-13)
-------------------

- Setup.py: require lxml 3.0+ for tomcat error messages. [Chris Adams]

  * Bumped version to 3.0.6

- Merge pull request #71 from mjumbewu/master. [Daniel Lindsley]

  Trailing slash in the base URL will break requests

- Make sure trailing and leading slashes do not collide. [Mjumbe Wawatu
  Ukweli]

v3.0.5 (2013-02-16)
-------------------

- Update error message string interpolation (closes #70) [Chris Adams]

  Python's string interpolation requires a tuple, not a list

v3.0.4 (2013-02-11)
-------------------

- Tag version 3.0.4 for PyPI. [Chris Adams]

  3.x had a minor bug (see SHA:74b0a36) but it broke logging for Solr
  errors which seems worth an easily deployed fix

- Correct log.error syntax on timeouts. [Chris Adams]

v3.0.3 (2013-01-24)
-------------------

- Update version to 3.0.3. [Chris Adams]

  Since python 2.6 compatibility was broken in 3.0+ this seems worth an update

- Force_unicode: backwards compatibility with Python 2.6. [Chris Adams]

v3.0.2 (2013-01-24)
-------------------

- Update version to 3.0.2. [Chris Adams]

- Fix rich content extraction method & tests. [Chris Adams]

  * Update test setup instructions with content extraction handler
    dependencies
  * Enable file upload support to _send_request
  * Added simple extract test

- Fix field boosting, simplify _build_doc. [Chris Adams]

  * Ensure that numbers are converted to strings to avoid
    lxml choking when asked to serialize a number (in 2013!).
  * Refactor logic to have a single code-path for both single and
    multi-value fields
  * Refactor use **kwargs style so there's a single Element() create
    call

- Force_unicode support for non-string types. [Chris Adams]

  Now force_unicode(1.0) will return u"1.0" for consistency and to avoid confusion
  with the Django function of the same name

v3.0.1 (2013-01-23)
-------------------

- Bumped to v3.0.1! [Daniel Lindsley]

- Updated README to include testing info & made sure the README gets
  included n the package. [Daniel Lindsley]

- Updated ignores. [Daniel Lindsley]

v3.0.0 (2013-01-23)
-------------------

- Bumped to v3.0.0, adding Python3 support! [Daniel Lindsley]

  Dependencies have changed & been slimmed down.

- Bumped to v2.1.0! [Daniel Lindsley]

- Catch socket errors for httplib fallback path. [Chris Adams]

- Catch IOError in _send_request. [Chris Adams]

  httplib2 can raise a bare socket.error in _send_request, which handles only
  AttributeError. This change catches all IOError subclasses, tells logging to
  include exception information and moves logging code outside of the try/except
  block to avoid any possibility of an exception in a log handler being caught by
  mistake.

- Fall back to HTML title when scraping error messages. [Chris Adams]

  Solr 3.6 + Jetty is not reliably detected by the existing approach but it does
  return a reasonably useful message in the title which is a lot more informative
  than "None"

- Provide full headers & response to logging handlers. [Chris Adams]

  This allows handlers such as Raven / Sentry to do something smart
  with the full HTTP headers and/or response body. Among other things
  this should provide more insight in situations when pysolr currently
  logs "Response: None"

- Full exception logging for basic connection failures. [Chris Adams]

- Logging: use obvious exc_info= syntax. [Chris Adams]

  As per the documentation, logging exc_info just needs to evaluate to
  True. This change makes it obvious that the passed in value is not
  actually used in any other way

- Added gthb to AUTHORS. [Daniel Lindsley]

- PEP-8 nitpicks. [Chris Adams]

- Don't bork on response with no "response" attr. [Gunnlaugur Þór Briem]

  (happens e.g. in grouped queries)

- Support 'grouped' in Solr results. [Gunnlaugur Þór Briem]

- Added ``extra_requires`` to cover the ``BeautifulSoup`` dependency.
  Thanks to kylemacfarlane for the report! [Daniel Lindsley]

- Added pabluk to AUTHORS. [Daniel Lindsley]

- Updated README file with optional requirement. [Pablo SEMINARIO]

- Added kwargs to extract() method. [Pablo SEMINARIO]

- Avoid forcing string interpolation when logging. [Chris Adams]

  This allows aggregators like Sentry and other consumers to see the raw,
  unformatted string and variables so they can e.g. group all instances of the
  same message even if the specific request values differ.

- Added HTTPS support for httplib. [Richard Mitchell]

- Added a long description for PyPI. [Daniel Lindsley]

- Added support for Solr rich-content extraction. [Chris Adams]

  This exposes Solr's http://wiki.apache.org/solr/ExtractingRequestHandler which
  allows you to index text content from structured file formats like PDF,
  Microsoft Office, etc.

- Bumped for the next round of beta. [Daniel Lindsley]

- Added cordmata to AUTHORS. [Daniel Lindsley]

- Updated suggest_terms so that it correctly handles response from Solr
  3.x releases. [Matt Cordial]

- Edited README via GitHub. [Daniel Lindsley]

- Bumped to v2.0.15! [Daniel Lindsley]

- Fixed a bug where ``server_string`` could come back as ``None``.
  Thanks to croddy for the report! [Daniel Lindsley]

- Added dourvais & soypunk to AUTHORS. [Daniel Lindsley]

- Unescape html entities in error messages. [David Cramer]

- Added support for getting at the Solr querying debug data when using
  search(). [Shawn Medero]

  Passing ``debug=True`` as kwarg, the ``search()`` method will activate this property in the JSON results.

- Fixed bug, qtime wasn't set when it was 0. [Daniel Dourvaris]

- Added query time to results as attribute. [Daniel Dourvaris]

- Bumped revision for dev on the next release. [Daniel Lindsley]

v2.0.14 (2011-04-29)
--------------------

- V2.0.14. [Daniel Lindsley]

- Always send commit if its not-null. [David Cramer]

- Add support for waitFlush and waitSearcher on update queries. Added
  support for expungeDeletes on commit(). Added support for maxSegments
  on optimize() [David Cramer]

- Ensure port is coerced to an integer as (at least some version of)
  socket does not handle unicode ports nicely. [David Cramer]

- Add support for commitWithin on Solr.add. [David Cramer]

- Better compatibility with the latest revisions of lxml. Thanks to
  ghostmob for pointing this out! [Daniel Lindsley]

- Fixed occasionally trying to call ``lower`` on ``None``. Thanks to
  girasquid for the report & original patch! [Daniel Lindsley]

v2.0.13 (2010-09-15)
--------------------

- Cleaned up how parameters are checked. Thanks to zyegfryed for the
  patch. v2.0.13. [Daniel Lindsley]

- Fixed a bug in the weighting when given a string field that's
  weighted. Thanks to akaihola for the report. [Daniel Lindsley]

- Fixed the case where the data being converted would be clean unicode.
  Thanks to acdha for submitting another version of this patch. [Daniel
  Lindsley]

- Fixed the long URL support to correctly deal with sequences. [Daniel
  Lindsley]

- Fixed a bug where additional parameters could cause the URL to be
  longer than 1024 even if the query is not. Thanks to zyegfryed for the
  report & patch! [Daniel Lindsley]

- Boost values are now coerced into a string. Thanks to notanumber for
  the patch! [Daniel Lindsley]

- All params are now safely encoded. Thanks to acdha for the patch!
  [Daniel Lindsley]

- Added term suggestion. Requires Solr 1.4+. Thanks to acdha for the
  patch! [Daniel Lindsley]

- If invalid characters are found, replace them. Thanks to stugots for
  the report and fix. [Daniel Lindsley]

- Slicing ``None`` doesn't work. Make it a string... [Daniel Lindsley]

- Added basic logging support. Thanks to sjaday for the suggestion.
  [Daniel Lindsley]

v2.0.12 (2010-06-20)
--------------------

- Releasing version v2.0.12. [Daniel Lindsley]

- Added a more helpful message for the ever classic "'NoneType' object
  has no attribute 'makefile'" error when providing an incorrect URL.
  [Daniel Lindsley]

- Added better error support when using Tomcat. Thanks to bochecha for
  the original patch. [Daniel Lindsley]

- Fixed a long-standing TODO, allowing commits to happen without a
  second request. Thanks to lyblandin for finally chiding me into fixing
  it. [Daniel Lindsley]

- Fixed a bug when sending long queries. Thanks to akaihola & gthb for
  the report and patch. [Daniel Lindsley]

- Corrected a bug where Unicode character might not transmit correctly.
  Thanks to anti-social for the initial patch. [Daniel Lindsley]

- Added field-based boost support. Thanks to notanumber for the patch.
  [David Sauve]

- Better error messages are now provided when things go south. Thanks to
  bochecha for the patch. [Daniel Lindsley]

- Added support for working with Solr cores. Thanks to james.colin.brady
  for the original patch. [Daniel Lindsley]

- Fixed a bug where empty strings/``None`` would be erroneously sent.
  Thanks to Chak for the patch. [Daniel Lindsley]

- Added support for the Stats component. Thanks to thomas.j.lee for the
  original patch. [Daniel Lindsley]

- Fixed datetime/date handling to use ``isoformat`` instead of manually
  constructing the string. Thanks to joegermuska for the suggestion.
  [Daniel Lindsley]

- Added document boost support. Thanks to Tomasz.Wegrzanowski for the
  patch. [Daniel Lindsley]

- Fixed pysolr to add documents explicitly using UTF-8. Thanks to jarek
  & dekstop for the patch. [Daniel Lindsley]

v2.0.11 (2010-04-28)
--------------------

- Fixed initialization parameters on ``Results``. Thanks to
  jonathan.slenders for pointing this out. v2.0.11. [Daniel Lindsley]

- Added a sane .gitignore. [Daniel Lindsley]

v2.0.10 (2010-04-28)
--------------------

- Fixed a bug in URL construction with httplib2. Thanks to maciekp.lists
  for the patch. v2.0.10. [Daniel Lindsley]

- Added a way to handle queries longer than 1024. Adapted from cogtree's
  Python Solr fork. [Daniel Lindsley]

- Fixed isinstance bug that can occur with the now potentially different
  datetime/date objects. [Daniel Lindsley]

- Altered pysolr to use, if available, Django's implementation of
  datetime for dates before 1900. Falls back to the default
  implementation of datetime. [Daniel Lindsley]

- If MLT was enabled but no reindexing was performed, Solr returns null
  instead of no docs. Handle this slightly more gracefully. [Daniel
  Lindsley]

- Corrected a regression when errors occur while using httplib. [Daniel
  Lindsley]

- Bumped version number for previous commit. [Daniel Lindsley]

- Altered the '_extract_error' method to be a little more useful when
  things go south. [Daniel Lindsley]

- Bumped version for previous commit. [polarcowz]

- Added (optional but default) sanitizing for updates. This cleans the
  XML sent of control characters which cause Solr's XML parser to break.
  [polarcowz]

- Fixed up a couple distribution bits. [polarcowz]

- Added spellchecking support. [polarcowz]

- Added timeouts (optional if httplib2 is installed). [polarcowz]

- Fixed DATETIME_REGEX & _from_python to match Solr documentation.
  Thanks initcrash! [polarcowz]

- Under some circumstances, Solr returns a regular data type instead of
  a string. Deal with it in _to_python as best as possible. [polarcowz]

- Added '_to_python' method for converting data back to its native
  Python type. Backward compatible (requires manually calling).
  [polarcowz]

- Updated pysolr to version 2.0. [polarcowz]

  New bits:
    * Now uses JSON instead of parsing XML. (jkocherhans)
    * Added support for passing many types of query parameters to Solr. (daniellindsley)
    * Added support for More Like This (requires Solr 1.3+). (daniellindsley)
    * Added support for highlighting. (daniellindsley)
    * Added support for faceting. (daniellindsley)

  Ought to be fairly backward-compatible (no known issues) but caution is advised when upgrading.

  Newly requires either the 'json' or 'simplejson' modules.

- Added the stuff needed to easy_install pysolr. And a LICENSE, since I
  just made fun of another project for not having one.
  [jacob.kaplanmoss]

- It would probably help if I imported the correct thing. [jkocherhans]

- This is getting a bit hairy, but try to import ElementTree from lxml
  as well. [jkocherhans]

- Use cElementTree if it's available. [jkocherhans]

- Removed unused import. Thanks, jarek.zgoda. [jkocherhans]

- Removed default values for start and rows from the search method.
  Thanks, jarek.zgoda. This will allow people to let solr determine what
  the default for those should be. [jkocherhans]

- Added converters for float and decimal. This references Issue 1.
  Thanks, jarek.zgoda. [jkocherhans]

- Fixed a bug for connections that don't specify a port number.
  [jkocherhans]

- Fixed Python 2.5-ism. [jkocherhans]

- Allowed for connections to solr instances that don't live at /solr.
  [jkocherhans]

- Added multiValue field handling support. [jkocherhans]

- Broke results out into a separate object with docs and hits
  attributes. [jkocherhans]

- Fixed typo that caused breakage with python < 2.5. [jkocherhans]

- Fixed a small typo. [jkocherhans]

- Initial import of pysolr. [jkocherhans]

- Initial directory structure. [(no author)]

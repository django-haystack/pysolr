import json
import unittest

from pysolr import SolrCoreAdmin, SolrError


class SolrCoreAdminTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin("http://localhost:8983/solr/admin/cores")

        # Unload any leftover demo cores before each test
        self._unload_demo_cores()

    def _unload_demo_cores(self):
        """
        Unload any demo cores left over from previous test runs.

        Solr keeps core state between requests, unlike a test database that can be
        reset easily after each test.

        If any test case perform a core operation such as:
            - creating a core,
            - renaming a core,
            - unloading a core,
            - swapping a core,
        leaves state behind and the next run encounters it, Solr will raise a
        "core already exists" error or another core-related error depending on the
        operation.

        Notes:
            - Unloading a core does not remove its `instanceDir` directory.
            - Tests can reuse that same `instanceDir` to create the core again.
        """
        demo_cores = [
            "demo_core1",
            "demo_core2",
        ]

        for core in demo_cores:
            try:
                self.solr_admin.unload(core)
            except SolrError:
                # Ignore any kind of errors during cleanup (e.g., API failures)
                pass

    def test_status(self):
        """Test the status endpoint returns details for all cores and specific cores."""

        # Status of all cores
        raw_all = self.solr_admin.status()
        all_data = json.loads(raw_all)

        self.assertIn("core0", all_data["status"])

        # Status of a specific core
        raw_single = self.solr_admin.status(core="core0")
        single_data = json.loads(raw_single)

        self.assertEqual(single_data["status"]["core0"]["name"], "core0")

    def test_create(self):
        """Test creating a core returns a successful response."""
        raw_response = self.solr_admin.create("demo_core1")
        data = json.loads(raw_response)

        self.assertEqual(data["responseHeader"]["status"], 0)
        self.assertEqual(data["core"], "demo_core1")

    def test_reload(self):
        """Test reloading a core returns a successful response."""
        raw_response = self.solr_admin.reload("core0")
        data = json.loads(raw_response)

        self.assertEqual(data["responseHeader"]["status"], 0)

    def test_rename(self):
        """Test renaming a core succeeds and the new name appears in the status."""

        # Create the core that will be renamed
        self.solr_admin.create("demo_core1")

        # Rename the core to a new name
        raw_response = self.solr_admin.rename("demo_core1", "demo_core2")
        data = json.loads(raw_response)

        self.assertEqual(data["responseHeader"]["status"], 0)

        # Verify that the renamed core appears in the status response
        raw_response2 = self.solr_admin.status(core="demo_core2")
        data2 = json.loads(raw_response2)

        self.assertEqual(data2["status"]["demo_core2"]["name"], "demo_core2")

    def test_swap(self):
        """
        Test that swapping two cores succeeds.
        ┌───────────────────────────────┬───────────────────────────────┐
        │            Before             │              After            │
        ├───────────────────────────────┼───────────────────────────────┤
        │ demo_core1/core.properties    │ demo_core1/core.properties    │
        │     → name = demo_core1       │     → name = demo_core2       │
        ├───────────────────────────────┼───────────────────────────────┤
        │ demo_core2/core.properties    │ demo_core2/core.properties    │
        │     → name = demo_core2       │     → name = demo_core1       │
        └───────────────────────────────┴───────────────────────────────┘
        """
        self.solr_admin.create("demo_core1")
        self.solr_admin.create("demo_core2")

        # Perform swap
        raw_swap = self.solr_admin.swap("demo_core1", "demo_core2")
        swap_data = json.loads(raw_swap)

        self.assertEqual(swap_data["responseHeader"]["status"], 0)

    def test_unload(self):
        """
        Test that unloading a core returns a successful JSON response.

        This test creates a core, unloads it, and verifies that the response
        contains a status of 0.
        """
        self.solr_admin.create("demo_core1")

        raw_response = self.solr_admin.unload("demo_core1")
        data = json.loads(raw_response)

        self.assertEqual(data["responseHeader"]["status"], 0)

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, "wheatley")

    def test_status__nonexistent_core_returns_empty_response(self):
        """Test that requesting status for a missing core returns an empty response."""
        raw_response = self.solr_admin.status(core="not_exists")
        data = json.loads(raw_response)

        self.assertNotIn("name", data["status"]["not_exists"])
        self.assertNotIn("instanceDir", data["status"]["not_exists"])

    def test_create__existing_core_raises_error(self):
        """Test creating a core that already exists returns a 500 error."""

        # First create succeeds
        self.solr_admin.create("demo_core1")

        # Creating the same core again should return a 500 error response
        raw_response = self.solr_admin.create("demo_core1")
        data = json.loads(raw_response)

        self.assertEqual(data["responseHeader"]["status"], 500)
        self.assertEqual(
            data["error"]["msg"], "Core with name 'demo_core1' already exists."
        )

    def test_reload__nonexistent_core_raises_error(self):
        """Test that reloading a non-existent core returns a 400 error."""
        raw_response = self.solr_admin.reload("not_exists")
        data = json.loads(raw_response)

        # Solr returns a 400 error for missing cores
        self.assertEqual(data["responseHeader"]["status"], 400)
        self.assertIn("No such core", data["error"]["msg"])
        self.assertIn("not_exists", data["error"]["msg"])

    def test_rename__nonexistent_core_no_effect(self):
        """
        Test that renaming a non-existent core has no effect on target core.

        Solr silently ignores rename operations when the source core does not exist.
        This test verifies that attempting to rename a missing core does not create
        the target core and does not modify any core state.
        """

        # Attempt to rename a core that does not exist (this should have no effect)
        self.solr_admin.rename("not_exists", "demo_core99")

        # Check the status of the target core to verify the rename had no effect
        raw_response = self.solr_admin.status(core="demo_core99")
        data = json.loads(raw_response)

        # The target core should not exist because the rename operation was ignored
        self.assertNotIn("name", data["status"]["demo_core99"])
        self.assertNotIn("instanceDir", data["status"]["demo_core99"])

    def test_swap__missing_source_core_returns_error(self):
        """Test swapping when the source core is missing returns a 400 error."""

        # Create only the target core
        self.solr_admin.create("demo_core2")

        # Attempt to swap a missing source core with an existing target core
        raw_response = self.solr_admin.swap("not_exists", "demo_core2")
        data = json.loads(raw_response)

        # Solr returns a 400 error when the source core does not exist
        self.assertEqual(data["responseHeader"]["status"], 400)
        self.assertIn("No such core", data["error"]["msg"])
        self.assertIn("not_exists", data["error"]["msg"])

    def test_swap__missing_target_core_returns_error(self):
        """Test swapping when the target core is missing returns a 400 error."""

        # Create only the source core
        self.solr_admin.create("demo_core1")

        # Attempt to swap with a missing target core
        raw_response = self.solr_admin.swap("demo_core1", "not_exists")
        data = json.loads(raw_response)

        # Solr returns a 400 error when the target core does not exist
        self.assertEqual(data["responseHeader"]["status"], 400)
        self.assertIn("No such core", data["error"]["msg"])
        self.assertIn("not_exists", data["error"]["msg"])

    def test_unload__nonexistent_core_returns_error(self):
        """Test unloading a non-existent core returns a 400 error response."""

        # Attempt to unload a core that does not exist
        raw_response = self.solr_admin.unload("not_exists")
        data = json.loads(raw_response)

        # Solr returns a 400 error for unloading a missing core
        self.assertEqual(data["responseHeader"]["status"], 400)
        self.assertIn("Cannot unload non-existent core", data["error"]["msg"])
        self.assertIn("not_exists", data["error"]["msg"])

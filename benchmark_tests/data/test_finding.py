from typing import Dict
from unittest.mock import patch

from nose.tools import assert_equals

from benchmark.data.finding import Finding
from benchmark_tests.test_utils.data_util import create_misuse


class TestPotentialHit:
    # noinspection PyAttributeOutsideInit
    def setup(self):
        self.misuse = create_misuse('misuse', meta={"location": {"file": "a", "method": "m()"}})

    def test_matches_on_file(self):
        self.misuse.location.file = "some-class.java"
        self.assert_potential_hit({"file": "some-class.java"})

    def test_matches_on_file_absolute(self):
        self.misuse.location.file = "java/main/some-class.java"
        self.assert_potential_hit({"file": "/some/prefix/java/main/some-class.java"})

    def test_matches_on_class(self):
        self.misuse.location.file = "some-class.java"
        self.assert_potential_hit({"file": "some-class.class"})

    def test_matches_on_inner_class(self):
        self.misuse.location.file = "some-class.java"
        self.assert_potential_hit({"file": "some-class$inner-class.class"})

    def test_differs_on_method(self):
        self.misuse.location.method = "method()"
        self.assert_no_potential_hit({"method": "other_method()"})

    def test_matches_on_method_name(self):
        self.misuse.location.method = "method(A, B)"
        self.assert_potential_hit({"method": "method"})

    def test_differs_on_method_name_prefix(self):
        self.misuse.location.method = "appendX"
        self.assert_no_potential_hit({"method": "append"})

    def test_matches_on_method_signature(self):
        self.misuse.location.method = "method(A, B)"
        self.assert_potential_hit({"method": "method(A, B)"})

    def test_matches_on_method_signature_name_only(self):
        self.misuse.location.method = "method(A)"
        self.assert_potential_hit({"method": "method(p.A)"}, True)

    def assert_potential_hit(self, finding_data: Dict[str, str], method_name_only: bool=False):
        finding = self.create_finding(finding_data)
        assert finding.is_potential_hit(self.misuse, method_name_only)

    def assert_no_potential_hit(self, finding_data: Dict[str, str]):
        finding = self.create_finding(finding_data)
        assert not finding.is_potential_hit(self.misuse)

    def create_finding(self, finding_data: Dict[str, str]):
        if "file" not in finding_data:
            finding_data["file"] = self.misuse.location.file
        if "method" not in finding_data:
            finding_data["method"] = self.misuse.location.method

        return Finding(finding_data)


@patch("benchmark.data.finding.exec_util")
class TestTargetCode:
    def test_loads_code(self, utils_mock):
        utils_mock.side_effect =\
            lambda tool, args: "1:-code-" if tool == "MethodExtractor" and args == '"-file-" "-method-"' else ""

        finding = Finding({"file": "-file-", "method": "-method-"})

        assert_equals("-code-", finding.get_snippet().code)

    def test_loads_first_line_number(self, util_mock):
        util_mock.return_value = "42:-code-"

        finding = Finding({"file": "-file-"})

        assert_equals(42, finding.get_snippet().first_line_number)

from os.path import join, exists
from tempfile import mkdtemp

from nose.tools import assert_equals

from benchmark.subprocesses.tasks.implementations.review import review_page
from benchmark.utils.io import remove_tree
from benchmark_tests.test_utils.data_util import create_project, create_version, create_misuse


class TestReviewPageGenerator:
    # noinspection PyAttributeOutsideInit
    def setup(self):
        self.temp_dir = mkdtemp(prefix='mubench-test-review-page-generator_')

        self.test_project = create_project('project')
        self.test_misuse = create_misuse('misuse', project=self.test_project)
        self.test_version = create_version('version', project=self.test_project, misuses=[self.test_misuse])

        self.findings_folder = join(self.temp_dir, 'findings', 'detector', 'project', 'version')
        self.review_folder = join(self.temp_dir, 'reviews', 'detector', 'project', 'version')

    def teardown(self):
        remove_tree(self.temp_dir)

    def test_creates_reviewing_line(self):
        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, [])

        content = self.read_review_file()
        assert "<h1>Review: detector/project/version/project.misuse</h1>" in content

    def test_adds_misuse_description(self):
        self.test_misuse._DESCRIPTION = "SubLine.intersection() may return null."

        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, [])

        content = self.read_review_file()
        assert "<b>Description:</b> SubLine.intersection() may return null." in content

    def test_adds_fix_description(self):
        self.test_misuse.fix.description = "Check result before using."

        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, [])

        content = self.read_review_file()
        assert "<b>Fix Description:</b> Check result before using." in content

    def test_adds_misuse_characteristics(self):
        self.test_misuse._characteristics = ["missing/condition/null_check"]

        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, [])

        content = self.read_review_file()
        assert "<b>Misuse Elements:</b><ul>\n<li>missing/condition/null_check</li>\n</ul>" in content

    def test_adds_location(self):
        self.test_misuse.location.file = "org.apache...SubLine"
        self.test_misuse.location.method = "intersection(SubLine subLine)"
        self.test_misuse.fix.commit = "http://commit.url"

        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, [])

        content = self.read_review_file()
        assert "<b>In File:</b> <a href=\"http://commit.url\">org.apache...SubLine</a>," \
               " <b>Method:</b> intersection(SubLine subLine)" in content

    def test_adds_potential_hit_information(self):
        potential_hits = [{"missingcalls": ["getAngle()"]}, {"additionalkey": "additional information"}]

        review_page.generate(self.review_folder, 'detector', self.test_project, self.test_version,
                             self.test_misuse, potential_hits)

        content = self.read_review_file()
        assert "<h2>Potential Hits</h2>\n<table border=\"1\" cellpadding=\"5\">\n" \
               "<tr>\n<th>additionalkey</th>\n<th>missingcalls</th>\n</tr>\n" \
               "<tr>\n<td></td>\n<td><ul>\n<li>getAngle()</li>\n</ul></td>\n</tr>\n" \
               "<tr>\n<td>additional information</td>\n<td></td>\n</tr>\n" \
               "</table>\n" in content

    def read_review_file(self):
        review_file = join(self.review_folder, 'review.html')
        assert exists(review_file)
        with open(review_file) as file:
            actual_lines = file.readlines()
        return "".join(actual_lines)
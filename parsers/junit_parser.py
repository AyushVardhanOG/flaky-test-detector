"""
Parser for JUnit (Java) test results using the surefire/JUnit XML report
format — NOT console scraping. This is the industry-standard way to read
JUnit results (Maven/Gradle both produce these XML files automatically),
so this parser is more reliable than the pytest/jest console parsers.

Typical location after a Maven build:
    target/surefire-reports/TEST-*.xml
Gradle:
    build/test-results/test/TEST-*.xml

Usage: run your test suite, then call parse_junit_xml_dir() pointing at
the reports folder, once per run.
"""

import os
import glob
import xml.etree.ElementTree as ET
from typing import Dict, List


def parse_junit_xml_file(filepath: str) -> Dict[str, str]:
    """Parses one TEST-*.xml file. Returns {test_name: status}."""
    results = {}
    try:
        tree = ET.parse(filepath)
    except ET.ParseError:
        return results

    root = tree.getroot()
    classname = root.attrib.get("name", "")

    for testcase in root.findall("testcase"):
        name = testcase.attrib.get("name", "unknown")
        full_name = f"{classname}::{name}" if classname else name

        if testcase.find("failure") is not None:
            status = "FAILED"
        elif testcase.find("error") is not None:
            status = "ERROR"
        elif testcase.find("skipped") is not None:
            status = "SKIPPED"
        else:
            status = "PASSED"

        results[full_name] = status

    return results


def parse_junit_xml_dir(reports_dir: str) -> Dict[str, str]:
    """
    Parses ALL TEST-*.xml files in a directory (one test run typically
    produces multiple XML files, one per test class).
    Returns merged {test_name: status} for that whole run.
    """
    merged = {}
    xml_files = glob.glob(os.path.join(reports_dir, "TEST-*.xml"))
    for filepath in xml_files:
        merged.update(parse_junit_xml_file(filepath))
    return merged


def parse_multiple_run_dirs(report_dirs: List[str]) -> Dict[str, List[str]]:
    """
    Given a list of report directories — ONE PER RUN (you'll need to copy/
    rename the surefire-reports folder between runs, since each new test
    run overwrites it) — returns {test_name: [status_run1, status_run2, ...]}
    """
    per_run_results = [parse_junit_xml_dir(d) for d in report_dirs]

    all_test_names = set()
    for run in per_run_results:
        all_test_names.update(run.keys())

    history: Dict[str, List[str]] = {name: [] for name in all_test_names}
    for run in per_run_results:
        for name in all_test_names:
            history[name].append(run.get(name, "MISSING"))

    return history
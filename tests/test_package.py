import importlib.util
from pathlib import Path


PACKAGE_PATH = Path(__file__).parents[1] / "package.py"
SPEC = importlib.util.spec_from_file_location("receiptreader_package", PACKAGE_PATH)
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def test_dependency_report_uses_real_paddlex_extras():
    reported = {name for name, _, _ in package.dependency_report()}
    expected = {
        dependency
        for extra in package.PADDLEX_EXTRAS
        for dependency in package.paddlex_deps.EXTRAS[extra]
    }
    assert reported == expected


def test_all_ocr_dependencies_are_available_in_build_environment():
    missing = [
        name
        for name, available, _ in package.dependency_report()
        if not available
    ]
    assert missing == []

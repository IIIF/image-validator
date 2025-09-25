from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Iterator
from urllib.error import HTTPError

from .tests.test import (
    get_tests,
    TargetServer,
    ComplianceLevel,
    TestCategory,
    ValidationFailure,
    ValidationSuccess,
    ValidationTest,
)


class SizedGenerator[T]:
    def __init__(self, it: Iterable[T], total: int):
        self._iterator = iter(it)
        self.num_total = total

    def __iter__(self) -> Iterator[T]:
        return self._iterator

    def __next__(self) -> T:
        return next(self._iterator)


def _test_is_applicable(test, features):
    if features.version not in test.versions:
        return False
    level = test.compliance_level
    if isinstance(level, dict):
        level = level[features.version]
    if level <= features.compliance_level:
        return True
    extra_names = test.extra_name
    if extra_names is None:
        return False
    elif isinstance(extra_names, str):
        extra_names = [extra_names]
    if test.category == TestCategory.FORMAT and any(
        name in features.extra_formats for name in extra_names
    ):
        return True
    if test.category == TestCategory.QUALITY and any(
        name in features.extra_qualities for name in extra_names
    ):
        return True
    if any(name in features.extra_features for name in extra_names):
        return True
    return False


def run_tests(
    server: TargetServer, max_threads=4
) -> SizedGenerator[
    tuple[
        type[ValidationTest],
        ValidationFailure
        | ValidationSuccess
        | list[ValidationFailure | ValidationSuccess],
    ]
]:
    features = server.feature_set()
    all_tests = get_tests(server.version)

    applicable_tests = [
        test for test in all_tests if _test_is_applicable(test, features)
    ]

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_test = {
            executor.submit(test.run, server): test for test in applicable_tests
        }

        def _generator():
            for future in as_completed(future_to_test):
                test = future_to_test[future]
                # try:
                result = future.result()
                # except Exception as exc:
                #    result = ValidationFailure(
                #        url= exc.url if isinstance(exc, HTTPError) else "<unknown>",
                #        expected="Test to complete without error",
                #        received=f"Test raised an exception: {exc}",
                #        details="An unexpected error occurred during the test execution",
                #    )
                yield test, result

        return SizedGenerator(_generator(), len(applicable_tests))

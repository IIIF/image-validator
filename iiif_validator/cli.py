import argparse

from collections import defaultdict

import rich
from rich.progress import Progress, BarColumn

from .validate import run_tests
from .tests.test import TargetServer, IIIFVersion, ValidationFailure, ValidationTest


def main(
    base_url: str,
    is_v2: bool,
    validation_id="67352ccc-d1b0-11e1-89ae-279075081939",
    max_threads: int = 4,
):
    server = TargetServer(
        base_url,
        validation_id=validation_id,
        version=IIIFVersion.V2 if is_v2 else IIIFVersion.V3,
    )

    rich.print(
        f"Validating IIIF Image API {server.version.value} server at [blue]{base_url}[/blue]"
    )
    features = server.feature_set()
    rich.print(
        f"Detected compliance level: [green]{features.compliance_level.name}[/green]"
    )
    if features.extra_qualities:
        rich.print(
            f"Detected extra qualities: [green]{', '.join(features.extra_qualities)}[/green]"
        )
    if features.extra_formats:
        rich.print(
            f"Detected extra formats: [green]{', '.join(features.extra_formats)}[/green]"
        )
    if features.extra_features:
        rich.print(
            f"Detected extra features: [green]{', '.join(features.extra_features)}[/green]"
        )

    test_gen = run_tests(server, max_threads=max_threads)

    failures: dict[type[ValidationTest], list[ValidationFailure]] = defaultdict(list)
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "[green]✓ {task.fields[ok]}[/green]",
        "[red]✗ {task.fields[failed]}[/red]",
        "[blue]{task.fields[passed_percent]:<2.0f}% passed[/blue]",
    ) as progress:
        failed_count = 0
        ok_count = 0
        task = progress.add_task(
            "Running tests...",
            total=test_gen.num_total,
            ok=0,
            failed=0,
            passed_percent=0.0,
        )
        for test, result in test_gen:
            if not isinstance(result, list):
                result = [result]
            for res in result:
                if isinstance(res, ValidationFailure):
                    failed_count += 1
                    failures[test].append(res)
                    iiif_name = (
                        f"[blue]({str(test.extra_name)})[/blue] "
                        if test.extra_name
                        else ""
                    )
                    progress.console.print(
                        f"[red]✗ {test.name} {iiif_name}[white]\\[{test.__module__.split('.')[-1]}][/white]: {res.details}[/red]\n"
                        f"  Expected: [blue]{res.expected}[/blue]\n"
                        f"  Received: [red]{res.received}[/red]\n"
                        f"  URL: {res.url}\n"
                    )
                else:
                    ok_count += 1
            progress.update(
                task,
                advance=1,
                failed=failed_count,
                ok=ok_count,
                passed_percent=ok_count / max((failed_count + ok_count), 1) * 100,
            )


def cli():
    parser = argparse.ArgumentParser(
        description="Validate an IIIF Image API 2.0 or 3.0 server."
    )
    parser.add_argument("base_url", type=str, help="The base URL of the IIIF server.")
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Validate as an IIIF Image API 2.0 server (default is 3.0).",
    )
    parser.add_argument(
        "--validation-id",
        type=str,
        default="67352ccc-d1b0-11e1-89ae-279075081939",
        help="The validation ID to use (default is the official IIIF validator ID).",
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=4,
        help="The maximum number of threads to use for running the tests (default is 4).",
    )
    args = parser.parse_args()

    main(
        args.base_url,
        args.v2,
        validation_id=args.validation_id,
        max_threads=args.max_threads,
    )


if __name__ == "__main__":
    cli()

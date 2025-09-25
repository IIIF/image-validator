import json
from typing import Callable

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationSuccess,
    ValidationFailure,
    get_info_json,
    make_request,
)


class TestInfoJsonStructure(ValidationTest):
    name = "Check info.json"
    compliance_level = ComplianceLevel.LEVEL_0
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> list[ValidationFailure | ValidationSuccess]:
        results = []
        info_resp = make_request(server.info_url())
        if info_resp.status != 200:
            url = server.info_url()
            return [
                ValidationFailure(
                    url=url,
                    expected="status code 200",
                    received=f"status code {info_resp.status}",
                    details="Failed to fetch info.json",
                )
            ]

        content_type = info_resp.headers.get("content-type", "").split(";")[0]
        if content_type not in ("application/json", "application/ld+json"):
            results.append(
                ValidationFailure(
                    url=server.info_url(),
                    expected="content-type is application/json or application/ld+json",
                    received=f"content-type is {content_type}",
                    details="Invalid content-type for info.json response",
                )
            )
        try:
            json.loads(info_resp.body)
        except ValueError:
            results.append(
                ValidationFailure(
                    url=server.info_url(),
                    expected="valid JSON",
                    received="invalid JSON",
                    details="info.json response must be valid JSON",
                )
            )
            return results

        info = get_info_json(server)
        is_v2 = IIIFVersion.V2 == server.version
        id_field = "@id" if is_v2 else "id"
        context = f"http://iiif.io/api/image/{2 if is_v2 else 3}/context.json"
        info_url = server.info_url()
        base_url = f"{server.base_url}/{server.validation_id}"
        results.extend(
            [
                has_required_field(info, "width", url=info_url),
                field_has_type(info, "width", int, url=info_url),
                has_required_field(info, "height", url=info_url),
                field_has_type(info, "height", int, url=info_url),
                has_required_field(info, id_field, url=info_url),
                field_has_value_matching(
                    info,
                    id_field,
                    lambda val: isinstance(val, str) and val.startswith("http"),
                    "is an URL",
                    url=info_url,
                ),
                field_has_value(info, id_field, base_url, url=info_url),
                has_required_field(info, "@context", url=info_url),
                field_has_value(info, "@context", context, url=info_url),
                has_required_field(info, "protocol", url=info_url),
                field_has_value(
                    info, "protocol", "http://iiif.io/api/image", url=info_url
                ),
                *check_profile(is_v2, info, url=info_url),
                *check_sizes(info, url=info_url),
                *check_tiles(info, url=info_url),
                *(check_v3_fields(info, url=info_url) if not is_v2 else []),
            ]
        )
        return results


def has_required_field(
    info: dict, field: str, url: str | None = None
) -> ValidationFailure | ValidationSuccess:
    return check(f"required field: {field}", field in info, url=url)


def field_has_type(
    info: dict, field: str, type_: type, url: str | None = None
) -> ValidationFailure | ValidationSuccess:
    return check(
        f"is {type_} field: {field}", isinstance(info.get(field), type_), url=url
    )


def field_has_value(
    info: dict, field: str, value: object, url: str | None = None
) -> ValidationFailure | ValidationSuccess:
    return check(
        f"field {field} has value: {value}",
        info.get(field) == value,
        str(value),
        str(info.get(field)),
        url=url,
    )


def field_has_value_matching(
    info: dict,
    field: str,
    predicate: Callable,
    description: str,
    url: str | None = None,
) -> ValidationFailure | ValidationSuccess:
    return check(
        f"field {field} {description}",
        predicate(info.get(field)),
        description,
        str(info.get(field)),
        url=url,
    )


def check_profile(
    is_v2: bool, info: dict, url: str | None = None
) -> list[ValidationFailure | ValidationSuccess]:
    results = []
    results.append(has_required_field(info, "profile", url=url))
    if is_v2:
        results.extend(
            [
                field_has_type(info, "profile", list, url=url),
                field_has_value_matching(
                    info,
                    "profile",
                    lambda p: isinstance(p, list)
                    and p[0].startswith("http://iiif.io/api/image/2/level"),
                    "should have an official IIIF profile as the first profile",
                    url=url,
                ),
            ]
        )
    else:
        results.append(
            field_has_value_matching(
                info,
                "profile",
                lambda p: p in ["level0", "level1", "level2"],
                "should be one of ['level0', 'level1', 'level2']",
                url=url,
            )
        )
    return results


def check_sizes(
    info: dict, url: str | None = None
) -> list[ValidationFailure | ValidationSuccess]:
    sizes = info.get("sizes")
    if sizes is None:
        return []

    results = [field_has_type(info, "sizes", list, url=url)]
    if not isinstance(sizes, list):
        return results

    for size in sizes:
        if not isinstance(size, dict):
            results.append(
                ValidationFailure(
                    url=url or "<unknown>",
                    expected="dict/object",
                    received=str(type(size)),
                    details="entries in 'sizes' must be objects",
                )
            )
        results.extend(
            [
                has_required_field(size, "width", url=url),
                field_has_type(size, "width", int, url=url),
                has_required_field(size, "height", url=url),
                field_has_type(size, "height", int, url=url),
            ]
        )
    return results


def check_tiles(
    info: dict, url: str | None = None
) -> list[ValidationFailure | ValidationSuccess]:
    tiles = info.get("tiles")
    if tiles is None:
        return []

    results = [field_has_type(info, "tiles", list, url=url)]
    if not isinstance(tiles, list):
        return results

    for tile in tiles:
        if not isinstance(tile, dict):
            results.append(
                ValidationFailure(
                    url=url or "<unknown>",
                    expected="dict/object",
                    received=str(type(tile)),
                    details="entries in 'tiles' must be objects",
                )
            )
        results.extend(
            [
                has_required_field(tile, "width", url=url),
                field_has_type(tile, "width", int, url=url),
                has_required_field(tile, "scaleFactors", url=url),
                field_has_value_matching(
                    tile,
                    "scaleFactors",
                    lambda f: isinstance(f, list)
                    and all(isinstance(x, int) for x in f),
                    "scaleFactors must be integer values",
                    url=url,
                ),
            ]
        )
    return results


def check_v3_fields(
    info: dict, url: str | None = None
) -> list[ValidationFailure | ValidationSuccess]:
    results = []
    results.append(has_required_field(info, "type", url=url))
    results.append(field_has_value(info, "type", "ImageService3", url=url))
    if "license" in info:
        results.append(
            ValidationFailure(
                url=url or "<unknown>",
                expected="field name 'rights'",
                received="field name 'license'",
                details="'license' has been renamed to 'rights' in v3",
            )
        )
    if "rights" in info:
        results.append(field_has_type(info, "rights", str, url=url))
        results.append(
            field_has_value_matching(
                info,
                "rights",
                lambda r: isinstance(r, str) and r.startswith("http:"),
                "'rights' must be a single URI from Creative Commonsl, RightsStatements.org or URIs registered as extensions",
                url=url,
            )
        )
    if "extraQualities" in info:
        field_has_type(info, "extraQualities", list, url=url)
        field_has_value_matching(
            info,
            "extraQualities",
            lambda qs: isinstance(qs, list) and all(isinstance(q, str) for q in qs),
            "'extraQualities' must be a list of strings",
            url=url,
        )
    if "extraFormats" in info:
        field_has_type(info, "extraFormats", list, url=url)
        field_has_value_matching(
            info,
            "extraFormats",
            lambda qs: isinstance(qs, list) and all(isinstance(q, str) for q in qs),
            "'extraFormats' must be a list of strings",
            url=url,
        )
    if "extraFeatures" in info:
        field_has_type(info, "extraFeatures", list, url=url)
        field_has_value_matching(
            info,
            "extraFeatures",
            lambda qs: isinstance(qs, list) and all(isinstance(q, str) for q in qs),
            "'extraFeatures' must be a list of strings",
            url=url,
        )
    results.extend(check_linking_prop(info, "service", url=url))
    results.extend(check_linking_prop(info, "partOf", url=url))
    results.extend(check_linking_prop(info, "seeAlso", url=url))

    if "attribution" in info:
        results.append(
            ValidationFailure(
                url=url or "<unknown>",
                expected="'attribution' field not to be present",
                received="'attribution' field was present",
                details="'attribution' field was removed in v3",
            )
        )
    if "logo" in info:
        results.append(
            ValidationFailure(
                url=url or "<unknown>",
                expected="'logo' field not to be present",
                received="'logo' field was present",
                details="'logo' field was removed in v3",
            )
        )
    return results
    return results


def check_linking_prop(
    info: dict, field: str, url: str | None = None
) -> list[ValidationFailure | ValidationSuccess]:
    if field not in info:
        return []
    results = []
    results.append(field_has_type(info, field, list, url=url))
    if not isinstance(info[field], list):
        return results

    for item in info[field]:
        if not isinstance(item, dict):
            results.append(
                ValidationFailure(
                    url=url or "<unknown>",
                    expected="type 'list'",
                    received=f"type '{type(item)}",
                    details=f"linking entries in {field} must be dicts/objects",
                )
            )
        else:
            results.append(
                ValidationSuccess(
                    details=f"Linking entries in {field} are dicts/objects"
                )
            )
        results.extend(
            [
                has_required_field(item, "id", url=url),
                field_has_type(item, "id", str, url=url),
                has_required_field(item, "type", url=url),
                field_has_type(item, "type", str, url=url),
            ]
        )

    return results


def check_label(obj: dict) -> list[ValidationFailure | ValidationSuccess]:
    raise NotImplementedError


def check(
    description: str,
    condition: bool,
    expected: str = "👍",
    received: str = "👎",
    url: str | None = None,
) -> ValidationFailure | ValidationSuccess:
    if condition:
        return ValidationSuccess(details=f"info.json passed: {description}")
    else:
        return ValidationFailure(
            url=url or "<unknown>",
            expected=expected,
            received=received,
            details=f"info.json failed: {description}",
        )

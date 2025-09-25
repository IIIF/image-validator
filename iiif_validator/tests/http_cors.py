from typing import Literal
from urllib.request import Request

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    make_request,
    HEADERS,
    ImageAPIRequest,
)


class CorsImageTest(ValidationTest):
    """
    [...]
    Servers SHOULD support CORS on image responses.
    [...]
    Servers SHOULD support reuse of Image API resources by following the
    relevant requirements of the CORS specification, including the
    `Access-Control-Allow-Origin` header and the preflight request pattern.
    """

    name = "CORS Header on info.json responses"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.HTTP
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "cors"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        results = []
        for resource_type in ("info", "image"):
            for method in ("OPTIONS", "GET"):
                results.append(_single_run(server, resource_type, method))
        return results


def _single_run(
    server: TargetServer,
    resource_type: Literal["info", "image"],
    method: Literal["GET", "OPTIONS"],
) -> ValidationSuccess | ValidationFailure:
    origin = HEADERS["Origin"]

    if resource_type == "info":
        url = server.info_url()
    else:
        url = ImageAPIRequest.of().url(server)
    resp = make_request(Request(url, method=method))
    cors = resp.headers.get("access-control-allow-origin", None)
    if cors in ("*", origin):
        return ValidationSuccess(
            details=f"CORS header on {resource_type} with method={method} present and correct"
        )
    else:
        return ValidationFailure(
            url=url,
            expected=f"Access-Control-Allow-Origin: {origin} or *",
            received=f"Access-Control-Allow-Origin: {cors or '<none>'}",
            details=f"CORS header for {resource_type} with method={method} missing or incorrect",
        )

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    make_request,
)


class InfoHasJsonLdTypeWhenRequested(ValidationTest):
    name = "Info response has JSON-LD type when requested"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.HTTP
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "jsonldMediaType"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        info_resp = make_request(server.info_url(), {"Accept": "application/ld+json"})
        if info_resp.status != 200:
            url = server.info_url()
            return ValidationFailure(
                url=url,
                expected="HTTP Status 200",
                received=f"HTTP Status {info_resp.status}",
                details="Got unexpected status code when requesting JSON-LD",
            )
        content_type = info_resp.headers.get("content-type", "")
        if not content_type.startswith("application/ld+json"):
            url = server.info_url()
            return ValidationFailure(
                url=url,
                expected="Content-Type to start with application/ld+json",
                received=f"Content-Type: {content_type}",
                details="Got unexpected Content-Type when requesting JSON-LD",
            )
        return ValidationSuccess(
            details="Info response had JSON-LD type when requested"
        )

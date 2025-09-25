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


class ErrorUnescapedIdentifier(ValidationTest):
    name = "Unescaped Identifier gives 404"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        url = f"{server.base_url}/%5Bfrob%5D/info.json"
        resp = make_request(url)
        if resp.status in (404, 400):
            return ValidationSuccess(
                details="Returned 404 or 400 for random identifier"
            )
        else:
            return ValidationFailure(
                url=url,
                expected="HTTP Status 404 or 400",
                received=f"HTTP Status {resp.status}",
                details="Got unexpected status code for unescaped identifier",
            )

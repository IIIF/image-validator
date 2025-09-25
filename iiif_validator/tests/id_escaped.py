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


class CorrectlyHandlesEscapedIdentifier(ValidationTest):
    name = "Correctly handles escaped identifier"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        escaped_id = server.validation_id.replace("-", "%2D")
        url = f"{server.base_url}/{escaped_id}/info.json"
        resp = make_request(url)
        if resp.status == 200:
            return ValidationSuccess(details="Returned 200 for escaped identifier")
        else:
            return ValidationFailure(
                url=url,
                expected="HTTP Status 200",
                received=f"HTTP Status {resp.status}",
                details="Got unexpected status code for escapedidentifier",
            )

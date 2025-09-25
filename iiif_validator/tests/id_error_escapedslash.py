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


class ErrorEscapedSlash(ValidationTest):
    name = "Forward slash gives 404"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        resp = make_request(f"{server.base_url}/a/b/info.json")
        if resp.status == 404:
            return ValidationSuccess(
                details="Returned 404 for forward slash in identifier"
            )
        else:
            url = f"{server.base_url}/a/b/info.json"
            return ValidationFailure(
                url=url,
                expected="HTTP Status 404",
                received=f"HTTP Status {resp.status}",
                details="Got unexpected status code for identifier with forward slash",
            )

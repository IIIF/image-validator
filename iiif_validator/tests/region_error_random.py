from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    ImageAPIRequest,
    make_request,
    make_random_string,
)


class ErrorOnRandomRegion(ValidationTest):
    name = "Random region gives 400"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.REGION
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        url = ImageAPIRequest.of(region=make_random_string(6)).url(server)
        resp = make_request(url)
        if resp.status != 400:
            return ValidationFailure(
                url=url,
                expected="400 Bad Request",
                received=f"{resp.status} {resp.body.decode('utf8')}",
                details=f"Server did not return 400 for random region",
            )
        return ValidationSuccess(details="Server returned 400 for random region")

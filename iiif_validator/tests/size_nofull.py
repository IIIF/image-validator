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
)


class SizeNoFullTest(ValidationTest):
    name = "Version 3.0 has replaced the size full with max"
    compliance_level = ComplianceLevel.LEVEL_0
    category = TestCategory.SIZE
    versions = [IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        req = ImageAPIRequest.of(size="full")
        url = req.url(server)
        resp = make_request(url)

        if resp.status != 200:
            return ValidationSuccess(
                details="Request for size='full' did not return 200, as expected in v3."
            )
        else:
            return ValidationFailure(
                url=url,
                expected="Non-200 status code",
                received=f"{resp.status}",
                details="Version 3.0 has replaced the size 'full' with 'max'. A request for 'full' should not return a 200 status.",
            )

import random

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    ImageAPIRequest,
    make_random_string,
    make_request,
)


class ErrorOnRandomQuality(ValidationTest):
    name = "Random quality gives 400"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.QUALITY
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        random.seed(31337)  # Ensure reproducibility
        url = ImageAPIRequest.of(quality=make_random_string(6)).url(server)
        resp = make_request(url)
        if resp.status != 400:
            return ValidationFailure(
                url=url,
                expected="400 Bad Request",
                received=f"{resp.status} {resp.body.decode('utf8')}",
                details=f"Server did not return 400 for random quality",
            )
        return ValidationSuccess(details="Server returned 400 for random quality")

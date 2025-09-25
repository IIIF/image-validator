import random

from .test import (
    ValidationTest,
    TargetServer,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    ValidationFailure,
    ValidationSuccess,
    ImageAPIRequest,
    make_request,
    make_random_string,
)


class TestFormatErrorRandom(ValidationTest):
    name = "Random format gives 400"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        random.seed(31337)
        for _ in range(16):
            random_format = make_random_string(3)
            url = ImageAPIRequest.of(format=random_format).url(server)
            resp = make_request(url)
            if resp.status == 400:
                continue  # This is the expected outcome
            return ValidationFailure(
                url=url,
                expected="400 Bad Request",
                received=f"{resp.status} {resp.body.decode('utf8')}",
                details="Server did not return 400 for random format",
            )
        return ValidationSuccess(details="Server returned 400 for random formats")

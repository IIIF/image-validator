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
    make_request,
    make_random_string,
)


class SizeErrorRandomTest(ValidationTest):
    name = "Random size gives 400"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.SIZE
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        results = []
        for i in range(4):
            random_size = make_random_string(6)
            req = ImageAPIRequest.of(size=random_size)
            url = req.url(server)
            resp = make_request(url)
            if resp.status == 400:
                results.append(
                    ValidationSuccess(
                        details=f"Received 400 for random size='{random_size}'"
                    )
                )
            else:
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="400",
                        received=f"{resp.status}",
                        details=f"Did not receive 400 for random size='{random_size}'",
                    )
                )
        return results

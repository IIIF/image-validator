import random
import uuid

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


class ErrorRandomId(ValidationTest):
    name = "Random Identifier gives 404"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        # For reproducability
        random.seed(31337)
        random_id = uuid.uuid1()
        url = f"{server.base_url}/{random_id}/info.json"
        resp = make_request(url)
        if resp.status == 404:
            return ValidationSuccess(details="Returned 404 for random identifier")
        else:
            return ValidationFailure(
                url=url,
                expected="HTTP Status 404",
                received=f"HTTP Status {resp.status}",
                details="Got unexpected status code for random identifier",
            )

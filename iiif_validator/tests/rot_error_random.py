from urllib.error import HTTPError

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


class RotationErrorRandomTest(ValidationTest):
    name = "Random rotation gives 400"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        random_string = make_random_string(4)
        request = ImageAPIRequest.of(rotation=random_string)
        url = request.url(server)
        resp = make_request(url)
        if resp.status != 400:
            return ValidationFailure(
                url=url,
                expected="HTTP Status 400",
                received=f"HTTP Status {resp.status}",
                details=f"Server did not return an error for invalid rotation value '{random_string}'.",
            )
        else:
            return ValidationSuccess(
                details=f"Server correctly returned HTTP 400 for invalid rotation value '{random_string}'."
            )

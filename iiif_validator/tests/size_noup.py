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
)


class SizeNoUpTest(ValidationTest):
    name = "Size greater than 100% should only work with the ^ notation"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.SIZE
    versions = [IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        s = random.randint(1100, 2000)
        sizes_to_check = [f"{s},{s}", f",{s}", f"{s},", "pct:200", "!2000,3000"]

        results = []
        for size_str in sizes_to_check:
            req = ImageAPIRequest.of(size=size_str)
            url = req.url(server)
            resp = make_request(url)

            if resp.status != 200:
                results.append(
                    ValidationSuccess(
                        details=f"Upscaling size='{size_str}' failed as expected."
                    )
                )
            else:
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="Non-200 status code",
                        received=f"{resp.status}",
                        details=f"Retrieving upscaled image with size='{size_str}' succeeded but should have failed.",
                    )
                )
        return results

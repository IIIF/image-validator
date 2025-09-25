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
    get_expected_image,
    get_image,
    compare_rectangle,
)


class RegionPixels(ValidationTest):
    name = "Region specified by pixels"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.REGION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "regionByPx"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationFailure | ValidationSuccess]:
        random.seed(31337)  # for reproducibility
        expected = get_expected_image()
        results = []
        for _ in range(5):
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            region = f"{x * 100},{y * 100},100,100"
            req = ImageAPIRequest.of(region=region)
            rect = get_image(server, req)
            if compare_rectangle(expected, rect, x, y):
                results.append(ValidationSuccess(details=f"Region {region} matches"))
            else:
                results.append(
                    ValidationFailure(
                        url=req.url(server),
                        expected=f"Region {region} to match expected image region",
                        received="Region does not match expected image region",
                        details=f"Region {region} does not match",
                    )
                )
        return results

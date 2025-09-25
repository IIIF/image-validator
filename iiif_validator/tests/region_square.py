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
    compare_images,
)


class RegionSquare(ValidationTest):
    name = "Request a square region of the full image."
    compliance_level = {
        IIIFVersion.V3: ComplianceLevel.LEVEL_1,
        IIIFVersion.V2: ComplianceLevel.OPTIONAL,
    }
    category = TestCategory.REGION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "regionSquare"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        random.seed(31337)  # for reproducibility
        # Square region on full image should return the full validation image, since its width/height are equal
        expected = get_expected_image()
        req = ImageAPIRequest.of(region="square")
        square = get_image(server, req)
        if not compare_images(expected, square):
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Square region to match expected image",
                received="Square region did not match expected image",
                details="Server did not correctly handle region=square",
            )
        return ValidationSuccess(details="Server correctly handled region=square")

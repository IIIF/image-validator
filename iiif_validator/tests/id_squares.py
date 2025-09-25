from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    get_image,
    ImageAPIRequest,
    get_expected_image,
    compare_images,
)


class FullImageMatches(ValidationTest):
    name = "Correctly serves full image"
    compliance_level = ComplianceLevel.LEVEL_0
    category = TestCategory.INFO
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of()
        given_image = get_image(server, req)
        expected_image = get_expected_image()
        if compare_images(given_image, expected_image):
            return ValidationSuccess(details="Full image matches expected image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Full image to match expected image",
                received="Full image did not match expected image",
                details="Full image did not match expected image",
            )

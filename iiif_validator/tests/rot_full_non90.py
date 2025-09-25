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
    get_image,
    get_expected_image,
    compare_images,
)


class RotationFullNon90Test(ValidationTest):
    name = "Rotation by non 90 degree values"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "rotationArbitrary"

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        # Pick a random rotation that isn't a multiple of 90
        rot = random.randint(1, 359)
        while rot % 90 == 0:
            rot = random.randint(1, 359)

        expected_image = get_expected_image().rotate(rot)
        request = ImageAPIRequest.of(rotation=str(rot))
        actual_image = get_image(server, request)
        if not compare_images(
            actual_image.extract_area(300, 300, 300, 300),
            expected_image.extract_area(300, 300, 300, 300),
        ):
            url = request.url(server)
            return ValidationFailure(
                url=url,
                expected="A correctly rotated image.",
                received="An incorrectly rotated image.",
                details=f"Image rotated by {rot} degrees does not match the expected image.",
            )
        return ValidationSuccess(
            details=f"Server successfully returned an image for a non-90 degree rotation ({rot})."
        )

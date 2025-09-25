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


class RotationRegionNon90Test(ValidationTest):
    name = "Rotation of region by non 90 degree values"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "rotationArbitrary"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        results = []
        for i in range(2):
            rot = random.randint(1, 359)
            while rot % 90 == 0:
                rot = random.randint(1, 359)

            x = random.randint(0, 500)
            y = random.randint(0, 500)
            w = random.randint(100, 400)
            h = random.randint(100, 400)
            region_str = f"{x},{y},{w},{h}"

            request = ImageAPIRequest.of(region=region_str, rotation=str(rot))
            img_from_server = get_image(server, request)
            expected_rotated = get_expected_image().extract_area(x, y, w, h).rotate(rot)
            center_server = img_from_server.extract_area(w // 4, h // 4, w // 4, h // 4)
            center_expected = expected_rotated.extract_area(
                w // 4, h // 4, w // 4, h // 4
            )
            if not compare_images(center_server, center_expected):
                url = request.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="A correctly rotated region.",
                        received="An incorrectly rotated region.",
                        details=f"Image region {region_str} rotated by {rot} degrees does not match the expected image.",
                    )
                )
            else:
                results.append(
                    ValidationSuccess(
                        details=f"Server successfully returned an image for a non-90 degree rotation ({rot}) of region '{region_str}'."
                    )
                )
        return results

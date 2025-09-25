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


class RotationRegionBasicTest(ValidationTest):
    name = "Rotation of region by 90 degree values"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "rotationBy90s"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        results = []
        expected_img = get_expected_image()
        rotations = [90, 180, 270]

        for i in range(2):
            x = random.randint(0, 500)
            y = random.randint(0, 500)
            w = random.randint(100, 400)
            h = random.randint(100, 400)
            region_str = f"{x},{y},{w},{h}"

            for rot in rotations:
                request = ImageAPIRequest.of(region=region_str, rotation=str(rot))
                img_from_server = get_image(server, request)

                expected_region = expected_img.extract_area(x, y, w, h)
                if rot == 90:
                    expected_rotated_region = expected_region.rot90()
                elif rot == 180:
                    expected_rotated_region = expected_region.rot180()
                else:
                    expected_rotated_region = expected_region.rot270()

                expected_w, expected_h = (
                    expected_rotated_region.width,
                    expected_rotated_region.height,
                )
                if (
                    img_from_server.width != expected_w
                    or img_from_server.height != expected_h
                ):
                    url = request.url(server)
                    results.append(
                        ValidationFailure(
                            url=url,
                            expected=f"Image dimensions to be ({expected_w}, {expected_h})",
                            received=f"Image dimensions were ({img_from_server.width}, {img_from_server.height})",
                            details="Incorrect image dimensions for rotated region.",
                        )
                    )
                    continue

                if compare_images(img_from_server, expected_rotated_region):
                    results.append(
                        ValidationSuccess(
                            details=f"Rotation of region '{region_str}' by {rot} degrees was successful."
                        )
                    )
                else:
                    url = request.url(server)
                    results.append(
                        ValidationFailure(
                            url=url,
                            expected="A correctly rotated region.",
                            received="An incorrectly rotated region.",
                            details=f"Image region {region_str} rotated by {rot} degrees does not match the expected image.",
                        )
                    )
        return results

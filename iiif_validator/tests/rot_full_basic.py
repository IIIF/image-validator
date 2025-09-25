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


class RotationFullBasicTest(ValidationTest):
    name = "Rotation by 90 degree values"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "rotationBy90s"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        results = []
        expected_img = get_expected_image()
        # 0 degree rotation is implicitly tested elsewhere
        rotations = [90, 180, 270]
        for rot in rotations:
            request = ImageAPIRequest.of(rotation=str(rot))
            try:
                rotated_img = get_image(server, request)
                if rot == 180:
                    expected_rotated_img = expected_img.rot180()
                elif rot == 90:
                    expected_rotated_img = expected_img.rot90()
                else:
                    expected_rotated_img = expected_img.rot270()

                if compare_images(rotated_img, expected_rotated_img):
                    results.append(
                        ValidationSuccess(
                            details=f"Rotation by {rot} degrees was successful."
                        )
                    )
                else:
                    url = request.url(server)
                    results.append(
                        ValidationFailure(
                            url=url,
                            expected="A correctly rotated image.",
                            received="An incorrectly rotated image.",
                            details=f"Image rotated by {rot} degrees does not match the expected image.",
                        )
                    )
            except Exception as e:
                url = request.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="A valid image.",
                        received=f"An error: {e}",
                        details=f"Request for rotation {rot} failed.",
                    )
                )
        return results

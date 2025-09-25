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


class RotationMirror180Test(ValidationTest):
    name = "Mirroring plus 180 rotation"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "mirroring"

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        request = ImageAPIRequest.of(rotation="!180")
        try:
            transformed_img = get_image(server, request)
            expected_img = get_expected_image()

            if (
                transformed_img.width != expected_img.width
                or transformed_img.height != expected_img.height
            ):
                url = request.url(server)
                return ValidationFailure(
                    url=url,
                    expected=f"Image dimensions to be ({expected_img.width}, {expected_img.height})",
                    received=f"Image dimensions were ({transformed_img.width}, {transformed_img.height})",
                    details="Incorrect image dimensions for mirrored 180 degree rotation.",
                )

            # !180 is a vertical flip
            expected_transformed_img = expected_img.flip("vertical")

            if compare_images(transformed_img, expected_transformed_img):
                return ValidationSuccess(
                    details="Mirroring plus 180 degree rotation was successful."
                )
            else:
                url = request.url(server)
                return ValidationFailure(
                    url=url,
                    expected="A correctly transformed image (mirrored and rotated 180 degrees).",
                    received="An incorrectly transformed image.",
                    details="Image does not match the expected transformation.",
                )
        except Exception as e:
            url = request.url(server)
            return ValidationFailure(
                url=url,
                expected="A valid image.",
                received=f"An error: {e}",
                details="Request for mirrored 180 degree rotation failed.",
            )

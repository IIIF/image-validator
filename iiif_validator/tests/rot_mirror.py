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


class RotationMirrorTest(ValidationTest):
    name = "Mirroring"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.ROTATION
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "mirroring"

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        request = ImageAPIRequest.of(rotation="!0")
        try:
            transformed_img = get_image(server, request)
            expected_img = get_expected_image()

            # !0 is a horizontal flip
            expected_transformed_img = expected_img.flip("horizontal")

            if compare_images(transformed_img, expected_transformed_img):
                return ValidationSuccess(details="Mirroring was successful.")
            else:
                url = request.url(server)
                return ValidationFailure(
                    url=url,
                    expected="A correctly mirrored image.",
                    received="An incorrectly mirrored image.",
                    details="Image does not match the expected transformation.",
                )
        except Exception as e:
            url = request.url(server)
            return ValidationFailure(
                url=url,
                expected="A valid image.",
                received=f"An error: {e}",
                details="Request for mirrored rotation failed.",
            )

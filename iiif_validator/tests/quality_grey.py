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
    is_grayscale,
)


class GrayscaleImagesAreReturned(ValidationTest):
    name = "Grayscale image is returned when requesting quality=gray"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.QUALITY
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "gray"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(quality="gray")
        img = get_image(server, req)
        if not is_grayscale(img):
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Grayscale image",
                received=f"Non-grayscale image: {img.interpretation}",
                details="Server did not return a grayscale image when requesting quality=gray",
            )
        return ValidationSuccess(
            details="Server returned a grayscale image when requesting quality=gray"
        )

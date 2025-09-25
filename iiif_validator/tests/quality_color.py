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
)


class ColorImagesAreReturned(ValidationTest):
    name = "Color image is returned when requesting quality=color"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.QUALITY
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "color"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(quality="color")
        img = get_image(server, req)
        if img.interpretation not in ("srgb", "rgb"):
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Color RGB/sRGB image",
                received=f"Non-color image: {img.interpretation}",
                details="Server did not return a color image when requesting quality=color",
            )
        return ValidationSuccess(
            details="Server returned a color image when requesting quality=color"
        )

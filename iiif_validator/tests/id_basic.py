from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    ImageAPIRequest,
    get_image_format,
)


class ImageReturned(ValidationTest):
    name = "Image is returned"
    compliance_level = ComplianceLevel.LEVEL_0
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of()
        try:
            get_image_format(server, req)
            return ValidationSuccess(details="Successfully received full image")
        except Exception as e:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Full JPEG image",
                received=f"Invalid image due to error: {e}",
                details="Server did not return an image for the validation identifier",
            )

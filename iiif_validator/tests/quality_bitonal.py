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
    is_bitonal,
)


class BitonalImagesAreReturned(ValidationTest):
    name = "Bitonal image is returned when requesting quality=bitonal"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.QUALITY
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "bitonal"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(quality="bitonal")
        img = get_image(server, req)
        if not is_bitonal(img):
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="Bitonal image",
                received="Non-bitonal image",
                details="Server did not return a bitonal image when requesting quality=bitonal",
            )
        return ValidationSuccess(
            details="Server returned a bitonal image when requesting quality=bitonal"
        )

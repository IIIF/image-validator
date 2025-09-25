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


class FormatJPEG(ValidationTest):
    name = "JPEG format"
    compliance_level = ComplianceLevel.LEVEL_0
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="jpg")
        fmt = get_image_format(server, req)
        if fmt == "jpeg":
            return ValidationSuccess(details="Server returned a JPEG image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="JPEG image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a JPEG image",
            )

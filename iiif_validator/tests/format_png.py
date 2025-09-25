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


class FormatPNG(ValidationTest):
    name = "PNG format"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "png"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="png")
        fmt = get_image_format(server, req)
        if fmt == "png":
            return ValidationSuccess(details="Server returned a PNG image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="PNG image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a PNG image",
            )

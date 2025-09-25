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


class FormatGif(ValidationTest):
    name = "GIF format"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "gif"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="gif")
        fmt = get_image_format(server, req)
        if fmt == "gif":
            return ValidationSuccess(details="Server returned a GIF image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="GIF image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a GIF image",
            )

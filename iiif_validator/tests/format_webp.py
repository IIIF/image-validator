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


class FormatWebP(ValidationTest):
    name = "WebP format"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "webp"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="webp")
        fmt = get_image_format(server, req)
        if fmt == "webp":
            return ValidationSuccess(details="Server returned a WebP image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="WebP image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a WebP image",
            )

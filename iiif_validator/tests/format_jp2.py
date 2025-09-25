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


class FormatJP2(ValidationTest):
    name = "JP2 format"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "jp2"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="jp2")
        fmt = get_image_format(server, req)
        if fmt == "jp2k":
            return ValidationSuccess(details="Server returned a jp2k image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="jp2k image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a jp2k image",
            )

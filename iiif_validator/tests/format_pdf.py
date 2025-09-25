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


class FormatPDF(ValidationTest):
    name = "JPEG format"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "pdf"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="pdf")
        fmt = get_image_format(server, req)
        if fmt == "pdf":
            return ValidationSuccess(details="Server returned a PDF image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="PDF image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a PDF image",
            )

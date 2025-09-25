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


class FormatTIF(ValidationTest):
    name = "TIFF format"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.FORMAT
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "tif"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of(format="tif")
        fmt = get_image_format(server, req)
        if fmt == "tiff":
            return ValidationSuccess(details="Server returned a TIFF image")
        else:
            url = req.url(server)
            return ValidationFailure(
                url=url,
                expected="TIFF image",
                received=f"{fmt or '<none>'} image",
                details="Server did not return a TIFF image",
            )

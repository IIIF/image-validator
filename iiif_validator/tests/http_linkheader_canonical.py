from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    make_request,
    ImageAPIRequest,
    parse_rel_links,
)


class ImagesHaveCanonicalLinkHeader(ValidationTest):
    name = "Images have canonical Link header"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.HTTP
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "canonicalLinkHeader"

    @staticmethod
    def run(server: TargetServer) -> ValidationFailure | ValidationSuccess:
        req = ImageAPIRequest.of()
        url = req.url(server)
        img_resp = make_request(url)
        if img_resp.status != 200:
            return ValidationFailure(
                url=url,
                expected="HTTP Status 200",
                received=f"HTTP Status {img_resp.status}",
                details="Got unexpected status code when requesting image",
            )
        if "link" not in img_resp.headers:
            return ValidationFailure(
                url=url,
                expected='Link header with rel="canonical"',
                received="No Link header",
                details="No Link header present in image response",
            )
        link_header = img_resp.headers["link"]
        rel_links = parse_rel_links(link_header)
        if "canonical" not in rel_links:
            return ValidationFailure(
                url=url,
                expected='Link header with rel="canonical"',
                received=f'Link header without rel="canonical": {link_header}',
                details="No canonical link found in Link header",
            )
        return ValidationSuccess(details="Image response had canonical Link header")

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


class ImagesHaveProfileLinkHeader(ValidationTest):
    name = "Images have profile Link header"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.HTTP
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "profileLinkHeader"

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
        headers = img_resp.headers
        if "link" not in headers:
            return ValidationFailure(
                url=url,
                expected='Link header with rel="profile"',
                received="No Link header",
                details="No Link header present in image response",
            )
        link_header = headers["link"]
        rel_links = parse_rel_links(link_header)
        if "profile" not in rel_links:
            return ValidationFailure(
                url=url,
                expected='Link header with rel="profile"',
                received=f'Link header without rel="profile": {link_header}',
                details="No profile link found in Link header",
            )
        profile = rel_links["profile"][0]
        is_v2 = server.version == IIIFVersion.V2
        expected_profile_prefix = f"http://iiif.io/api/image/{'2' if is_v2 else '3'}/"
        if not profile.startswith(expected_profile_prefix):
            return ValidationFailure(
                url=url,
                expected=f"profile link starting with {expected_profile_prefix}",
                received=f"profile link: {profile}",
                details="Profile link header returned unexpected link.",
            )
        return ValidationSuccess(details="Image response had profile Link header")

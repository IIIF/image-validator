from urllib.request import HTTPRedirectHandler, build_opener

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    make_request,
)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Prevent redirection
        return None


opener = build_opener(NoRedirect)


class BaseUrlRedirect(ValidationTest):
    name = "Base URL Redirects"
    compliance_level = ComplianceLevel.LEVEL_1
    category = TestCategory.HTTP
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "baseUriRedirect"

    @staticmethod
    def run(server: TargetServer) -> ValidationSuccess | ValidationFailure:
        url = f"{server.base_url}/{server.validation_id}"
        expected = server.info_url()
        response = make_request(url, opener=opener)
        if response.status >= 300 and response.status < 400:
            new_url = response.headers.get("location", "")
            if new_url == expected:
                return ValidationSuccess(details=f"Redirected to {new_url}")
            else:
                return ValidationFailure(
                    url=url,
                    expected=f"Redirect to {expected}",
                    received=f"Redirect to {new_url}",
                    details="Invalid redirect location",
                )
        else:
            return ValidationFailure(
                url=url,
                expected="Redirect Status (3xx)",
                received=f"Status {response.status}",
                details="Did not receive a redirect status code",
            )

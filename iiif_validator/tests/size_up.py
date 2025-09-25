import random

from .test import (
    ValidationTest,
    ComplianceLevel,
    TestCategory,
    IIIFVersion,
    TargetServer,
    ValidationFailure,
    ValidationSuccess,
    ImageAPIRequest,
    get_image,
    get_expected_image,
    compare_images,
    make_request,
)


class SizeUpTest(ValidationTest):
    name = "Size greater than 100%"
    compliance_level = ComplianceLevel.OPTIONAL
    category = TestCategory.SIZE
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "sizeUpscaling"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        if server.version == IIIFVersion.V3:
            return SizeUpTest.run_v3(server)
        else:
            return SizeUpTest.run_v2(server)

    @staticmethod
    def run_v2(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        s = random.randint(1100, 2000)
        req = ImageAPIRequest.of(size=f",{s}")
        img = get_image(server, req)

        expected_size = (s, s)
        if img.size != expected_size:
            url = req.url(server)
            return [
                ValidationFailure(
                    url=url,
                    expected=f"Image size to be {expected_size}",
                    received=f"{img.size}",
                    details=f"Incorrect image size for upscaled size=',{s}'",
                )
            ]

        full_expected_img = get_expected_image()
        expected_img = full_expected_img.thumbnail_image(s, height=s, size="force")
        if not compare_images(img, expected_img):
            url = req.url(server)
            return [
                ValidationFailure(
                    url=url,
                    expected="Image content to match validation image",
                    received="Different image content",
                    details=f"Image content incorrect for upscaled size=',{s}'",
                )
            ]

        return [
            ValidationSuccess(
                details=f"Image size and content correct for upscaled size=',{s}'"
            )
        ]

    @staticmethod
    def run_v3(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        results = []
        s = random.randint(1100, 2000)

        # Test that upscaling without ^ fails
        req = ImageAPIRequest.of(size=f",{s}")
        url = req.url(server)
        resp = make_request(url)
        if resp.status != 200:
            results.append(
                ValidationSuccess(
                    details=f"Upscaling size=',{s}' failed as expected in v3 without '^'."
                )
            )
        else:
            results.append(
                ValidationFailure(
                    url=url,
                    expected="Non-200 status code",
                    received=f"{resp.status}",
                    details=f"Upscaling size=',{s}' should fail in v3 without '^'.",
                )
            )

        # Test that upscaling with ^ works
        sizes_to_check = {
            f"^{s},{s}": (s, s),
            f"^,{s}": (s, s),
            f"^{s},": (s, s),
            "^max": (1000, 1000),
            "^pct:200": (2000, 2000),
            "^!2000,500": (500, 500),
            "^!2000,3000": (2000, 2000),
        }

        full_expected_img = get_expected_image()
        for size_str, expected_size in sizes_to_check.items():
            req = ImageAPIRequest.of(size=size_str)
            img = get_image(server, req)

            if img.size != expected_size:
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected=f"Image size to be {expected_size}",
                        received=f"{img.size}",
                        details=f"Incorrect image size for upscaled size='{size_str}'",
                    )
                )
                continue

            expected_img = full_expected_img.thumbnail_image(
                expected_size[0], height=expected_size[1], size="force"
            )
            if not compare_images(img, expected_img):
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="Image content to match validation image",
                        received="Different image content",
                        details=f"Image content incorrect for upscaled size='{size_str}'",
                    )
                )
                continue

            results.append(
                ValidationSuccess(
                    details=f"Image size and content correct for upscaled size='{size_str}'"
                )
            )

        return results

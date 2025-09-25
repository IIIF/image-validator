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
)


class SizeRegionTest(ValidationTest):
    name = "Region at specified size"
    compliance_level = ComplianceLevel.LEVEL_2
    category = TestCategory.SIZE
    versions = [IIIFVersion.V2, IIIFVersion.V3]

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        full_expected_img = get_expected_image()
        results = []

        for i in range(5):
            s = random.randint(35, 90)
            x = random.randint(0, 9)
            y = random.randint(0, 9)

            region = f"{x * 100},{y * 100},100,100"
            size = f"{s},{s}"
            req = ImageAPIRequest.of(region=region, size=size)
            img = get_image(server, req)

            if img.width != s or img.height != s:
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected=f"({s}, {s})",
                        received=f"({img.width}, {img.height})",
                        details=f"Incorrect image size for region='{region}' and size='{size}'",
                    )
                )
                continue

            expected_region = full_expected_img.extract_area(x * 100, y * 100, 100, 100)
            expected_img = expected_region.thumbnail_image(s, height=s, size="force")

            if compare_images(img, expected_img):
                results.append(
                    ValidationSuccess(
                        details=f"Image content correct for region='{region}' and size='{size}'"
                    )
                )
            else:
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected=f"Image content to match validation image for region {x},{y}",
                        received="Different image content",
                        details=f"Image content incorrect for region='{region}' and size='{size}'",
                    )
                )
        return results

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


class SizePercentTest(ValidationTest):
    name = "Size specified by percent"
    compliance_level = {
        IIIFVersion.V3: ComplianceLevel.LEVEL_2,
        IIIFVersion.V2: ComplianceLevel.LEVEL_1,
    }
    category = TestCategory.SIZE
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = "sizeByPct"

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        results = []
        full_expected_img = get_expected_image()
        for i in range(4):
            s = random.randint(45, 75)
            req = ImageAPIRequest.of(size=f"pct:{s}")
            img = get_image(server, req)

            expected_size = (s * 10, s * 10)
            if (img.width, img.height) != expected_size:
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected=f"Image size to be {expected_size}",
                        received=f"{img.size}",
                        details=f"Incorrect image size for size='pct:{s}'",
                    )
                )
                continue

            expected_img = full_expected_img.thumbnail_image(
                s * 10, height=s * 10, size="force"
            )
            if not compare_images(img, expected_img):
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="Image content to match validation image",
                        received="Different image content",
                        details=f"Image content incorrect for size='pct:{s}'",
                    )
                )
                continue

            results.append(
                ValidationSuccess(
                    details=f"Image size and content correct for size='pct:{s}'"
                )
            )
        return results

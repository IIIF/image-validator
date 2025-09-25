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


class SizeWhTest(ValidationTest):
    name = "Size specified by w,h"
    compliance_level = {
        IIIFVersion.V3: ComplianceLevel.LEVEL_1,
        IIIFVersion.V2: ComplianceLevel.LEVEL_2,
    }
    category = TestCategory.SIZE
    versions = [IIIFVersion.V2, IIIFVersion.V3]
    extra_name = ["sizeByWh", "sizeAboveFull"]

    @staticmethod
    def run(server: TargetServer) -> list[ValidationSuccess | ValidationFailure]:
        random.seed(31337)
        results = []
        full_expected_img = get_expected_image()
        for i in range(4):
            w = random.randint(350, 750)
            h = random.randint(350, 750)
            req = ImageAPIRequest.of(size=f"{w},{h}")
            img = get_image(server, req)

            expected_size = (w, h)
            if (img.width, img.height) != expected_size:
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected=f"Image size to be {expected_size}",
                        received=f"{img.size}",
                        details=f"Incorrect image size for size='{w},{h}'",
                    )
                )
                continue

            expected_img = full_expected_img.thumbnail_image(w, height=h, size="force")
            if not compare_images(img, expected_img):
                url = req.url(server)
                results.append(
                    ValidationFailure(
                        url=url,
                        expected="Image content to match validation image",
                        received="Different image content",
                        details=f"Image content incorrect for size='{w},{h}'",
                    )
                )
                continue

            results.append(
                ValidationSuccess(
                    details=f"Image size and content correct for size='{w},{h}'"
                )
            )
        return results

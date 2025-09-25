from __future__ import annotations

import inspect
import importlib.resources
import json
import pkgutil
import random
import re
from collections import defaultdict
from enum import Enum
from urllib.request import urlopen, Request, OpenerDirector
from urllib.error import HTTPError
from typing import ClassVar, NamedTuple, Protocol, runtime_checkable

from pyvips import Image

#: Standard headers to use for requests, based on those
# used by the official validator.
HEADERS = {
    "Origin": "http://iiif.io/",
    "Referer": "http://iiif.io/api/image/validator",
    "User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1b3pre) Gecko/20081130 Minefield/3.1b3pre",
}
VIPS_FORMAT_BITS = {
    "uchar": 8,
    "char": 8,
    "ushort": 16,
    "short": 16,
    "uint": 32,
    "int": 32,
    "float": 32,
    "complex": 64,
    "double": 64,
    "dpcomplex": 128,
}


class TestCategory(str, Enum):
    INFO = "Info/Identifier"
    REGION = "Region"
    SIZE = "Size"
    ROTATION = "Rotation"
    QUALITY = "Quality"
    FORMAT = "Format"
    HTTP = "HTTP"


class ComplianceLevel(int, Enum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    OPTIONAL = 3

    @classmethod
    def from_profile(cls, profile: str | list[str | dict]) -> ComplianceLevel:
        if isinstance(profile, list):
            if not isinstance(profile[0], str):
                raise ValueError(
                    f"Invalid profile in info.json, first profile in a v2 `profile` array must be a string with an IIIF compliance level, was: {profile[0]!r}"
                )
            profile = profile[0]
        if profile == "level2" or profile == "http://iiif.io/api/image/2/level2.json":
            return cls.LEVEL_2
        elif profile == "level1" or profile == "http://iiif.io/api/image/2/level1.json":
            return cls.LEVEL_1
        elif profile == "level0" or profile == "http://iiif.io/api/image/2/level0.json":
            return cls.LEVEL_0
        raise ValueError(f"Unknown IIIF compliance level in profile: {profile!r}")


class IIIFVersion(str, Enum):
    V2 = "2.0"
    V3 = "3.0"


class ValidationSuccess(NamedTuple):
    success: bool = True
    details: str = "Validation successful"


class ValidationFailure(NamedTuple):
    expected: str
    received: str
    url: str
    success: bool = False
    details: str = "Validation failed"


@runtime_checkable
class ValidationTest(Protocol):
    name: ClassVar[str]
    category: ClassVar[TestCategory]
    compliance_level: ClassVar[ComplianceLevel | dict[IIIFVersion, ComplianceLevel]]
    versions: ClassVar[list[IIIFVersion]]
    extra_name: ClassVar[str | list[str] | None] = None

    @staticmethod
    def run(
        server: TargetServer,
    ) -> (
        ValidationSuccess
        | ValidationFailure
        | list[ValidationSuccess | ValidationFailure]
    ): ...


class TargetServer(NamedTuple):
    base_url: str
    validation_id: str
    version: IIIFVersion

    def info_url(self) -> str:
        return f"{self.base_url}/{self.validation_id}/info.json"

    def feature_set(self) -> ServerFeatures:
        return ServerFeatures.from_info_json(get_info_json(self))


class ServerFeatures(NamedTuple):
    version: IIIFVersion
    compliance_level: ComplianceLevel
    extra_qualities: list[str]
    extra_formats: list[str]
    extra_features: list[str]

    @classmethod
    def from_info_json(cls, info: dict) -> ServerFeatures:
        compliance = ComplianceLevel.from_profile(info["profile"])
        if "id" in info:
            version = IIIFVersion.V3
            extra_qualities = info.get("extraQualities", [])
            extra_formats = info.get("extraFormats", [])
            extra_features = info.get("extraFeatures", [])
        else:
            version = IIIFVersion.V2
            profile = info["profile"]
            extra_qualities = []
            extra_formats = []
            extra_features = []
            if isinstance(profile, list) and len(profile) > 1:
                for p in profile[1:]:
                    if isinstance(p, dict) and "qualities" in p:
                        extra_qualities.extend([q for q in p["qualities"]])
                    if isinstance(p, dict) and "formats" in p:
                        extra_formats.extend([f for f in p["formats"]])
                    if isinstance(p, dict) and "supports" in p:
                        extra_features.extend(p["supports"])
        return cls(
            version=version,
            compliance_level=compliance,
            extra_qualities=extra_qualities,
            extra_formats=extra_formats,
            extra_features=extra_features,
        )


class HttpResponse(NamedTuple):
    status: int
    body: bytes
    headers: dict[str, str]


class ImageAPIRequest(NamedTuple):
    region: str
    size: str
    rotation: str
    quality: str
    format: str

    @classmethod
    def of(
        cls,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: str = "default",
        format: str = "jpg",
    ) -> "ImageAPIRequest":
        return cls(
            region=region,
            size=size,
            rotation=rotation,
            quality=quality,
            format=format,
        )

    def to_v2(self) -> "ImageAPIRequest":
        size = self.size
        if size == "max":
            size = "full"
        return ImageAPIRequest(
            region=self.region,
            size=size,
            rotation=self.rotation,
            quality=self.quality,
            format=self.format,
        )

    def url(self, server: TargetServer) -> str:
        if server.version == IIIFVersion.V2:
            req = self.to_v2()
        else:
            req = self
        return f"{server.base_url}/{server.validation_id}/{req.region}/{req.size}/{req.rotation}/{req.quality}.{req.format}"


def make_request(
    req_or_url: str | Request,
    extra_headers: dict[str, str] = {},
    opener: OpenerDirector | None = None,
) -> HttpResponse:
    if isinstance(req_or_url, str):
        req = Request(req_or_url, headers={**HEADERS, **extra_headers})
    else:
        req = req_or_url
        for k, v in HEADERS.items():
            req.add_header(k, v)
    try:
        if opener:
            resp = opener.open(req)
        else:
            resp = urlopen(req)
        return HttpResponse(
            resp.status, resp.read(), {k.lower(): v for k, v in resp.headers.items()}
        )
    except HTTPError as e:
        return HttpResponse(
            e.code, e.read(), {k.lower(): v for k, v in e.headers.items()}
        )


def get_info_json(server: TargetServer) -> dict:
    url = f"{server.base_url}/{server.validation_id}/info.json"
    response = make_request(url)
    if response.status != 200:
        raise Exception(f"Failed to fetch info.json: {response.status}")
    return json.loads(response.body)


def get_image(server: TargetServer, request: ImageAPIRequest) -> Image:
    if server.version == IIIFVersion.V2:
        request = request.to_v2()

    url = f"{server.base_url}/{server.validation_id}/{request.region}/{request.size}/{request.rotation}/{request.quality}.{request.format}"
    response = make_request(url)
    if response.status != 200:
        raise Exception(f"Failed to fetch image: {response.status}")
    return Image.new_from_buffer(response.body, "")


def get_expected_image() -> Image:
    img_path = importlib.resources.files("iiif_validator") / "validation_image.png"
    return Image.new_from_file(str(img_path))


def compare_rectangle(reference: Image, rect: Image, x: int, y: int) -> bool:
    if rect.width != 100 or rect.height != 100:
        return False
    # Omit 13 pixel border and compare a 74x74 square in the center
    square_reference = reference.extract_area(x * 100 + 13, y * 100 + 13, 74, 74)
    square_rect = rect.extract_area(13, 13, 74, 74)
    diff = (square_reference - square_rect).abs().max()
    # Allow minor differences due to compression
    return diff < 6


def compare_images(
    given: Image, expected: Image, x: int | None = None, y: int | None = None
) -> bool:
    # For similarity, subtract the two images and get the average color value
    # since the reference image has no blacks, the closer we are to black
    # the better the match. We'll never get full black due to compression
    # artifacts, but 6 is a good threshold
    if x is not None and y is not None:
        # Omit 13 pixel border and compare a 74x74 square in the center
        square_given = given.extract_area(x * 100 + 13, y * 100 + 13, 74, 74)
        square_expected = expected.extract_area(x * 100 + 13, y * 100 + 13, 74, 74)
        diff = (square_given - square_expected).abs().avg()
    else:
        diff = (given - expected).abs().avg()
    # Allow minor differences due to compression
    return diff < 6


def get_image_format(server: TargetServer, request: ImageAPIRequest) -> str:
    img = get_image(server, request)
    loader = img.get("vips-loader")
    return loader[: loader.index("load")]


def make_random_string(length: int) -> str:
    return (
        "".join(chr(random.randint(48, 122)) for _ in range(length))
        .replace("?", "$")
        .replace("#", "$")
        .replace("/", "$")
    )


def parse_rel_links(header: str) -> dict[str, list[str]]:
    links = defaultdict(lambda: [])
    for link in re.finditer(r'<([^>]+)>;\s*rel="([^"]+)"\s*([,]*)', header):
        uri = link.group(1)
        rel = link.group(2)
        links[rel].append(uri)
    return links


def is_bitonal(img: Image, min_pct: float = 0.99) -> bool:
    if img.hasalpha():
        img = img[:-1]

    black = [0] * img.bands
    white = [(1 << VIPS_FORMAT_BITS[img.format]) - 1] * img.bands

    # Mask of pixels that are either black or white, values
    # will be 0 (false) or 255 (true)
    mask = ((img == black) | (img == white)).bandand()
    return mask.avg() / 255


def is_grayscale(img: Image, min_pct: float = 0.99) -> bool:
    if img.hasalpha():
        img = img[:-1]
    if img.bands == 1 or img.interpretation in ("grey16", "b-w"):
        return True

    # Mask of pixels where R == G == B, values will be 0 (false) or 255 (true)
    mask = (img[0] == img[1]) & (img[1] == img[2])
    return mask.avg() / 255 >= min_pct


def get_tests(iiif_version: IIIFVersion = IIIFVersion.V3) -> list[type[ValidationTest]]:
    assert __package__ is not None, "This function must be called from within a package"
    top_level_pkg = __package__.split(".")[0]
    tests_pkg_name = f"{top_level_pkg}.tests"

    tests_pkg = importlib.import_module(tests_pkg_name)

    implementations = []
    package_path = tests_pkg.__path__
    package_name = tests_pkg.__name__

    for module_info in pkgutil.walk_packages(
        path=package_path, prefix=f"{package_name}."
    ):
        if module_info.name == __name__:
            continue
        module = importlib.import_module(module_info.name)
        for _, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__ == module.__name__ and (
                (ValidationTest in member.mro() or isinstance(member, ValidationTest))
                and iiif_version in member.versions
            ):
                implementations.append(member)

    return implementations

from __future__ import absolute_import

import re
import six
import logging

from sentry.stacktraces.processing import find_stacktraces_in_data
from sentry.utils.safe import get_path

logger = logging.getLogger(__name__)

# Regex to parse OS versions from a minidump OS string.
VERSION_RE = re.compile(r'(\d+\.\d+\.\d+)\s+(.*)')

# Regex to guess whether we're dealing with Windows or Unix paths.
WINDOWS_PATH_RE = re.compile(r'^([a-z]:\\|\\\\)', re.IGNORECASE)

# Event platforms that could contain native stacktraces
NATIVE_PLATFORMS = ('cocoa', 'native')

# Debug image types that can be handled by the symbolicator
NATIVE_IMAGE_TYPES = (
    'apple',     # Deprecated in favor of "macho"
    'symbolic',  # Generic if type is not known
    'elf',       # Linux
    'macho',     # macOS, iOS
    'pe'         # Windows
)


def is_native_platform(platform):
    return platform in NATIVE_PLATFORMS


def is_native_image(image):
    return bool(image) \
        and image.get('type') in NATIVE_IMAGE_TYPES \
        and image.get('image_addr') is not None \
        and image.get('image_size') is not None \
        and (image.get('debug_id') or image.get('id') or image.get('uuid')) is not None


def native_images_from_data(data):
    return get_path(data, 'debug_meta', 'images', default=(),
                    filter=is_native_image)


def is_native_event(data):
    if is_native_platform(data.get('platform')):
        return True

    for stacktrace in find_stacktraces_in_data(data):
        if any(is_native_platform(x) for x in stacktrace.platforms):
            return True

    return False


def image_name(pkg):
    if not pkg:
        return pkg
    split = '\\' if WINDOWS_PATH_RE.match(pkg) else '/'
    return pkg.rsplit(split, 1)[-1]


def get_sdk_from_event(event):
    sdk_info = get_path(event, 'debug_meta', 'sdk_info')
    if sdk_info:
        return sdk_info

    os = get_path(event, 'contexts', 'os')
    if os and os.get('type') == 'os':
        return get_sdk_from_os(os)


def get_sdk_from_os(data):
    if data.get('name') is None or data.get('version') is None:
        return

    try:
        version = six.text_type(data['version']).split('-', 1)[0] + '.0' * 3
        system_version = tuple(int(x) for x in version.split('.')[:3])
    except ValueError:
        return

    return {
        'sdk_name': data['name'],
        'version_major': system_version[0],
        'version_minor': system_version[1],
        'version_patchlevel': system_version[2],
        'build': data.get('build'),
    }


def signal_from_data(data):
    exceptions = get_path(data, 'exception', 'values', filter=True)
    signal = get_path(exceptions, 0, 'mechanism', 'meta', 'signal', 'number')
    if signal is not None:
        return int(signal)

    return None

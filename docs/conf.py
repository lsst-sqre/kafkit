from documenteer.conf.guide import *


linkcheck_anchors_ignore = [
    r"^!",
    r"compatibility-types",
    r"wire-format",
    r"subject-name-strategy",
    r"errors",
]

napoleon_type_aliases = {
    # resolves confusion between sans-io version of impl specific version
    "RegistryApi": "kafkit.registry.sansio.RegistryApi",
    # Napoleon doesn't resolve whats under TYPE_CHECKING
    "ClientSession": "aiohttp.ClientSession",
    "optional": "typing.Optional",
}

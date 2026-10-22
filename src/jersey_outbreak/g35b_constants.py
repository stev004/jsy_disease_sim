"""Independent frozen G35-B controls; never populated from a supplied config.

Ridge lineage source: owner-clarification-1, item 1. Scientific controls and
logical hashes: frozen predeclaration §§3, 6–9. Later arms are declarations only.
"""

from __future__ import annotations

PREDECLARATION_PATH = "docs/research/v1_3/2026-10-22-g35b-predeclaration.md"
PREDECLARATION_SHA256 = "2e8358abd9e275a5cf04a58b4ad76313c10964f2da06d46cd0f8a7190733216e"
# Exact LF bytes of the config with B/i/ii/iii implementation metadata.
CONFIG_SHA256 = "4259c45f01cf122521f6853dba5059415a0ca6317a02d3f883be18e3263105d0"
RIDGE_PATH = "docs/research/v1_3/2026-09-29-phase0b-ridge-diagnostic-EXPLORATORY.md"
RIDGE_SHA256 = "8cf4c76612434cbd90c5de4ca9dfd1326422b94a72bd4a63ccff71e95f34908a"
CLARIFICATION_PATH = "docs/research/v1_3/2026-10-22-g35b-owner-clarification-1.md"
CLARIFICATION_SHA256 = "2b1d4a5ee6bbab965a32e2abcdc4d00cab769d7d994a015fcf3bf5b0df0346d5"
OWNER_RULING_SHA256 = "f84738a9594312f3371f4bb469c5cfaafed265dc5d233ee34f1f0be564d99643"
EARLIER_SEED_SETS = (
    tuple(range(42001, 42006)),
    tuple(range(52001, 52006)),
    tuple(range(43001, 43004)),
    tuple(range(53001, 53004)),
    tuple(range(62001, 62006)),
    tuple(range(72001, 72006)),
    tuple(range(63001, 63004)),
    tuple(range(73001, 73004)),
    tuple(range(81001, 81007)),
    tuple(range(91001, 91004)),
)
TARGET_PROCESS_SEEDS = tuple(range(82001, 82011))
TARGET_OBSERVATION_SEEDS = tuple(range(92001, 92011))
TARGET_SEROSURVEY_SEEDS = tuple(range(94001, 94011))
CANDIDATE_BATCHES = (
    ("A", (83001, 83002, 83003), (93001, 93002, 93003)),
    ("B_prime", (83004, 83005, 83006), (93004, 93005, 93006)),
    ("C_prime", (83007, 83008, 83009), (93007, 93008, 93009)),
    ("D_prime", (83010, 83011, 83012), (93010, 93011, 93012)),
)
FIT_SEROSURVEY_SEEDS = (95001, 95002, 95003)
# name, truth, grid, tolerance, bias limit: finite decimal strings, §3.
DIMENSIONS = (
    ("beta", "0.08", ("0.04", "0.06", "0.08", "0.10", "0.12"), "0.02", "0.01"),
    ("inoculation_day_offset", "2", ("0", "1", "2", "3", "4"), "1", "0.5"),
    (
        "symptomatic_detection_probability",
        "0.75",
        ("0.50", "0.625", "0.75", "0.875", "1.00"),
        "0.125",
        "0.0625",
    ),
    (
        "asymptomatic_detection_probability",
        "0.25",
        ("0.10", "0.175", "0.25", "0.325", "0.40"),
        "0.075",
        "0.0375",
    ),
)
# arm, R, latent days, dates, cells, NEW latent, transforms, samples, builds.
ARM_CAPS = (
    ("B", 3, 30, 34, 625, 85, 1885, 0, 13),
    ("i", 12, 30, 34, 625, 225, 5625, 0, 9),
    ("ii", 3, 49, 53, 625, 85, 1885, 0, 0),
    ("iii", 3, 30, 34, 625, 0, 0, 85, 0),
)
TOTAL_CAPS = (2500, 395, 9395, 85, 22)
# M2 / M3 / M4, transcribed from the committed frozen §8 final-primary rows.
PROCESS_HASHES: dict[int, tuple[str, str, str]] = {
    82001: (
        "29be3731586fcb88f93edd646c9db8aae1057dc11f7f18a947f67b9ad01f3e19",
        "473a4901f68338392a74c0b3f2df23518f9df1a1c09f01d7508d827e3ebb3f75",
        "0315d935b99761abdfb79eddfd66077d300e056379f47c2af69c033d12779bab",
    ),
    82002: (
        "0fcfa17427521af536c7fc7eddb247b1665acba2ca802be0cb7c9951d7e0b7ea",
        "709c123cffb0a8dc8c8fdf79f83347fd038bc1fe2390f85087ebba2a92b1a213",
        "1fa4eb9b9f80c013d6c8ca97e72d87d6aaa101e8f1812ec6026af0c26dfc2bc5",
    ),
    82003: (
        "2e2abec14b86855210b5db41a0f32f1ef26401dcf4a9df87c26460ec78f51c3d",
        "c8c73f50e6f9db8abcc165bf292390b1067d824a255fb94a0777f92290514233",
        "9f8211d43f9352e6b1c716988695839a7ba10c1781173a6071d7914edd73acfc",
    ),
    82004: (
        "4c91addee491fc2ce5efe84b21a3f18ad2822d852f97134f5cec9382835aa2d7",
        "de4114c92f4ed53e33b85f52086ad21797acebbdb1acc6ba25fe6240bb9270aa",
        "121b6ff4756ed002cc12865f53e47cdf0048e95391ec91b548011f3f9abcc1ca",
    ),
    82005: (
        "366d6486a4790093e9845b31efc0c79a530fdb22d607db24ac905160b6ddebf2",
        "18d02e1413e81f9bdb295a2dc9a86ca8d005d4ad16a55e98351c3edcb2365bcd",
        "7b7719d020070878215ddce776005878f281146be7f9c69bf78d2c2fd30694e0",
    ),
    82006: (
        "9a55c6f251af65bf70694b04a1d4030530ff481828eb1435243fc2c6701cfa0d",
        "18ecca09b73e9711ca71b52d36b42bc7bf906b22a382fcd53902a16e25d5116b",
        "0919bc563350669a31672a685324205c19b8c875274e778b27ea572b85b1399d",
    ),
    82007: (
        "f857b9bee85696f7d1ddb999e5e92bf9e8d8ef078a050ee853fffac37580b01c",
        "202589ef822273969468ef1b5336a758f7e9738692455ef8f4bf11d21065f258",
        "ba70c35a4afc547c4ce9960dff3a39907dcc128e1a87214c72d298a3c82ad6bb",
    ),
    82008: (
        "2e28de397db5a765e0c6484ef4dbe98aaec638eb58f62488656b2b113a36e60e",
        "3d0ec001d43734484b31d8a796541fa2958b08ce8e2a2bba13fbb3f6fffe0542",
        "beb428c9d6a1420444bd60dcc5cb9fdf4e6cad6785672834bc4fc9c262a8c405",
    ),
    82009: (
        "a7a472c8e974e065ab8b80d3a638d7b45802dfd03a4c9e238cf671d1cacec24c",
        "583502f9615196e331b297f062cc534dd78132720260f3159847f0dbbf7eb252",
        "be0013d9a4a1899316693c1d76a55254ed9b2cd7e4fd0c9fc680158fa8e71e50",
    ),
    82010: (
        "beba6277bc836401f506e813d38915ada5932896122bd331882b63f0952aebf1",
        "3df598689ee901d22aac5a0b325e5667ae9e6bfa570a38d7aad79a97176abd9b",
        "a277760a2224db3bab4986de9a15ed302c9f3a15b334128209ca3e3cda4c3f52",
    ),
    83001: (
        "cd9b3810b7f82c7acc98afb308f292a7a31e9f8439e9e48c4fc9719e8ebf27db",
        "e50724db82ac5475249d7adfa0f779f5e408df78de3f024fc722564269cfb66d",
        "448920b78f1effdca6236389a14b241d8352a806e4f5f352ec03e0ecba510bd5",
    ),
    83002: (
        "18576334ad6bbe771a7cbf2efdf44344afd71b104ecdc8125ad2884d22ef53ea",
        "109bb47e8eafdc912ed7963c316384db5277b36abb088c3570d5d258d0db0df8",
        "be6d085971128ec37d95bc92e7b75f3edebe8e7daae78a6359023d2189a4e977",
    ),
    83003: (
        "1942929d096e8999dd335d39893f16926bd40aab4b9971b610d3848bc2286617",
        "287fd4b9f23b5bf939658d8793b3067f49468992d49426e81b2205711112209f",
        "6b614984120615ccd78d44aec9c4302bfe691fadc93b6ec93bf1337b79bab0fc",
    ),
    83004: (
        "d791b1cccb554c02cffd88d0887142694e2e64d440fa2bf4aa7bec6bf28e4525",
        "a388e9ace447324fad942d6b716d882e9e8a2a69abf1cf5dd1a44e03eb363e0e",
        "79fcdd9aa3ac2d9171d3a81ce70e2862c8dc0f420bc1bd2b49200ae04728cacc",
    ),
    83005: (
        "cdf5d4ef0c1fc113a9c379da9db8dcf5080b8ff2dda0f8f785b8dfa1671a706e",
        "601866c328f023292ac4d488ce5496161f7afd9b018fd9e1fa85724401aed3c3",
        "cd94b37f3a67a48b3cb3d99bd6f3547aed9632e16abac7bb4d309087c673af81",
    ),
    83006: (
        "b590f15749a0b9536be85cd646fc6e7cf867baa74f310580fd4c4673b001f5ef",
        "d2608c75efe50704ab46c3d072b56b287726d77494b8fe2db6f3a17188030f1c",
        "0af0c44893a755363caeec5474be033c92ebc55d511b735cc7ab98450a7a9acb",
    ),
    83007: (
        "0d51d1f8b9ae6a2ebb4a44935c4d02d99eb309f4a70e50a563ad7aae0d39808e",
        "bd40941d56e8f76fb2175e2a430227f283698cda137bcb4e9a7b03e002d163ff",
        "8ed53ac6aa78a9fca98004b425e91d2a4c21f0f60e0f5a2ece717a76621cd95b",
    ),
    83008: (
        "7453dbf5d3eea512497c995c92f64527534a1c80a0e1d9b7df165affd9587ebe",
        "446e5f5722808f335a9c88d7ee3eec4b8242bcb7616d525c9f7865f70472c500",
        "65d1bff09584abb3528d0356a5b5ae7507c2d38f54b2288a8aca97a529d32426",
    ),
    83009: (
        "4c91becbd1d218f4f9c6b76a7e203714f0aefcba5cdf6346f1cc7d9a2591b7ff",
        "6538342b86913f0143b9c39c914fbc18f9cd0a2ba69b4f63b95c793cef91d49d",
        "5e3562d890207aab01cb3072baa8bdd13654001db93c45b304192c5dab1b9fee",
    ),
    83010: (
        "c2d6c43a84cbabc7704482e646535bad0613e378a8ab628114117717093b9752",
        "d0bb98138cb48c04ecfabe8e32d06a0230fec6fd041de391bbed23044446b036",
        "f21ba813a10683ab8ac7ee60901f4905da951052053a581dd7764d4c362fb224",
    ),
    83011: (
        "b9195f7493f6d647d59e92274030c5723d4c0595ee95c2e144fdc8c8b69fbfe7",
        "8e2f646d05eb1de06f532bc0980e2d75b88c61b12ad095386bf5f9b7b3986107",
        "42ee89e0306f1d0c699bf4dce1dc7a70aca4df9fd6b9dc285ef301c51750e617",
    ),
    83012: (
        "969a04909ef4d6385258ab3256e83554aa95d426898547f6df1b0e2486ab6d44",
        "a6f42c1dbdc8eccd715e041d6c80771534bf22b73cf76a995fe6793e78e04f25",
        "3b43297015067c60e3a8e32e6e5181700d3070360c2a98a00cf370db04e8f3b4",
    ),
}

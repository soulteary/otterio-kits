Reports cover the six go.work release modules independently: highwayhash, sha256-simd, simdjson-go, sio, crc64nvme, md5-simd. Auxiliary md5-simd/_gen and simdjson-go/benchmarks remain covered by the existing tooling checks, not library coverage.

Each module is tested with GOWORK=off, race, atomic coverage and -count=1. simdjson-go requires actual AVX2/CLMUL CPU support and retains its full corpus plus a 20-minute package timeout. Existing native cross-platform, noasm, architecture, fuzz, benchmark and security gates remain enabled. No new coverage/score floor is introduced.

README shows each module's actual coverage and score badge, without inventing a combined cross-module grade. PR/ordinary coverage jobs only upload evidence. Tag/release/manual publishers collect all six successful module artifacts and only update 30 report files when the tested SHA is still default-branch HEAD. Failed or cancelled modules cannot write reports.

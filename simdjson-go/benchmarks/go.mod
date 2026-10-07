// Modified by otterio-kits maintainers on 2026-10-08:
// updated module paths and aligned benchmark dependencies with the parent module.
module github.com/soulteary/otterio-kits/simdjson-go/benchmarks

go 1.17

require (
	github.com/buger/jsonparser v1.1.1
	github.com/json-iterator/go v1.1.12
	github.com/klauspost/compress v1.15.15
	github.com/soulteary/otterio-kits/simdjson-go v0.0.0-00010101000000-000000000000
)

replace github.com/soulteary/otterio-kits/simdjson-go => ../

require (
	github.com/klauspost/cpuid/v2 v2.2.3 // indirect
	github.com/modern-go/concurrent v0.0.0-20180228061459-e0a39a4cb421 // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	golang.org/x/sys v0.0.0-20220704084225-05e143d24a9e // indirect
)

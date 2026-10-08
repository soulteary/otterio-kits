// Modified by otterio-kits maintainers on 2026-10-08:
// updated module paths and aligned benchmark dependencies with the parent module.
// Updated by otterio-kits maintainers on 2026-10-08: aligned Go 1.27.1 and refreshed dependencies.
module github.com/soulteary/otterio-kits/simdjson-go/benchmarks

go 1.27.1

require (
	github.com/buger/jsonparser v1.6.1
	github.com/json-iterator/go v1.1.12
	github.com/klauspost/compress v1.20.1
	github.com/soulteary/otterio-kits/simdjson-go v0.0.0-00010101000000-000000000000
)

replace github.com/soulteary/otterio-kits/simdjson-go => ../

require (
	github.com/klauspost/cpuid/v2 v2.4.0 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	golang.org/x/sys v0.48.0 // indirect
)

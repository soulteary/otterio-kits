// Modified by otterio-kits maintainers on 2026-10-11: remove the inherited ARM64 backend and use Go crypto/sha256.
// Minio Cloud Storage, (C) 2021 Minio, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

// Modified by otterio-kits maintainers on 2026-10-08:
// require a compiled assembly implementation before selecting CPU acceleration.

package sha256

import (
	"runtime"

	"github.com/klauspost/cpuid/v2"
)

var (
	hasIntelSha = assemblyAvailable && runtime.GOARCH == "amd64" && cpuid.CPU.Supports(cpuid.SHA, cpuid.SSSE3, cpuid.SSE4)
	hasAvx512   = assemblyAvailable && runtime.GOARCH == "amd64" && cpuid.CPU.Supports(cpuid.AVX512F, cpuid.AVX512DQ, cpuid.AVX512BW, cpuid.AVX512VL)
)

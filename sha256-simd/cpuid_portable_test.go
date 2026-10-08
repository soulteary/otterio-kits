//go:build appengine || noasm || (!amd64 && !arm64) || !gc

// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package sha256

import (
	"testing"

	"github.com/klauspost/cpuid/v2"
)

func TestCPUFeaturesWithoutAssembly(t *testing.T) {
	// Keep this test serial and restore the CPU information before other tests.
	// A noasm build must stay portable even when every acceleration flag is set.
	savedCPU := cpuid.CPU
	defer func() { cpuid.CPU = savedCPU }()
	cpuid.CPU.Enable(cpuid.SHA, cpuid.SHA2, cpuid.SSSE3, cpuid.SSE4,
		cpuid.AVX512F, cpuid.AVX512DQ, cpuid.AVX512BW, cpuid.AVX512VL)
	if hasIntelSha || hasAvx512 || hasArmSha2() {
		t.Fatal("CPU features enabled an assembly backend that is absent from this build")
	}
	if _, ok := New().(*digest); ok {
		t.Fatal("New selected a custom assembly digest in a portable build")
	}
}

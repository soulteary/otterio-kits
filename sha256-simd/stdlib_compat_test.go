// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0
package sha256

import (
	"bytes"
	stdsha "crypto/sha256"
	"encoding"
	"fmt"
	"hash"
	"runtime"
	"testing"
)

// Test the retained digest directly to cover states written before replacement.
func TestStdlibStateCompatibility(t *testing.T) {
	for _, n := range []int{0, 1, 55, 56, 63, 64, 65, 127, 128, 129, 1024, 65536} {
		t.Run(fmt.Sprint(n), func(t *testing.T) {
			p := make([]byte, n)
			for i := range p {
				p[i] = byte(i*37 + 11)
			}
			want := stdsha.Sum256(p)
			if Sum256(p) != want {
				t.Fatal("one-shot digest")
			}
			for _, cut := range []int{0, n / 2, n} {
				old := new(digest)
				old.Reset()
				standard := stdsha.New()
				old.Write(p[:cut])
				standard.Write(p[:cut])
				a, err := old.MarshalBinary()
				if err != nil {
					t.Fatal(err)
				}
				b, err := standard.(encoding.BinaryMarshaler).MarshalBinary()
				if err != nil {
					t.Fatal(err)
				}
				if !bytes.Equal(a, b) {
					t.Fatalf("state at %d", cut)
				}
				for _, pair := range []struct {
					newHash func() hash.Hash
					state   []byte
				}{
					{func() hash.Hash { d := new(digest); d.Reset(); return d }, b},
					{stdsha.New, a}, {New, a},
				} {
					h := pair.newHash()
					if err := h.(encoding.BinaryUnmarshaler).UnmarshalBinary(pair.state); err != nil {
						t.Fatal(err)
					}
					h.Write(p[cut:])
					if !bytes.Equal(h.Sum([]byte{1, 2}), append([]byte{1, 2}, want[:]...)) {
						t.Fatal("resumed digest/prefix")
					}
					if !bytes.Equal(h.Sum(nil), want[:]) {
						t.Fatal("Sum changed state")
					}
					h.Reset()
					empty := stdsha.Sum256(nil)
					if !bytes.Equal(h.Sum(nil), empty[:]) {
						t.Fatal("Reset")
					}
				}
			}
		})
	}
}

func TestARM64UsesStdlib(t *testing.T) {
	if runtime.GOARCH != "arm64" {
		t.Skip("ARM64 dispatch")
	}
	if _, custom := New().(*digest); custom {
		t.Fatal("custom ARM64 digest")
	}
	if assemblyAvailable || hasIntelSha || hasAvx512 {
		t.Fatal("kit assembly selected")
	}
}

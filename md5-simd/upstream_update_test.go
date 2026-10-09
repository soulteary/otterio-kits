// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package md5simd

import (
	"bytes"
	"crypto/md5"
	"fmt"
	"testing"
)

func TestServerOptionsAndHasherReuse(t *testing.T) {
	for _, avx512 := range []bool{false, true} {
		t.Run(fmt.Sprint(avx512), func(t *testing.T) {
			server := NewServerWithOptions(ServerOptions{UseAVX512: avx512})
			defer server.Close()
			for round := 0; round < 20; round++ {
				for _, h := range []Hasher{server.NewHash(), StdlibHasher()} {
					for _, size := range []int{0, 1, 55, 56, 63, 64, 65, 32768, 32769} {
						h.Reset()
						input := bytes.Repeat([]byte{byte(round + size)}, size)
						for pos := 0; pos < len(input); {
							end := pos + 37
							if end > len(input) {
								end = len(input)
							}
							if _, err := h.Write(input[pos:end]); err != nil {
								t.Fatal(err)
							}
							pos = end
						}
						want := md5.Sum(input)
						if got := h.Sum(nil); !bytes.Equal(got, want[:]) {
							t.Fatalf("round=%d size=%d: got %x want %x", round, size, got, want)
						}
					}
					h.Close()
				}
			}
		})
	}
}

//go:build amd64 && !appengine && !noasm && gc

// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package md5simd

import (
	"crypto/md5"
	"encoding/binary"
	"fmt"
	"testing"
)

func TestBlockScalarMatchesStandardLibrary(t *testing.T) {
	for _, size := range []int{0, 1, 55, 56, 63, 64, 65, 127, 128, 129, 4096} {
		t.Run(fmt.Sprint(size), func(t *testing.T) {
			input := make([]byte, size)
			for i := range input {
				input[i] = byte(i*37 + size)
			}
			want := md5.Sum(input)
			padded := append([]byte(nil), input...)
			padded = append(padded, 0x80)
			for len(padded)%64 != 56 {
				padded = append(padded, 0)
			}
			padded = binary.LittleEndian.AppendUint64(padded, uint64(size)*8)
			digest := [4]uint32{0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476}
			blockScalar(&digest, padded)
			var got [16]byte
			for i, word := range digest {
				binary.LittleEndian.PutUint32(got[i*4:], word)
			}
			if got != want {
				t.Fatalf("MD5(%d bytes) = %x, want %x", size, got, want)
			}
		})
	}
}

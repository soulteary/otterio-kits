// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package simdjson

import (
	"math"
	"reflect"
	"testing"
)

func TestArrayAsIntegerRetainsUnsignedValues(t *testing.T) {
	// Iter.SetUint can produce a uint tag even when its value fits in int64.
	// Construct the tape directly so this regression also runs without SIMD.
	array := Array{tape: ParsedJson{Tape: []uint64{
		uint64(TagUint) << JSONTAGOFFSET, 0,
		uint64(TagUint) << JSONTAGOFFSET, 42,
		uint64(TagUint) << JSONTAGOFFSET, math.MaxInt64,
		uint64(TagArrayEnd) << JSONTAGOFFSET,
	}}}
	got, err := array.AsInteger()
	want := []int64{0, 42, math.MaxInt64}
	if err != nil || !reflect.DeepEqual(got, want) {
		t.Fatalf("AsInteger() = %v, %v; want %v, nil", got, err, want)
	}
}

func TestArrayAsIntegerRejectsUnsignedOverflow(t *testing.T) {
	array := Array{tape: ParsedJson{Tape: []uint64{
		uint64(TagUint) << JSONTAGOFFSET, uint64(math.MaxInt64) + 1,
		uint64(TagArrayEnd) << JSONTAGOFFSET,
	}}}
	if _, err := array.AsInteger(); err == nil {
		t.Fatal("AsInteger accepted a uint value outside the int64 range")
	}
}

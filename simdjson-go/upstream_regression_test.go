// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package simdjson

import "testing"

func TestObjectForEachSkipsUnselectedValuesWithoutSIMD(t *testing.T) {
	// A parsed object with string keys and integer values. Direct tape construction
	// keeps the upstream filtering regression runnable on unsupported parser CPUs.
	obj := Object{tape: ParsedJson{
		Message: []byte("abc"),
		Tape: []uint64{
			uint64(TagString) << JSONTAGOFFSET, 1,
			uint64(TagInteger) << JSONTAGOFFSET, 10,
			uint64(TagString)<<JSONTAGOFFSET | 1, 1,
			uint64(TagInteger) << JSONTAGOFFSET, 20,
			uint64(TagString)<<JSONTAGOFFSET | 2, 1,
			uint64(TagInteger) << JSONTAGOFFSET, 30,
			uint64(TagObjectEnd) << JSONTAGOFFSET,
		},
	}}
	for _, key := range []string{"b", "c", "missing"} {
		t.Run(key, func(t *testing.T) {
			calls := 0
			err := obj.ForEach(func(name []byte, i Iter) {
				calls++
				value, err := i.Int()
				want := int64(20)
				if key == "c" {
					want = 30
				}
				if string(name) != key || err != nil || value != want {
					t.Errorf("callback = (%q, %d, %v); want (%q, %d, nil)", name, value, err, key, want)
				}
			}, map[string]struct{}{key: {}})
			wantCalls := 1
			if key == "missing" {
				wantCalls = 0
			}
			if err != nil || calls != wantCalls {
				t.Fatalf("ForEach = %v, %d callbacks; want nil, %d", err, calls, wantCalls)
			}
		})
	}
}

func TestIterArrayReportsExpectedType(t *testing.T) {
	i := Iter{t: TagObjectStart}
	if _, err := i.Array(nil); err == nil || err.Error() != "next item is not array" {
		t.Fatalf("Array() error = %v; want next item is not array", err)
	}
}

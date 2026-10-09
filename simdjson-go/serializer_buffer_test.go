// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package simdjson

import "testing"

func TestSerializerReusesTagBuffer(t *testing.T) {
	s := NewSerializer()
	s.CompressMode(CompressNone)
	pj := ParsedJson{Strings: &TStrings{}}
	output := s.Serialize(nil, pj)
	buffer := &s.tagsBuf[0]
	output = s.Serialize(output[:0], pj)
	if &s.tagsBuf[0] != buffer {
		t.Fatal("Serialize reallocated a sufficiently large tag buffer")
	}
	if _, err := s.Deserialize(output, nil); err != nil {
		t.Fatalf("reused serialization is invalid: %v", err)
	}
}

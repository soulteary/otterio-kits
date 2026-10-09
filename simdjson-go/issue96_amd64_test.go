//go:build !noasm && !appengine && gc

// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package simdjson

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestIssue96UnicodeEscapeDigits(t *testing.T) {
	if !SupportedCPU() {
		t.Skip("requires AVX2/CLMUL")
	}
	for _, escape := range []string{`\u00 !`, `\u00,-`, `\u+000`, `\u/000`, `\u000:`, `\u000Z`, `\u00\t`, `\u0000`, `\u00aF`} {
		for _, copyStrings := range []bool{false, true} {
			input := []byte(`{"a":"` + escape + `"}`)
			_, err := Parse(input, nil, WithCopyStrings(copyStrings))
			if (err == nil) != json.Valid(input) {
				t.Errorf("escape %q, copy=%v: Parse error=%v, json.Valid=%v", escape, copyStrings, err, json.Valid(input))
			}
		}
	}
}

func TestIssue96StringScanBound(t *testing.T) {
	if !SupportedCPU() {
		t.Skip("requires AVX2/CLMUL")
	}
	// The closing quote is outside the permitted window, but inside an allocated
	// padded buffer. The negative control therefore needs no unsafe memory access.
	buf := bytes.Repeat([]byte{'a'}, 256)
	buf[0], buf[80] = '"', '"'
	for _, tt := range []struct {
		bound uint64
		want  bool
	}{{32, false}, {128, true}} {
		var length uint64
		copyString := false
		if got := parseStringSimdValidateOnly(buf, &tt.bound, &length, &copyString); got != tt.want {
			t.Errorf("scan bound %d: got %v, want %v", tt.bound, got, tt.want)
		}
	}
}

func TestIssue96StringBufferGrowth(t *testing.T) {
	if !SupportedCPU() {
		t.Skip("requires AVX2/CLMUL")
	}
	input := make([]byte, 128)
	copy(input, `"hello"`)
	for _, prefix := range []string{"", "prefix"} {
		dst := make([]byte, len(prefix))
		copy(dst, prefix)
		if !parseStringSimd(input, &dst) || string(dst) != prefix+"hello" {
			t.Errorf("grown buffer = %q; want %q", dst, prefix+"hello")
		}
	}
}

func TestIssue96ParseNDReuse(t *testing.T) {
	if !SupportedCPU() {
		t.Skip("requires AVX2/CLMUL")
	}
	pj, err := ParseND([]byte("{\"a\":1}\n{\"b\":2}"), nil)
	if err != nil {
		t.Fatal(err)
	}
	parser := pj.internal
	if parser == nil {
		t.Fatal("ParseND did not retain its parser")
	}
	pj, err = ParseND([]byte(`{"c":3}`), pj)
	if err != nil {
		t.Fatal(err)
	}
	if pj.internal != parser {
		t.Fatal("ParseND replaced its reusable parser")
	}
	var documents int
	if err := pj.ForEach(func(i Iter) error {
		documents++
		obj, err := i.Object(nil)
		if err != nil {
			return err
		}
		if obj.FindKey("c", nil) == nil {
			t.Error("reused parser retained stale data")
		}
		return nil
	}); err != nil || documents != 1 {
		t.Fatalf("reused document count = %d, error = %v", documents, err)
	}
}

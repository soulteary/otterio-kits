/*
 * MinIO Cloud Storage, (C) 2020 MinIO, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Modified by otterio-kits maintainers on 2026-10-08:
// use deterministic local NDJSON coverage and report fixture errors without downloads.

package simdjson

import (
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/klauspost/compress/zstd"
)

const demo_ndjson = `{"Image":{"Width":800,"Height":600,"Title":"View from 15th Floor","Thumbnail":{"Url":"http://www.example.com/image/481989943","Height":125,"Width":100},"Animated":false,"IDs":[116,943,234,38793]}}
{"Image":{"Width":801,"Height":601,"Title":"View from 15th Floor","Thumbnail":{"Url":"http://www.example.com/image/481989943","Height":125,"Width":100},"Animated":false,"IDs":[116,943,234,38793]}}
{"Image":{"Width":802,"Height":602,"Title":"View from 15th Floor","Thumbnail":{"Url":"http://www.example.com/image/481989943","Height":125,"Width":100},"Animated":false,"IDs":[116,943,234,38793]}}`

func verifyDemoNdjson(pj internalParsedJson, t *testing.T, object int) {

	const nul = '\000'

	testCases := []struct {
		expected []struct {
			c   byte
			val uint64
		}
	}{
		{
			[]struct {
				c   byte
				val uint64
			}{
				// First object
				{'r', 0x33},
				{'{', 0x32},
				{'"', 0x2},
				{nul, 0x5},
				{'{', 0x31},
				{'"', 0xb},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x320},
				{'"', 0x17},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x258},
				{'"', 0x24},
				{nul, 0x5},
				{'"', 0x2c},
				{nul, 0x14},
				{'"', 0x43},
				{nul, 0x9},
				{'{', 0x21},
				{'"', 0x50},
				{nul, 0x3},
				{'"', 0x56},
				{nul, 0x26},
				{'"', 0x7f},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x7d},
				{'"', 0x8c},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x64},
				{'}', 0x13},
				{'"', 0x99},
				{nul, 0x8},
				{'f', 0x0},
				{'"', 0xaa},
				{nul, 0x3},
				{'[', 0x30},
				{'l', 0x0},
				{nul, 0x74},
				{'l', 0x0},
				{nul, 0x3af},
				{'l', 0x0},
				{nul, 0xea},
				{'l', 0x0},
				{nul, 0x9789},
				{']', 0x26},
				{'}', 0x4},
				{'}', 0x1},
				{'r', 0x0},
				//
				// Second object
				{'r', 0x66},
				{'{', 0x65},
				{'"', 0xc7},
				{nul, 0x5},
				{'{', 0x64},
				{'"', 0xd0},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x321},
				{'"', 0xdc},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x259},
				{'"', 0xe9},
				{nul, 0x5},
				{'"', 0xf1},
				{nul, 0x14},
				{'"', 0x108},
				{nul, 0x9},
				{'{', 0x54},
				{'"', 0x115},
				{nul, 0x3},
				{'"', 0x11b},
				{nul, 0x26},
				{'"', 0x144},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x7d},
				{'"', 0x151},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x64},
				{'}', 0x46},
				{'"', 0x15e},
				{nul, 0x8},
				{'f', 0x0},
				{'"', 0x16f},
				{nul, 0x3},
				{'[', 0x63},
				{'l', 0x0},
				{nul, 0x74},
				{'l', 0x0},
				{nul, 0x3af},
				{'l', 0x0},
				{nul, 0xea},
				{'l', 0x0},
				{nul, 0x9789},
				{']', 0x59},
				{'}', 0x37},
				{'}', 0x34},
				{'r', 0x33},
				//
				// Third object
				{'r', 0x99},
				{'{', 0x98},
				{'"', 0x18c},
				{nul, 0x5},
				{'{', 0x97},
				{'"', 0x195},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x322},
				{'"', 0x1a1},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x25a},
				{'"', 0x1ae},
				{nul, 0x5},
				{'"', 0x1b6},
				{nul, 0x14},
				{'"', 0x1cd},
				{nul, 0x9},
				{'{', 0x87},
				{'"', 0x1da},
				{nul, 0x3},
				{'"', 0x1e0},
				{nul, 0x26},
				{'"', 0x209},
				{nul, 0x6},
				{'l', 0x0},
				{nul, 0x7d},
				{'"', 0x216},
				{nul, 0x5},
				{'l', 0x0},
				{nul, 0x64},
				{'}', 0x79},
				{'"', 0x223},
				{nul, 0x8},
				{'f', 0x0},
				{'"', 0x234},
				{nul, 0x3},
				{'[', 0x96},
				{'l', 0x0},
				{nul, 0x74},
				{'l', 0x0},
				{nul, 0x3af},
				{'l', 0x0},
				{nul, 0xea},
				{'l', 0x0},
				{nul, 0x9789},
				{']', 0x8c},
				{'}', 0x6a},
				{'}', 0x67},
				{'r', 0x66},
			},
		},
	}

	tc := testCases[0]

	//	For TestFindNewlineDelimiters, adjust the array that we are testing against
	if object == 1 {
		tc.expected = tc.expected[:51]
	} else if object == 2 || object == 3 {
		tc.expected = tc.expected[:51]

		adjustQoutes := []uint64{2, 5, 9, 13, 15, 17, 20, 22, 24, 28, 33, 36}
		for _, a := range adjustQoutes {
			tc.expected[a].val += 1
		}
		if object == 2 {
			tc.expected[8].val = 801
			tc.expected[12].val = 601
		} else if object == 3 {
			tc.expected[8].val = 802
			tc.expected[12].val = 602
		}
	}

	if len(pj.Tape) != len(tc.expected) {
		t.Errorf("verifyDemoNdjson: got: %d want: %d", len(pj.Tape), len(tc.expected))
	}
	for ii, tp := range pj.Tape {
		//c := "'" + string(byte(tp >> 56)) + "'"
		//if byte(tp >> 56) == 0 {
		//	c = "nul"
		//}
		//fmt.Printf("{%s, 0x%x},\n", c, tp&0xffffffffffffff)
		expected := tc.expected[ii].val | (uint64(tc.expected[ii].c) << 56)
		if !pj.copyStrings && tp != expected {
			t.Errorf("verifyDemoNdjson(%d): got: %016x want: %016x", ii, tp, expected)
		}
	}
}

func TestNdjsonCountWhere(t *testing.T) {
	if !SupportedCPU() {
		t.SkipNow()
	}
	if testing.Short() {
		t.Skip("skipping... too long")
	}
	ndjson := loadFile(t, "testdata/parking-citations.json.zst")
	pj, err := ParseND(ndjson, nil)
	if err != nil {
		t.Fatal(err)
	}

	const want = 116
	t.Run("countWhere", func(t *testing.T) {
		if result := countWhere("Make", "HOND", *pj); result != want {
			t.Errorf("TestNdjsonCountWhere: got: %d want: %d", result, want)
		}
	})
	t.Run("foreach", func(t *testing.T) {
		var result int
		var elem *Element
		var obj *Object
		err := pj.ForEach(func(i Iter) error {
			var err error
			obj, err = i.Object(obj)
			if err == nil {
				elem = obj.FindKey("Make", elem)
				if elem != nil {
					bts, _ := elem.Iter.StringBytes()
					if string(bts) == "HOND" {
						result++
					}
				}
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
		if result != want {
			t.Errorf("TestNdjsonCountWhere: got: %d want: %d", result, want)
		}
	})
	t.Run("foreach-findelement", func(t *testing.T) {
		var result int
		var elem *Element
		err := pj.ForEach(func(i Iter) error {
			var err error
			elem, err = i.FindElement(elem, "Make")
			if err != nil {
				return nil
			}
			bts, _ := elem.Iter.StringBytes()
			if string(bts) == "HOND" {
				result++
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
		if result != want {
			t.Errorf("TestNdjsonCountWhere: got: %d want: %d", result, want)
		}
	})
}

func TestNdjsonCountWhere2(t *testing.T) {
	if !SupportedCPU() {
		t.SkipNow()
	}
	// Cover matching, missing, non-string and case-sensitive fields without
	// relying on the external Reddit corpus. Blank lines also exercise
	// the trimming that the original test constructed but did not parse.
	ndjson := []byte("\n\n" + `{"subreddit":"reddit.com","author":"otter","score":3}
{"subreddit":"golang","author":"otter","score":7}
{"subreddit":"reddit.com","author":"soulteary","score":1}
{"subreddit":"programming","author":"otter","score":0}
{"subreddit":"golang","author":"soulteary","score":10}
{"subreddit":"reddit.com","author":"otter","score":4}
{"author":"otter","score":5}
{"subreddit":null,"author":"soulteary","score":2}
{"subreddit":123,"author":"otter","score":9}
{"subreddit":"Golang","author":"otter","score":6}
{"subreddit":"elsewhere","author":"guest","nested":{"subreddit":"reddit.com"}}
{"subreddit":"","author":"guest"}` + "\n\n")
	pj, err := ParseND(ndjson, nil)
	if err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		name  string
		key   string
		value string
		want  int
	}{
		{name: "reddit", key: "subreddit", value: "reddit.com", want: 3},
		{name: "golang", key: "subreddit", value: "golang", want: 2},
		{name: "case-sensitive", key: "subreddit", value: "Golang", want: 1},
		{name: "empty-string", key: "subreddit", value: "", want: 1},
		{name: "unmatched", key: "subreddit", value: "absent", want: 0},
		{name: "other-key", key: "author", value: "otter", want: 7},
		{name: "missing-key", key: "missing", value: "", want: 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Run("countWhere", func(t *testing.T) {
				if result := countWhere(tc.key, tc.value, *pj); result != tc.want {
					t.Errorf("got: %d want: %d", result, tc.want)
				}
			})
			t.Run("foreach-findelement", func(t *testing.T) {
				var result int
				var elem *Element
				err := pj.ForEach(func(i Iter) error {
					var err error
					elem, err = i.FindElement(elem, tc.key)
					if err != nil || elem.Type != TypeString {
						return nil
					}
					bts, err := elem.Iter.StringBytes()
					if err != nil {
						return err
					}
					if string(bts) == tc.value {
						result++
					}
					return nil
				})
				if err != nil {
					t.Fatal(err)
				}
				if result != tc.want {
					t.Errorf("got: %d want: %d", result, tc.want)
				}
			})
		})
	}
}

func loadFile(tb testing.TB, filename string) []byte {
	tb.Helper()
	data, err := readFixture(filename)
	if err != nil {
		tb.Fatalf("load local fixture: %v; prepare the fixture at %s before running this test or benchmark (no automatic download)", err, filename)
	}
	return data
}

func readFixture(filename string) ([]byte, error) {
	if !strings.HasSuffix(filename, ".zst") {
		data, err := os.ReadFile(filename)
		if err != nil {
			return nil, fmt.Errorf("read fixture %q: %w", filename, err)
		}
		return data, nil
	}
	f, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("open fixture %q: %w", filename, err)
	}
	defer f.Close()
	dec, err := zstd.NewReader(f)
	if err != nil {
		return nil, fmt.Errorf("create decompressor for fixture %q: %w", filename, err)
	}
	defer dec.Close()
	data, err := io.ReadAll(dec)
	if err != nil {
		return nil, fmt.Errorf("decompress fixture %q: %w", filename, err)
	}
	return data, nil
}

func TestReadFixtureMissing(t *testing.T) {
	for _, name := range []string{"missing.json", "missing.json.zst"} {
		t.Run(name, func(t *testing.T) {
			filename := filepath.Join(t.TempDir(), name)
			data, err := readFixture(filename)
			if !errors.Is(err, os.ErrNotExist) {
				t.Fatalf("expected missing-file error, got data %q and error %v", data, err)
			}
			if !strings.Contains(err.Error(), filename) {
				t.Fatalf("error does not identify the missing fixture: %v", err)
			}
		})
	}
}

func count_raw_tape(tape []uint64) (count int) {

	for tapeidx := uint64(0); tapeidx < uint64(len(tape)); count++ {
		tape_val := tape[tapeidx]
		tapeidx = tape_val & JSONVALUEMASK
	}

	return
}

func countWhere(key, value string, data ParsedJson) (count int) {
	tmpi := data.Iter()
	stack := []*Iter{&tmpi}
	var obj *Object
	var tmp *Iter
	var elem Element

	for len(stack) > 0 {
		iter := stack[len(stack)-1]
		typ := iter.Advance()

	typeswitch:
		switch typ {
		case TypeNone:
			if len(stack) == 0 {
				return
			}
			stack = stack[:len(stack)-1]
		case TypeRoot:
			var err error
			typ, tmp, err = iter.Root(tmp)
			if err != nil {
				log.Fatal(err)
			}
			switch typ {
			case TypeNone:
				break typeswitch
			case TypeObject:
			default:
				log.Fatalf("expected object inside root, got %v", typ)
			}
			if len(stack) > 2 {
				break
			}
			obj, err = tmp.Object(obj)
			if err != nil {
				log.Fatal(err)
			}
			e := obj.FindKey(key, &elem)
			if e != nil && elem.Type == TypeString {
				v, _ := elem.Iter.StringBytes()
				if string(v) == value {
					count++
				}
			}
		default:
		}
	}

	return
}

func countObjects(data ParsedJson) (count int) {
	iter := data.Iter()
	for {
		typ := iter.Advance()
		switch typ {
		case TypeNone:
			return
		case TypeRoot:
			count++
		default:
			panic(typ)
		}
	}
}

func BenchmarkNdjsonWarmCountStar(b *testing.B) {
	if !SupportedCPU() {
		b.SkipNow()
	}

	ndjson := loadFile(b, "testdata/parking-citations-1M.json.zst")

	pj, err := ParseND(ndjson, nil)
	if err != nil {
		b.Fatal(err)
	}
	b.SetBytes(int64(len(ndjson)))
	b.ReportAllocs()
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		countObjects(*pj)
	}
}

func BenchmarkNdjsonWarmCountStarWithWhere(b *testing.B) {
	if !SupportedCPU() {
		b.SkipNow()
	}

	ndjson := loadFile(b, "testdata/parking-citations-1M.json.zst")

	pj, err := ParseND(ndjson, nil)
	if err != nil {
		b.Fatal(err)
	}

	b.Run("iter", func(b *testing.B) {
		b.SetBytes(int64(len(ndjson)))
		b.ReportAllocs()
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			countWhere("Make", "HOND", *pj)
		}
	})
}

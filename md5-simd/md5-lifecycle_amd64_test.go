//go:build amd64 && !appengine && !noasm && gc

// Copyright 2026 otterIO contributors.
// SPDX-License-Identifier: Apache-2.0

package md5simd

import (
	"bytes"
	"crypto/md5"
	"fmt"
	"sync"
	"testing"
	"time"
)

func lifecycleServer(t *testing.T, useAVX512 bool) *md5Server {
	t.Helper()
	server := NewServerWithOptions(ServerOptions{UseAVX512: useAVX512})
	s, ok := server.(*md5Server)
	if !ok {
		server.Close()
		t.Skip("SIMD server requires AVX2")
	}
	if useAVX512 && !hasAVX512 {
		s.Close()
		<-s.done
		t.Skip("AVX512 is unavailable")
	}
	cleanupLifecycleServer(t, s)
	return s
}

func cleanupLifecycleServer(t *testing.T, s *md5Server) {
	t.Helper()
	t.Cleanup(func() {
		s.Close()
		select {
		case <-s.done:
		case <-time.After(5 * time.Second):
			t.Error("server did not exit")
		}
	})
}

// These tests keep at most one data lane active, exercising the real scheduler
// and scalar assembly even on amd64 hosts without AVX2.
func scalarLifecycleServer(t *testing.T) *md5Server {
	t.Helper()
	s := newMD5Server(ServerOptions{})
	cleanupLifecycleServer(t, s)
	return s
}

func TestClosedHashersReleaseDigestState(t *testing.T) {
	s := scalarLifecycleServer(t)
	for i := 0; i < 1000; i++ {
		h := s.NewHash()
		h.Write(bytes.Repeat([]byte{byte(i)}, BlockSize))
		h.Sum(nil)
		h.Close()
	}
	// Process one more data block so the scheduler scans closed clients.
	// Reset removes the remaining live client's state before inspecting the map.
	h := s.NewHash()
	h.Write(make([]byte, BlockSize))
	h.Reset()
	h.Sum(nil)
	h.Close()
	s.Close()
	<-s.done
	if len(s.digests) != 0 {
		t.Fatalf("closed hashers retained %d digest entries", len(s.digests))
	}
	if len(s.buffers) != cap(s.buffers) {
		t.Fatalf("buffers returned: %d/%d", len(s.buffers), cap(s.buffers))
	}
}

func TestExhaustedBuffersWakeServer(t *testing.T) {
	for _, operation := range []string{"write", "partial-block", "sum"} {
		t.Run(operation, func(t *testing.T) {
			s := scalarLifecycleServer(t)
			h := s.NewHash().(*md5Digest)
			// Ensure registration is processed before queuing an unnotified block.
			h.Sum(nil)
			input := bytes.Repeat([]byte{0x5a}, BlockSize)
			buf := <-s.buffers
			copy(buf, input)
			h.len = BlockSize
			h.sendBlock(blockInput{uid: h.uid, msg: buf[:BlockSize]}, false)
			// Reserve the other buffers to deterministically model pool exhaustion.
			reserved := make([][]byte, cap(s.buffers)-1)
			for i := range reserved {
				reserved[i] = <-s.buffers
			}
			done := make(chan []byte, 1)
			go func() {
				switch operation {
				case "write":
					h.Write(input)
				case "partial-block":
					h.Write(input[:1])
					h.Write(input[1:])
				}
				done <- h.Sum(nil)
			}()
			select {
			case got := <-done:
				data := input
				if operation != "sum" {
					data = bytes.Repeat(input, 2)
				}
				want := md5.Sum(data)
				if !bytes.Equal(got, want[:]) {
					t.Errorf("digest = %x, want %x", got, want)
				}
			case <-time.After(5 * time.Second):
				// Release the blocked writer before failing, including on old code.
				s.cycle <- h.uid
				<-done
				t.Error("writer stalled while queued work could return a buffer")
			}
			for _, buf := range reserved {
				s.buffers <- buf
			}
			h.Close()
		})
	}
}

func TestConcurrentHasherLifecycle(t *testing.T) {
	for _, useAVX512 := range []bool{false, true} {
		t.Run(fmt.Sprint(useAVX512), func(t *testing.T) {
			s := lifecycleServer(t, useAVX512)
			var wg sync.WaitGroup
			for worker := 0; worker < 64; worker++ {
				wg.Add(1)
				go func(worker int) {
					defer wg.Done()
					input := bytes.Repeat([]byte{byte(worker)}, 4*internalBlockSize+1)
					want := md5.Sum(input)
					for round := 0; round < 8; round++ {
						h := s.NewHash()
						for reuse := 0; reuse < 2; reuse++ {
							if reuse != 0 {
								h.Reset()
							}
							h.Write(input[:1])
							h.Write(input[1:])
							if got := h.Sum(nil); !bytes.Equal(got, want[:]) {
								t.Errorf("worker=%d round=%d reuse=%d: digest=%x, want=%x", worker, round, reuse, got, want)
							}
						}
						h.Close()
					}
				}(worker)
			}
			wg.Wait()
		})
	}
}

func TestHasherCloseAfterServerExit(t *testing.T) {
	s := scalarLifecycleServer(t)
	h := s.NewHash()
	s.Close()
	<-s.done
	// Make notification impossible so Close must observe server exit.
	for len(s.cycle) < cap(s.cycle) {
		s.cycle <- 0
	}
	done := make(chan struct{})
	go func() {
		h.Close()
		h.Close()
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		<-s.cycle
		<-done
		t.Fatal("hasher close blocked after server exit")
	}
}

//go:build !noasm && !appengine && gc
// +build !noasm,!appengine,gc

// Copyright (c) 2020 MinIO Inc. All rights reserved.
// Use of this source code is governed by a license that can be
// found in the LICENSE file.
// Modified by otterIO contributors in 2026: wake buffer waits and closed clients.

package md5simd

import (
	"encoding/binary"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
)

// md5Digest - Type for computing MD5 using either AVX2 or AVX512
type md5Digest struct {
	serverDone  <-chan struct{}
	uid         uint64
	blocksCh    chan blockInput
	cycleServer chan uint64
	x           [BlockSize]byte
	nx          int
	len         uint64
	buffers     <-chan []byte
}

// NewHash - initialize instance for Md5 implementation.
func (s *md5Server) NewHash() Hasher {
	uid := atomic.AddUint64(&s.uidCounter, 1)
	blockCh := make(chan blockInput, buffersPerLane)
	s.newInput <- newClient{
		uid:   uid,
		input: blockCh,
	}
	return &md5Digest{
		serverDone:  s.done,
		uid:         uid,
		buffers:     s.buffers,
		blocksCh:    blockCh,
		cycleServer: s.cycle,
	}
}

// Size - Return size of checksum
func (d *md5Digest) Size() int { return Size }

// BlockSize - Return blocksize of checksum
func (d md5Digest) BlockSize() int { return BlockSize }

func (d *md5Digest) Reset() {
	if d.blocksCh == nil {
		panic("reset after close")
	}
	d.nx = 0
	d.len = 0
	d.sendBlock(blockInput{uid: d.uid, reset: true}, false)
}

// write to digest
func (d *md5Digest) Write(p []byte) (nn int, err error) {
	if d.blocksCh == nil {
		return 0, errors.New("md5Digest closed")
	}

	// break input into chunks of maximum internalBlockSize size
	for {
		l := len(p)
		if l > internalBlockSize {
			l = internalBlockSize
		}
		nnn, err := d.write(p[:l])
		if err != nil {
			return nn, err
		}
		nn += nnn
		p = p[l:]

		if len(p) == 0 {
			break
		}

	}
	return
}

func (d *md5Digest) write(p []byte) (nn int, err error) {

	nn = len(p)
	d.len += uint64(nn)
	if d.nx > 0 {
		n := copy(d.x[d.nx:], p)
		d.nx += n
		if d.nx == BlockSize {
			// Create a copy of the overflow buffer in order to send it async over the channel
			// (since we will modify the overflow buffer down below with any access beyond multiples of 64)
			tmp := d.acquireBuffer()
			tmp = tmp[:BlockSize]
			copy(tmp, d.x[:])
			d.sendBlock(blockInput{uid: d.uid, msg: tmp}, len(p)-n < BlockSize)
			d.nx = 0
		}
		p = p[n:]
	}
	if len(p) >= BlockSize {
		n := len(p) &^ (BlockSize - 1)
		buf := d.acquireBuffer()
		buf = buf[:n]
		copy(buf, p)
		d.sendBlock(blockInput{uid: d.uid, msg: buf}, len(p)-n < BlockSize)
		p = p[n:]
	}
	if len(p) > 0 {
		d.nx = copy(d.x[:], p)
	}
	return
}

func (d *md5Digest) Close() {
	if d.blocksCh != nil {
		close(d.blocksCh)
		d.blocksCh = nil
		// An idle server must wake up to release this client's state.
		// Do not wait for a notification after the server has exited.
		select {
		case d.cycleServer <- d.uid:
		case <-d.serverDone:
		}
	}
}

var sumChPool sync.Pool

func init() {
	sumChPool.New = func() interface{} {
		return make(chan sumResult, 1)
	}
}

// Sum - Return MD5 sum in bytes
func (d *md5Digest) Sum(in []byte) (result []byte) {
	if d.blocksCh == nil {
		panic("sum after close")
	}

	trail := d.acquireBuffer()
	trail = append(trail[:0], d.x[:d.nx]...)

	length := d.len
	// Padding.  Add a 1 bit and 0 bits until 56 bytes mod 64.
	var tmp [64]byte
	tmp[0] = 0x80
	if length%64 < 56 {
		trail = append(trail, tmp[0:56-length%64]...)
	} else {
		trail = append(trail, tmp[0:64+56-length%64]...)
	}

	// Length in bits.
	length <<= 3
	binary.LittleEndian.PutUint64(tmp[:], length) // append length in bits

	trail = append(trail, tmp[0:8]...)
	if len(trail)%BlockSize != 0 {
		panic(fmt.Errorf("internal error: sum block was not aligned. len=%d, nx=%d", len(trail), d.nx))
	}
	sumCh := sumChPool.Get().(chan sumResult)
	d.sendBlock(blockInput{uid: d.uid, msg: trail, sumCh: sumCh}, true)

	sum := <-sumCh
	sumChPool.Put(sumCh)

	return append(in, sum.digest[:]...)
}

// acquireBuffer wakes the server before waiting on an exhausted shared pool.
// Otherwise writers can hold all buffers in partially filled input channels
// while the server waits for a cycle notification that none of them can send.
func (d *md5Digest) acquireBuffer() []byte {
	select {
	case buf := <-d.buffers:
		return buf
	default:
		d.cycleServer <- d.uid
		return <-d.buffers
	}
}

// sendBlock will send a block for processing.
// If cycle is true we will block on cycle, otherwise we will only block
// if the block channel is full.
func (d *md5Digest) sendBlock(bi blockInput, cycle bool) {
	if cycle {
		select {
		case d.blocksCh <- bi:
			d.cycleServer <- d.uid
		}
		return
	}
	// Only block on cycle if we filled the buffer
	select {
	case d.blocksCh <- bi:
		return
	default:
		d.cycleServer <- d.uid
		d.blocksCh <- bi
	}
}

import pydivert
import time
import threading
import traceback

class BandwidthLimiter:
    def __init__(self):
        self._stop_event = threading.Event()
        self.download_limit_bps = 0  # 0 means unlimited
        self.upload_limit_bps = 0    # 0 means unlimited
        
        # Token bucket state
        self.bucket_in = 0.0
        self.bucket_out = 0.0
        self.last_check_in = time.time()
        self.last_check_out = time.time()
        
    def set_limits(self, download_mbps, upload_mbps):
        """Set limits in Mbps (Megabits per second)"""
        # Convert Mbps to bytes per second for easier handling with packet lengths
        # 1 Mbps = 1,000,000 bits/s = 125,000 bytes/s
        self.download_limit_bps = float(download_mbps) * 125000
        self.upload_limit_bps = float(upload_mbps) * 125000
        
        # Reset buckets to burst size (1 second worth of data or min 15KB)
        self.bucket_in = self.download_limit_bps if self.download_limit_bps > 0 else float('inf')
        self.bucket_out = self.upload_limit_bps if self.upload_limit_bps > 0 else float('inf')

    def _refill_bucket(self, current_bucket, limit_rate, last_check):
        now = time.time()
        elapsed = now - last_check
        if limit_rate <= 0:
            return float('inf'), now
        
        added = elapsed * limit_rate
        new_bucket = min(current_bucket + added, limit_rate * 1.0) # Max burst 1 second
        return new_bucket, now

    def start(self):
        self._stop_event.clear()
        # Run in a separate thread so GUI doesn't freeze
        self._thread = threading.Thread(target=self._worker)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        # pydivert loop is blocking, so we might need to send a dummy packet or just wait 
        # for it to timeout if we used a timeout. 
        # However, a hard stop from main process (exit) usually kills it.
        # For clean shutdown, we rely on the loop checking stop_event if we use a timeout.
    
    def _worker(self):
        # Filter: Capture all traffic (true). "ip" might be ambiguous or limited on some systems.
        # priority=0 by default.
        try:
            # recv_bufsize=65535 to standard MTU limit to prevent WinError 87 on large packets
            with pydivert.WinDivert(filter="true") as w: # Filter moved to named arg for clarity
                # Manually handle buffer size via recv() if needed, but pydivert usually handles it if we don't pass it?
                # Wait, pydivert constructor does NOT take bufsize. 
                # Research said use w.recv(65535) method instead of iterator.
                # So I must change `for packet in w:` to a while loop with w.recv().
                
                while not self._stop_event.is_set():
                    try:
                        packet = w.recv(bufsize=65535) # Catch large packets
                    except Exception as e:
                        # Timeout or other error during recv
                        # But wait, does it timeout? default timeout is infinite?
                        # WinError 87 might happen here if buffer too small.
                        if "87" in str(e): 
                             print("WinDivert recv error 87 (packet too big?)")
                             continue
                        raise e

                    if self._stop_event.is_set():
                        w.send(packet)
                        break

                    packet_len = len(packet.raw)
                    is_outbound = packet.is_outbound
                    
                    limit = self.upload_limit_bps if is_outbound else self.download_limit_bps
                    
                    # If unlimited, just pass
                    if limit <= 0:
                        w.send(packet)
                        continue

                    # Token Bucket Logic
                    if is_outbound:
                        self.bucket_out, self.last_check_out = self._refill_bucket(
                            self.bucket_out, self.upload_limit_bps, self.last_check_out
                        )
                        bucket = self.bucket_out
                    else:
                        self.bucket_in, self.last_check_in = self._refill_bucket(
                            self.bucket_in, self.download_limit_bps, self.last_check_in
                        )
                        bucket = self.bucket_in
                    
                    if bucket >= packet_len:
                        # Enough tokens, pass
                        if is_outbound:
                            self.bucket_out -= packet_len
                        else:
                            self.bucket_in -= packet_len
                        w.send(packet)
                    else:
                        # Not enough tokens.
                        # Calculate needed time: (needed - have) / rate
                        # We throttle by sleeping. NOTE: This blocks ALL traffic of that direction.
                        # Ideally we should queue, but for global simple throttle, simple sleep is 'okay'-ish
                        # though it adds latency.
                        shortage = packet_len - bucket
                        wait_time = shortage / limit
                        
                        # Cap max wait to avoid timeouts (e.g. 0.5s)
                        if wait_time > 0.5:
                             # Drop packet if wait is too long (TCP will retransmit)
                             # Or just cap sleep? Dropping is better for congestion control than massive lag.
                             # Let's cap sleep and send anyway (burst) or drop?
                             # Let's sleep max 0.1s and send (allow slight burst over limit)
                             time.sleep(0.1)
                             # We deduct anyway? No, negative bucket.
                             if is_outbound:
                                 self.bucket_out -= packet_len
                             else:
                                 self.bucket_in -= packet_len
                        else:
                            time.sleep(wait_time)
                            # After sleep, assume we 'paid' for it with time, but we update bucket logic?
                            # Actually, simplest is direct sleep then send.
                            # Update bucket to 0 or negative
                            if is_outbound:
                                self.bucket_out -= packet_len
                            else:
                                self.bucket_in -= packet_len
                        
                        w.send(packet)
                        
                        # Update timestamps for next iteration to avoid double adding
                        # Actually _refill_bucket relies on system time, so checking next time it will work.

        except Exception as e:
            traceback.print_exc()
            print(f"Error in traffic shaper: {e}")

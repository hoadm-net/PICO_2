# NRF24L01 MicroPython driver for Raspberry Pi Pico
# Compatible with MicroPython on RP2040 / RP2350

from micropython import const
import utime

# ===== SPI COMMANDS =====
R_REGISTER   = const(0x00)
W_REGISTER   = const(0x20)
R_RX_PAYLOAD = const(0x61)
W_TX_PAYLOAD = const(0xA0)
FLUSH_TX     = const(0xE1)
FLUSH_RX     = const(0xE2)
NOP          = const(0xFF)

# ===== REGISTERS =====
CONFIG      = const(0x00)
EN_AA       = const(0x01)
EN_RXADDR   = const(0x02)
SETUP_AW    = const(0x03)
SETUP_RETR  = const(0x04)
RF_CH       = const(0x05)
RF_SETUP    = const(0x06)
STATUS      = const(0x07)
RX_ADDR_P0  = const(0x0A)
TX_ADDR     = const(0x10)
RX_PW_P0    = const(0x11)
FIFO_STATUS = const(0x17)

# ===== CONFIG BITS =====
EN_CRC  = const(0x08)
CRCO    = const(0x04)
PWR_UP  = const(0x02)
PRIM_RX = const(0x01)

# ===== STATUS BITS =====
RX_DR  = const(0x40)
TX_DS  = const(0x20)
MAX_RT = const(0x10)


class NRF24L01:

    def __init__(self, spi, cs, ce, channel=46, payload_size=1):
        self.spi = spi
        self.cs = cs
        self.ce = ce
        self.payload_size = payload_size
        self.pipe0_read_addr = None

        self.cs.value(1)
        self.ce.value(0)
        utime.sleep_ms(5)

        # Payload size for pipe 0
        self._reg_write(RX_PW_P0, payload_size)
        # RF channel
        self._reg_write(RF_CH, channel)
        # RF setup: 2Mbps, 0dBm  (0x0E = DR_HIGH=1, PWR=11)
        self._reg_write(RF_SETUP, 0x0E)
        # Disable Auto-ACK on all pipes
        self._reg_write(EN_AA, 0x00)
        # Disable auto-retransmit
        self._reg_write(SETUP_RETR, 0x00)
        # 2-byte CRC, power up
        self._reg_write(CONFIG, EN_CRC | CRCO | PWR_UP)
        # Flush FIFOs
        self._send_cmd(FLUSH_RX)
        self._send_cmd(FLUSH_TX)
        # Clear status flags
        self._reg_write(STATUS, RX_DR | TX_DS | MAX_RT)

        utime.sleep_ms(2)

    # ---- Low-level SPI helpers ----

    def _send_cmd(self, cmd):
        self.cs.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def _reg_write(self, reg, value):
        self.cs.value(0)
        self.spi.write(bytes([W_REGISTER | reg, value]))
        self.cs.value(1)

    def _reg_write_bytes(self, reg, data):
        self.cs.value(0)
        self.spi.write(bytes([W_REGISTER | reg]) + data)
        self.cs.value(1)

    def _reg_read(self, reg):
        self.cs.value(0)
        self.spi.write(bytes([R_REGISTER | reg]))
        val = self.spi.read(1)
        self.cs.value(1)
        return val[0]

    def _status(self):
        self.cs.value(0)
        val = self.spi.read(1, NOP)
        self.cs.value(1)
        return val[0]

    # ---- Public API ----

    def open_tx_pipe(self, address):
        """Set TX address (5 bytes). Also sets RX pipe 0 to same address for ACK."""
        self.pipe0_read_addr = address
        self._reg_write_bytes(TX_ADDR, address)
        self._reg_write_bytes(RX_ADDR_P0, address)
        self._reg_write(RX_PW_P0, self.payload_size)

    def open_rx_pipe(self, pipe_id, address):
        """Open a receive pipe (0-5) with the given address."""
        if pipe_id == 0:
            self.pipe0_read_addr = address
        self._reg_write_bytes(RX_ADDR_P0 + pipe_id, address)
        self._reg_write(RX_PW_P0 + pipe_id, self.payload_size)
        self._reg_write(EN_RXADDR, self._reg_read(EN_RXADDR) | (1 << pipe_id))

    def stop_listening(self):
        """Switch to TX mode."""
        self.ce.value(0)
        self._reg_write(CONFIG, self._reg_read(CONFIG) & ~PRIM_RX)
        if self.pipe0_read_addr is not None:
            self._reg_write_bytes(RX_ADDR_P0, self.pipe0_read_addr)

    def start_listening(self):
        """Switch to RX mode."""
        self._reg_write(CONFIG, self._reg_read(CONFIG) | PRIM_RX)
        self._reg_write(STATUS, RX_DR | TX_DS | MAX_RT)
        self.ce.value(1)
        utime.sleep_us(130)

    def any(self):
        """Return True if there is data in the RX FIFO."""
        return not bool(self._reg_read(FIFO_STATUS) & 0x01)

    def recv(self):
        """Read payload from RX FIFO."""
        self.cs.value(0)
        self.spi.write(bytes([R_RX_PAYLOAD]))
        buf = self.spi.read(self.payload_size)
        self.cs.value(1)
        self._reg_write(STATUS, RX_DR)
        return buf

    def send(self, buf, timeout=500):
        """
        Transmit buf (bytes). Blocks until TX_DS (success) or raises OSError.
        buf is padded/trimmed to payload_size automatically.
        """
        # Prepare payload
        data = buf[:self.payload_size]
        if len(data) < self.payload_size:
            data = data + b'\x00' * (self.payload_size - len(data))

        self.ce.value(0)
        self._send_cmd(FLUSH_TX)
        self._reg_write(STATUS, RX_DR | TX_DS | MAX_RT)

        # Write payload
        self.cs.value(0)
        self.spi.write(bytes([W_TX_PAYLOAD]) + data)
        self.cs.value(1)

        # Pulse CE to start transmission
        self.ce.value(1)
        utime.sleep_us(15)
        self.ce.value(0)

        # Wait for TX FIFO to clear (TX_DS set when packet leaves FIFO)
        start = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start) < timeout:
            status = self._status()
            if status & TX_DS:
                self._reg_write(STATUS, TX_DS)
                return True
            if status & MAX_RT:
                # MAX_RT should not fire when Auto-ACK is off, but clear it just in case
                self._reg_write(STATUS, MAX_RT)
                self._send_cmd(FLUSH_TX)
                return False
        raise OSError("NRF24L01: send timeout")

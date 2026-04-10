import busio
import board


class SIM28:
    """
    Driver for the SIM28 GPS module (CircuitPython version).
    Parses NMEA sentences (GPGGA/GNGGA) to extract position data.
    """

    def __init__(self, uart=None, tx=board.P14, rx=board.P13, baudrate=9600):
        """
        Initialize the SIM28 GPS module.

        Args:
            uart: Pre-configured UART object. If None, creates one with given parameters.
            tx: TX pin (default board.P14).
            rx: RX pin (default board.P13).
            baudrate: UART baudrate (default 9600).
        """
        if uart is not None:
            self._uart = uart
        else:
            self._uart = busio.UART(tx, rx, baudrate=baudrate)

        self._latitude = None
        self._longitude = None
        self._altitude = None
        self._satellites = None
        self._time = None

    def read_buffer(self):
        """
        Read UART buffer and return a list of valid NMEA sentences.

        Returns:
            list: List of valid NMEA sentences found in the buffer.
        """
        buffer = ""
        if self._uart.in_waiting:
            raw_data = self._uart.read()
            if raw_data:
                try:
                    buffer = raw_data.decode('ascii', errors='ignore')
                except:
                    buffer = ""

        sentences_raw = buffer.split("\r\n")
        sentences = []
        for sentence in sentences_raw:
            if sentence.startswith("$") and len(sentence.split(',')) >= 3:
                sentences.append(sentence)
        return sentences

    def _parse_gga(self, sentence):
        """
        Parse a GGA sentence and update internal state.

        Args:
            sentence: NMEA GGA sentence string.

        Returns:
            dict: Parsed GPS data or empty dict on error.
        """
        data = {}
        fields = sentence.split(',')

        try:
            # Time (format HHMMSS.ss)
            if fields[1]:
                time_val = float(fields[1])
                h = int(time_val / 10000)
                m = int((time_val - h * 10000) / 100)
                s = int(time_val - h * 10000 - m * 100)
                data["time"] = "{:02d}:{:02d}:{:02d}".format(h, m, s)

            # Latitude (format DDMM.MMMM)
            if fields[2]:
                lat = float(fields[2])
                lat_deg = int(lat / 100)
                lat_min = lat - lat_deg * 100
                lat_decimal = lat_deg + lat_min / 60
                if fields[3] == "S":
                    lat_decimal *= -1
                data["latitude"] = lat_decimal

            # Longitude (format DDDMM.MMMM)
            if fields[4]:
                lon = float(fields[4])
                lon_deg = int(lon / 100)
                lon_min = lon - lon_deg * 100
                lon_decimal = lon_deg + lon_min / 60
                if fields[5] == "W":
                    lon_decimal *= -1
                data["longitude"] = lon_decimal

            # Number of satellites
            if fields[7]:
                data["satellites"] = int(fields[7])

            # Altitude (meters)
            if fields[9]:
                data["altitude"] = float(fields[9])

        except (ValueError, IndexError):
            pass

        return data

    def update(self):
        """
        Read GPS data from UART and update internal state.

        Returns:
            bool: True if valid GPS data was received, False otherwise.
        """
        sentences = self.read_buffer()
        updated = False

        for sentence in sentences:
            if sentence.startswith("$GPGGA") or sentence.startswith("$GNGGA"):
                data = self._parse_gga(sentence)
                if data:
                    if "latitude" in data:
                        self._latitude = data["latitude"]
                    if "longitude" in data:
                        self._longitude = data["longitude"]
                    if "altitude" in data:
                        self._altitude = data["altitude"]
                    if "satellites" in data:
                        self._satellites = data["satellites"]
                    if "time" in data:
                        self._time = data["time"]
                    updated = True

        return updated

    def read(self, info="all"):
        """
        Read GPS data and return requested information.

        Args:
            info: Information to return ("latitude", "longitude", "altitude",
                  "satellites", "time", "all").

        Returns:
            dict or value: Requested info or dict with all data if info="all".
        """
        self.update()

        if info == "all":
            return {
                "latitude": self._latitude,
                "longitude": self._longitude,
                "altitude": self._altitude,
                "satellites": self._satellites,
                "time": self._time
            }
        elif info == "latitude":
            return self._latitude
        elif info == "longitude":
            return self._longitude
        elif info == "altitude":
            return self._altitude
        elif info == "satellites":
            return self._satellites
        elif info == "time":
            return self._time
        else:
            return None

    @property
    def latitude(self):
        """Current latitude in decimal degrees (negative for South)."""
        return self._latitude

    @property
    def longitude(self):
        """Current longitude in decimal degrees (negative for West)."""
        return self._longitude

    @property
    def altitude(self):
        """Current altitude in meters."""
        return self._altitude

    @property
    def satellites(self):
        """Number of satellites in use."""
        return self._satellites

    @property
    def time(self):
        """UTC time as HH:MM:SS string."""
        return self._time

    @property
    def has_fix(self):
        """True if GPS has a valid position fix."""
        return self._latitude is not None and self._longitude is not None

    @property
    def position(self):
        """Tuple of (latitude, longitude) or None if no fix."""
        if self.has_fix:
            return (self._latitude, self._longitude)
        return None


def version():
    return "1.0.0"

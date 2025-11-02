"""
Printer discovery service for automatic network detection.
Supports Bambu Lab printers (via SSDP) and Prusa printers (via mDNS/Bonjour).
"""
import asyncio
import socket
import struct
import netifaces
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

try:
    from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False

try:
    from ssdpy import SSDPClient
    SSDP_AVAILABLE = True
except ImportError:
    SSDP_AVAILABLE = False

logger = structlog.get_logger()


class DiscoveredPrinter:
    """Represents a discovered printer on the network."""

    def __init__(
        self,
        printer_type: str,
        name: str,
        ip_address: str,
        hostname: str,
        model: Optional[str] = None,
        serial: Optional[str] = None
    ):
        self.printer_type = printer_type  # "bambu" or "prusa"
        self.name = name
        self.ip_address = ip_address
        self.hostname = hostname
        self.model = model
        self.serial = serial
        self.discovered_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "type": self.printer_type,
            "name": self.name,
            "ip": self.ip_address,
            "hostname": self.hostname,
            "model": self.model,
            "serial": self.serial,
            "discovered_at": self.discovered_at.isoformat()
        }


class PrusaMDNSListener(ServiceListener):
    """Listener for Prusa printer mDNS services."""

    def __init__(self):
        self.printers: List[DiscoveredPrinter] = []

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            try:
                # Extract IP address
                if info.addresses:
                    ip_address = socket.inet_ntoa(info.addresses[0])
                else:
                    logger.warning("No IP address found for Prusa printer", name=name)
                    return

                # Extract hostname
                hostname = name.replace(f'.{type_}', '')

                # Try to determine if it's a PrusaLink printer
                # PrusaLink typically advertises on _http._tcp.local.
                # We can check properties for PrusaLink-specific indicators
                properties = {}
                if info.properties:
                    properties = {
                        k.decode('utf-8'): v.decode('utf-8') if isinstance(v, bytes) else v
                        for k, v in info.properties.items()
                    }

                # Check if this is actually a Prusa printer
                # PrusaLink may have specific properties or we can check the hostname pattern
                is_prusa = (
                    'prusa' in hostname.lower() or
                    'prusalink' in properties.get('path', '').lower() or
                    'mk4' in hostname.lower() or
                    'mk3' in hostname.lower() or
                    'core' in hostname.lower()
                )

                if is_prusa:
                    printer = DiscoveredPrinter(
                        printer_type="prusa",
                        name=hostname,
                        ip_address=ip_address,
                        hostname=f"{hostname}.local",
                        model=properties.get('model')
                    )
                    self.printers.append(printer)
                    logger.info("Discovered Prusa printer",
                               name=hostname, ip=ip_address)

            except Exception as e:
                logger.error("Error processing Prusa discovery",
                           name=name, error=str(e))

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        pass

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        pass


class DiscoveryService:
    """Service for discovering printers on the local network."""

    def __init__(self, timeout: int = 10):
        """
        Initialize discovery service.

        Args:
            timeout: Discovery timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.discovered_printers: List[DiscoveredPrinter] = []

    async def discover_all(
        self,
        interface: Optional[str] = None,
        configured_ips: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Discover all printers on the network.

        Args:
            interface: Network interface to use (None for auto-detect)
            configured_ips: List of already configured printer IPs for duplicate detection

        Returns:
            Dictionary with discovered printers and scan metadata
        """
        start_time = datetime.utcnow()
        errors = []

        # Reset discovered printers
        self.discovered_printers = []

        # Run both discovery methods concurrently
        tasks = []

        if SSDP_AVAILABLE:
            tasks.append(self._discover_bambu_ssdp(interface))
        else:
            errors.append("SSDP library not available - Bambu Lab discovery disabled")
            logger.warning("SSDP library (ssdpy) not available")

        if ZEROCONF_AVAILABLE:
            tasks.append(self._discover_prusa_mdns(interface))
        else:
            errors.append("mDNS library not available - Prusa discovery disabled")
            logger.warning("mDNS library (zeroconf) not available")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and collect errors
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                    logger.error("Discovery task failed", error=str(result))

        # Mark printers that are already configured
        configured_ips_set = set(configured_ips or [])
        for printer in self.discovered_printers:
            printer.already_added = printer.ip_address in configured_ips_set

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return {
            "discovered": [p.to_dict() for p in self.discovered_printers],
            "scan_duration_ms": duration_ms,
            "errors": errors,
            "timestamp": end_time.isoformat()
        }

    async def _discover_bambu_ssdp(self, interface: Optional[str] = None) -> None:
        """
        Discover Bambu Lab printers using SSDP protocol.

        Bambu Lab printers broadcast on:
        - Multicast: 239.255.255.250
        - Ports: 1990, 2021
        - Service Type: urn:bambulab-com:device:3dprinter:1
        """
        try:
            logger.info("Starting Bambu Lab SSDP discovery")

            # Create SSDP client
            # Note: We need to listen on both ports 1990 and 2021
            # We'll use a custom implementation since ssdpy might not support this
            await self._ssdp_discover_bambu_custom(interface)

        except Exception as e:
            logger.error("Bambu SSDP discovery failed", error=str(e))
            raise

    async def _ssdp_discover_bambu_custom(self, interface: Optional[str] = None) -> None:
        """
        Custom SSDP implementation for Bambu Lab printers.
        Listens for SSDP NOTIFY messages on ports 1990 and 2021.
        """
        try:
            # Create UDP socket for multicast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)  # Make socket non-blocking for async

            # Bind to SSDP port (we'll try port 1990 first)
            sock.bind(('', 1990))

            # Join multicast group 239.255.255.250
            mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Listen for SSDP messages
            discovered_ips = set()
            start_time = asyncio.get_event_loop().time()
            loop = asyncio.get_event_loop()

            while (loop.time() - start_time) < self.timeout:
                try:
                    # Use loop.sock_recv for async socket reading
                    data = await asyncio.wait_for(
                        loop.sock_recv(sock, 4096),
                        timeout=0.5  # Short timeout to check time condition
                    )

                    # Get peer address (we need to decode the message to find it)
                    message = data.decode('utf-8', errors='ignore')

                    # Check if this is a Bambu Lab printer
                    if 'bambulab-com:device:3dprinter' in message.lower():
                        # Extract IP from message headers
                        ip_address = None
                        for line in message.split('\n'):
                            if line.upper().startswith('LOCATION:'):
                                # Try to extract IP from LOCATION header
                                # Format: LOCATION: http://192.168.1.100:port/
                                import re
                                match = re.search(r'://(\d+\.\d+\.\d+\.\d+)', line)
                                if match:
                                    ip_address = match.group(1)
                                    break

                        if ip_address and ip_address not in discovered_ips:
                            discovered_ips.add(ip_address)

                            # Extract printer info from SSDP message
                            name = self._extract_ssdp_field(message, 'SERVER') or f"Bambu Lab Printer ({ip_address})"
                            model = self._extract_ssdp_field(message, 'MODEL')
                            serial = self._extract_ssdp_field(message, 'USN')

                            printer = DiscoveredPrinter(
                                printer_type="bambu",
                                name=name,
                                ip_address=ip_address,
                                hostname=ip_address,  # Bambu doesn't use mDNS hostname
                                model=model,
                                serial=serial
                            )
                            self.discovered_printers.append(printer)
                            logger.info("Discovered Bambu Lab printer",
                                       ip=ip_address, name=name)

                except asyncio.TimeoutError:
                    # No data received in this iteration, continue
                    continue
                except Exception as e:
                    logger.debug("SSDP receive error", error=str(e))
                    continue

            sock.close()
            logger.info("Bambu SSDP discovery completed",
                       count=len(discovered_ips))

        except Exception as e:
            logger.error("Custom SSDP discovery failed", error=str(e))
            raise

    def _extract_ssdp_field(self, message: str, field: str) -> Optional[str]:
        """Extract a field from SSDP message."""
        try:
            for line in message.split('\n'):
                if line.startswith(f'{field}:'):
                    return line.split(':', 1)[1].strip()
        except Exception:
            pass
        return None

    async def _discover_prusa_mdns(self, interface: Optional[str] = None) -> None:
        """
        Discover Prusa printers using mDNS/Bonjour.

        Prusa printers advertise via mDNS with .local hostnames.
        We look for _http._tcp.local. services.
        """
        try:
            logger.info("Starting Prusa mDNS discovery")

            zc = Zeroconf()
            listener = PrusaMDNSListener()

            # Browse for HTTP services (PrusaLink advertises as HTTP)
            # We may also want to look for _octoprint._tcp.local.
            services = ["_http._tcp.local.", "_octoprint._tcp.local."]

            browsers = []
            for service in services:
                browser = ServiceBrowser(zc, service, listener)
                browsers.append(browser)

            # Wait for discovery timeout
            await asyncio.sleep(self.timeout)

            # Add discovered printers to our list
            self.discovered_printers.extend(listener.printers)

            # Cleanup
            for browser in browsers:
                browser.cancel()
            zc.close()

            logger.info("Prusa mDNS discovery completed",
                       count=len(listener.printers))

        except Exception as e:
            logger.error("Prusa mDNS discovery failed", error=str(e))
            raise

    @staticmethod
    def get_network_interfaces() -> List[Dict[str, str]]:
        """
        Get list of available network interfaces.

        Returns:
            List of interfaces with name and IP address
        """
        interfaces = []

        try:
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)

                # Get IPv4 address
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        if ip and not ip.startswith('127.'):
                            interfaces.append({
                                "name": iface,
                                "ip": ip,
                                "is_default": False  # Will be set by caller
                            })
        except Exception as e:
            logger.error("Failed to get network interfaces", error=str(e))

        return interfaces

    @staticmethod
    def get_default_interface() -> Optional[str]:
        """
        Get the default network interface (most likely to have printers).

        Returns:
            Interface name or None
        """
        try:
            # Get default gateway
            gateways = netifaces.gateways()
            default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)

            if default_gateway:
                return default_gateway[1]  # Interface name

        except Exception as e:
            logger.error("Failed to get default interface", error=str(e))

        return None

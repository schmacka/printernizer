"""
Bambu Lab status extractor.

Extracts and processes status information from Bambu Lab printers,
breaking down the large status method into focused, testable components.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class TemperatureData:
    """Temperature readings from printer."""

    bed_temp: float = 0.0
    """Current bed temperature (°C)"""

    bed_target: float = 0.0
    """Target bed temperature (°C)"""

    nozzle_temp: float = 0.0
    """Current nozzle temperature (°C)"""

    nozzle_target: float = 0.0
    """Target nozzle temperature (°C)"""


@dataclass
class ProgressData:
    """Print progress information."""

    current_layer: int = 0
    """Current layer being printed"""

    total_layers: int = 0
    """Total number of layers"""

    percent_complete: int = 0
    """Percentage complete (0-100)"""

    remaining_time_minutes: Optional[int] = None
    """Estimated remaining time in minutes"""

    elapsed_time_minutes: Optional[int] = None
    """Elapsed print time in minutes"""


@dataclass
class StateData:
    """Printer state information."""

    state: str = "UNKNOWN"
    """Printer state name"""

    message: str = ""
    """Status message"""

    current_job: Optional[str] = None
    """Name of current job"""

    current_job_file_id: Optional[str] = None
    """File ID of current job"""

    current_job_has_thumbnail: bool = False
    """Whether current job has a thumbnail"""

    print_start_time: Optional[datetime] = None
    """When the print started"""

    estimated_end_time: Optional[datetime] = None
    """Estimated completion time"""


class BambuStatusExtractor:
    """Extracts status information from Bambu Lab API responses.

    Breaks down the large status extraction logic into focused methods
    for temperature, progress, and state data.
    """

    def __init__(self, printer_id: str, file_service=None):
        """Initialize status extractor.

        Args:
            printer_id: Unique identifier for the printer
            file_service: Optional file service for looking up file IDs
        """
        self.printer_id = printer_id
        self.file_service = file_service
        self.logger = logger.bind(printer_id=printer_id)

    def extract_temperature_data(self, client: Any) -> TemperatureData:
        """Extract all temperature-related data from client.

        Args:
            client: Bambu Lab API client

        Returns:
            TemperatureData with current readings
        """
        bed_temp = self._safe_get_temp(
            lambda: client.get_bed_temperature(),
            "bed temperature"
        )

        bed_target = self._safe_get_temp(
            lambda: client.get_bed_target_temperature(),
            "bed target temperature"
        )

        nozzle_temp = self._safe_get_temp(
            lambda: client.get_nozzle_temperature(),
            "nozzle temperature"
        )

        nozzle_target = self._safe_get_temp(
            lambda: client.get_nozzle_target_temperature(),
            "nozzle target temperature"
        )

        return TemperatureData(
            bed_temp=bed_temp,
            bed_target=bed_target,
            nozzle_temp=nozzle_temp,
            nozzle_target=nozzle_target
        )

    def extract_progress_data(self, client: Any) -> ProgressData:
        """Extract all progress-related data from client.

        Args:
            client: Bambu Lab API client

        Returns:
            ProgressData with current progress info
        """
        current_layer = self._safe_get_int(
            lambda: client.get_current_layer(),
            "current layer"
        )

        total_layers = self._safe_get_int(
            lambda: client.get_total_layers(),
            "total layers"
        )

        percent_complete = self._safe_get_int(
            lambda: client.get_progress(),
            "progress"
        )

        remaining_time_minutes = self._safe_get_int(
            lambda: client.get_remaining_time(),
            "remaining time"
        )

        # Calculate elapsed time if we have start time
        elapsed_time_minutes = None
        try:
            start_time_str = client.get_start_time() if hasattr(client, 'get_start_time') else None
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                elapsed = datetime.now() - start_time
                elapsed_time_minutes = int(elapsed.total_seconds() / 60)
        except Exception as e:
            self.logger.debug("Could not calculate elapsed time", error=str(e))

        return ProgressData(
            current_layer=current_layer,
            total_layers=total_layers,
            percent_complete=percent_complete,
            remaining_time_minutes=remaining_time_minutes,
            elapsed_time_minutes=elapsed_time_minutes
        )

    def extract_state_data(self, client: Any) -> StateData:
        """Extract all state-related data from client.

        Args:
            client: Bambu Lab API client

        Returns:
            StateData with current state info
        """
        state = self._safe_get_string(
            lambda: client.get_state(),
            "state",
            default="UNKNOWN"
        )

        current_job = self._safe_get_string(
            lambda: client.get_current_file(),
            "current file"
        )

        # Look up file ID if we have file service
        current_job_file_id = None
        current_job_has_thumbnail = False

        if current_job and self.file_service:
            try:
                file_record = self.file_service.get_file_by_name(current_job)
                if file_record:
                    current_job_file_id = file_record.get('id')
                    current_job_has_thumbnail = bool(file_record.get('has_thumbnail'))
            except Exception as e:
                self.logger.debug(
                    "Could not look up file ID",
                    filename=current_job,
                    error=str(e)
                )

        # Calculate print times
        print_start_time = None
        estimated_end_time = None

        try:
            start_time_str = client.get_start_time() if hasattr(client, 'get_start_time') else None
            if start_time_str:
                print_start_time = datetime.fromisoformat(start_time_str)

                # Calculate estimated end time if we have remaining time
                remaining_minutes = client.get_remaining_time()
                if remaining_minutes and remaining_minutes > 0:
                    estimated_end_time = datetime.now() + timedelta(minutes=remaining_minutes)

        except Exception as e:
            self.logger.debug("Could not parse print times", error=str(e))

        # Create message from state
        message = f"Bambu status: {state}"
        if current_job:
            message = f"{message} - Printing: {current_job}"

        return StateData(
            state=state,
            message=message,
            current_job=current_job,
            current_job_file_id=current_job_file_id,
            current_job_has_thumbnail=current_job_has_thumbnail,
            print_start_time=print_start_time,
            estimated_end_time=estimated_end_time
        )

    def _safe_get_temp(self, getter_func, field_name: str, default: float = 0.0) -> float:
        """Safely get temperature value with error handling.

        Args:
            getter_func: Function to call to get the value
            field_name: Name of field for logging
            default: Default value if extraction fails

        Returns:
            Temperature value or default
        """
        try:
            value = getter_func()
            if value is None:
                return default
            return float(value)
        except (ConnectionError, TimeoutError) as e:
            self.logger.debug(
                f"Connection error getting {field_name}",
                error=str(e)
            )
            return default
        except (ValueError, TypeError) as e:
            self.logger.debug(
                f"Invalid {field_name} value",
                error=str(e)
            )
            return default
        except Exception as e:
            self.logger.warning(
                f"Unexpected error getting {field_name}",
                error=str(e),
                error_type=type(e).__name__
            )
            return default

    def _safe_get_int(self, getter_func, field_name: str, default: int = 0) -> int:
        """Safely get integer value with error handling.

        Args:
            getter_func: Function to call to get the value
            field_name: Name of field for logging
            default: Default value if extraction fails

        Returns:
            Integer value or default
        """
        try:
            value = getter_func()
            if value is None:
                return default
            return int(value)
        except (ConnectionError, TimeoutError) as e:
            self.logger.debug(
                f"Connection error getting {field_name}",
                error=str(e)
            )
            return default
        except (ValueError, TypeError) as e:
            self.logger.debug(
                f"Invalid {field_name} value",
                error=str(e)
            )
            return default
        except Exception as e:
            self.logger.warning(
                f"Unexpected error getting {field_name}",
                error=str(e),
                error_type=type(e).__name__
            )
            return default

    def _safe_get_string(
        self,
        getter_func,
        field_name: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """Safely get string value with error handling.

        Args:
            getter_func: Function to call to get the value
            field_name: Name of field for logging
            default: Default value if extraction fails

        Returns:
            String value or default
        """
        try:
            value = getter_func()
            if value is None:
                return default
            return str(value)
        except (ConnectionError, TimeoutError) as e:
            self.logger.debug(
                f"Connection error getting {field_name}",
                error=str(e)
            )
            return default
        except Exception as e:
            self.logger.warning(
                f"Unexpected error getting {field_name}",
                error=str(e),
                error_type=type(e).__name__
            )
            return default

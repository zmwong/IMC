from scripts.libs.utils.singleton_meta import SingletonMeta
from scripts.libs.utils.cpu_id import CPUID
from scripts.libs.data_handlers.memory_data import MemoryData
from scripts.libs.utils.environment import EnvironmentInfo
from scripts.libs.system_handler import SystemHandler
from scripts.libs.components.loggers.logger_manager import (
    LoggerManager,
    LoggerManagerThread,
)
import ctypes
import sys
import os


class MemoryHandler(metaclass=SingletonMeta):
    def retrieve_cache_information(self, desired_level, per_core=True):
        """
        Retrieves the total cache size for caches of the specified level.

        desired_level: 1 for L1, 2 for L2, etc.
        per_core: If True, returns the size of a single cache instance (for one core).
                  Otherwise, sums all instances.

        The CPUID leaf 4 instruction returns cache details for various subleaves.
        EAX bits [4:0] contain the cache type (0 indicates no further caches),
        and bits [7:5] contain the cache level.
        The cache size is computed as:
            cache_size = (line_size) * (ways) * (partitions) * (sets)
        where each value is encoded as N = (value from register + 1).
        """
        cpuid = CPUID()
        leaf = 0x04  # Cache parameters leaf
        subleaf = 0
        total_cache = 0
        single_instance_value = 0
        # Loop through subleaves until CPUID indicates no more caches.
        while True:
            regs = cpuid.get_flag_dynamic(leaf, subleaf)
            eax = regs.get("eax", 0)
            cache_type = eax & 0x1F  # bits 4:0, 0 = no cache
            if cache_type == 0:
                break
            cache_level = (eax >> 5) & 0x7  # bits 7:5 indicate level (1,2,3...)
            if cache_level == desired_level:
                ebx = regs["ebx"]
                ecx = regs["ecx"]
                line_size = (ebx & 0xFFF) + 1
                partitions = ((ebx >> 12) & 0x3FF) + 1
                ways = ((ebx >> 22) & 0x3FF) + 1
                sets = ecx + 1
                cache_size = ways * partitions * line_size * sets
                total_cache += cache_size
                if single_instance_value == 0:
                    single_instance_value = cache_size
                # Save detailed info (if desired)
                MemoryData().data[f"l{desired_level}_line_size"] = line_size
                MemoryData().data[f"l{desired_level}_ways"] = ways
                MemoryData().data[f"l{desired_level}_partitions"] = partitions
                MemoryData().data[f"l{desired_level}_sets"] = sets
                MemoryData().data[f"l{desired_level}_size"] = cache_size
                # If per_core is desired, stop after the first instance.
                if per_core:
                    return single_instance_value
            subleaf += 1
        return total_cache

    def set_l1_cache(self):
        # For L1, desired_level is 1.
        self.l1_cache = self.retrieve_cache_information(1, per_core=True)

    def set_l2_cache(self):
        # For L2, desired_level is 2.
        self.l2_cache = self.retrieve_cache_information(2, per_core=True)

    def set_l3_cache(self):
        # L3 is typically shared.
        self.l3_cache = self.retrieve_cache_information(3, per_core=True)

    def get_total_memory(self):
        """
        Retrieves the total physical memory of the system in bytes.
        Works on both Linux and Windows platforms.

        Returns:
            int: Total physical memory in bytes
        """
        if sys.platform.startswith("win"):
            # Windows implementation using GlobalMemoryStatusEx
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32 = ctypes.windll.kernel32
            if not kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                raise ctypes.WinError()
            return stat.ullTotalPhys
        else:
            # Linux implementation using sysinfo
            class Sysinfo(ctypes.Structure):
                _fields_ = [
                    ("uptime", ctypes.c_long),
                    ("loads", ctypes.c_ulong * 3),
                    ("totalram", ctypes.c_ulong),
                    ("freeram", ctypes.c_ulong),
                    ("sharedram", ctypes.c_ulong),
                    ("bufferram", ctypes.c_ulong),
                    ("totalswap", ctypes.c_ulong),
                    ("freeswap", ctypes.c_ulong),
                    ("procs", ctypes.c_ushort),
                    ("pad", ctypes.c_ushort),
                    ("totalhigh", ctypes.c_ulong),
                    ("freehigh", ctypes.c_ulong),
                    ("mem_unit", ctypes.c_uint),
                    ("_f", ctypes.c_char * 8),
                ]

            libc = ctypes.CDLL("libc.so.6")
            sysinfo = Sysinfo()
            if libc.sysinfo(ctypes.byref(sysinfo)) != 0:
                raise OSError("sysinfo() call failed")
            return sysinfo.totalram * sysinfo.mem_unit

    def get_page_size(self):
        """
        Retrieves the system memory page size in bytes.
        Works on both Linux and Windows platforms.

        Returns:
            int: System page size in bytes
        """
        if SystemHandler().os_system.platform_name == "windows":
            # Windows implementation
            kernel32 = ctypes.windll.kernel32
            system_info = ctypes.create_string_buffer(
                36
            )  # SYSTEM_INFO structure size
            kernel32.GetSystemInfo(system_info)
            # Page size is at offset 4 in the SYSTEM_INFO structure (dwPageSize)
            return ctypes.c_ulong.from_buffer(system_info, 4).value
        else:
            # Linux and SVOS implementation using os.sysconf
            try:
                return os.sysconf("SC_PAGE_SIZE")
            except (ValueError, OSError, AttributeError):
                # Fallback if sysconf fails
                libc = ctypes.CDLL("libc.so.6")
                libc.getpagesize.restype = ctypes.c_int
                return libc.getpagesize()

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.set_l1_cache()
            self.set_l2_cache()
            self.set_l3_cache()
            self.total_memory = self.get_total_memory()
            self.page_size = self.get_page_size()
            self._logged = False

    def log_memory_info(self, logger=None):
        """
        Logs memory information specifically during the initialization phase.
        Args:
            logger: StructuredLogger instance
        """
        logger.log_initialization("System Memory Information:")
        logger.log_initialization(
            f"L1 data cache (per core): {(self.l1_cache/1024):.2f} KB"
        )
        logger.log_initialization(
            f"L2 cache (per core): {(self.l2_cache/(1024*1024)):.2f} MB"
        )
        logger.log_initialization(
            f"L3 cache (total): {(self.l3_cache/(1024*1024)):.2f} MB"
        )
        logger.log_initialization(
            f"System page size: {self.page_size:,d} bytes"
        )
        logger.log_initialization(
            f"Total system memory: {(self.total_memory/(1024*1024*1024)):.2f} GB"
        )
        logger.log_initialization("")

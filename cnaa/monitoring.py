"""CNAA monitoring and health check system."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Comprehensive health check result for all CNAA components."""
    
    status: str = "healthy"  # healthy, degraded, unhealthy
    timestamp: datetime = field(default_factory=datetime.utcnow)
    components: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_component(self, name: str, status: str, details: str = ""):
        """Add component status to health report."""
        if details:
            self.components[name] = f"{status}: {details}"
        else:
            self.components[name] = status
    
    def add_error(self, error_msg: str):
        """Record an error that may affect overall status."""
        self.errors.append(error_msg)
        self._update_overall_status()
    
    def add_warning(self, warning_msg: str):
        """Record a warning without affecting status."""
        self.warnings.append(warning_msg)
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        self.metrics[name] = value
    
    def _update_overall_status(self):
        """Update overall status based on component states."""
        if len(self.errors) > 0:
            critical_errors = [e for e in self.errors if "critical" in e.lower()]
            if critical_errors:
                self.status = "unhealthy"
            else:
                self.status = "degraded"
        elif len(self.warnings) > 5:
            self.status = "degraded"
        else:
            self.status = "healthy"
    
    def summary(self) -> Dict[str, Any]:
        """Get JSON-serializable summary of health status."""
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "component_count": len(self.components),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "metrics_recorded": len(self.metrics),
            "components": self.components,
            "latest_errors": self.errors[-5:] if self.errors else []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert full health status to dictionary."""
        return {
            **self.summary(),
            "details": {
                "all_components": self.components.copy(),
                "all_errors": self.errors.copy(),
                "all_warnings": self.warnings.copy(),
                "all_metrics": self.metrics.copy()
            }
        }


class Monitor:
    """Monitoring service for CNAA with health checks and metrics collection."""
    
    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path or "./cnaa_monitor.log"
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up structured logging for monitoring."""
        try:
            import structlog
            
            structlog.configure(
                processors=[
                    structlog.stdtimeiso,
                    structlog.processors.add_log_level,
                    structlog.dev.ConsoleRenderer()
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory()
            )
            self.logger = structlog.get_logger("cnaa.monitor")
        except ImportError:
            self.logger = logging.getLogger(__name__)
    
    async def check_all_systems(self) -> HealthStatus:
        """Run comprehensive health check on all CNAA systems."""
        status = HealthStatus(status="healthy")
        
        # Check memory storage
        await self._check_memory_storage(status)
        
        # Check state storage
        await self._check_state_storage(status)
        
        # Check authentication configuration
        self._check_auth_config(status)
        
        # Check database connectivity
        await self._check_database_connectivity(status)
        
        # Check configuration
        self._check_configuration(status)
        
        return status
    
    async def _check_memory_storage(self, status: HealthStatus):
        """Check memory storage subsystem."""
        try:
            from cloud.storage.sqlite_memory_store import SQLiteMemoryStore
            
            store = SQLiteMemoryStore()
            count = store.count()
            
            status.add_component("memory_storage", "ok", f"{count} memories")
            status.record_metric("memory_count", float(count))
            
        except Exception as e:
            status.add_component("memory_storage", "error", str(e))
            status.add_error(f"Memory storage check failed: {e}")
    
    async def _check_state_storage(self, status: HealthStatus):
        """Check state storage subsystem."""
        try:
            from cloud.storage.sql_state_store import SQLStateStore
            
            store = SQLStateStore()
            count = store.count()
            
            status.add_component("state_storage", "ok", f"{count} states")
            status.record_metric("state_count", float(count))
            
        except Exception as e:
            status.add_component("state_storage", "error", str(e))
            status.add_error(f"State storage check failed: {e}")
    
    def _check_auth_config(self, status: HealthStatus):
        """Check authentication configuration."""
        try:
            from cnaa.security import SecurityConfig
            
            config = SecurityConfig()
            
            if config.auth_enabled:
                key_count = len(config.api_keys or {})
                status.add_component("authentication", "active", f"{key_count} API keys")
                
                if key_count == 0:
                    status.add_warning("Authentication enabled but no API keys configured")
            else:
                status.add_component("authentication", "disabled", "auth disabled")
                
        except Exception as e:
            status.add_component("authentication", "error", str(e))
    
    async def _check_database_connectivity(self, status: HealthStatus):
        """Check database file connectivity."""
        import sqlite3
        
        db_files = ["cnaa_memories.db", "cnaa_states.db"]
        
        for db_file in db_files:
            if Path(db_file).exists():
                try:
                    conn = sqlite3.connect(db_file)
                    conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                    conn.close()
                    
                    db_size = Path(db_file).stat().st_size / (1024 * 1024)
                    status.add_component(db_file.split(".")[0], "ok", f"{db_size:.2f} MB")
                    status.record_metric(f"{db_file}_size_mb", db_size)
                    
                except Exception as e:
                    status.add_component(db_file, "error", str(e))
                    status.add_error(f"Database check failed for {db_file}: {e}")
    
    def _check_configuration(self, status: HealthStatus):
        """Check environment configuration."""
        import os
        
        required_vars = ["CNAA_SERVER_URL"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            status.add_warning(f"Missing optional env vars: {', '.join(missing_vars)}")
        
        # Check server URL format
        server_url = os.getenv("CNAA_SERVER_URL", "")
        if server_url:
            if server_url.startswith(("http://", "https://")):
                status.add_component("configuration", "ok", "server URL valid")
            else:
                status.add_warning("Server URL may have invalid format")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of monitored metrics."""
        import os
        
        return {
            "uptime_seconds": self._get_uptime(),
            "process_memory_mb": self._get_process_memory(),
            "environment_vars_count": len(os.environ),
            "last_check": datetime.utcnow().isoformat()
        }
    
    def _get_uptime(self) -> float:
        """Estimate system uptime."""
        # Simple uptime estimation from process start time
        import psutil
        
        try:
            process = psutil.Process()
            start_time = process.create_time()
            uptime = (datetime.now().timestamp() - start_time) / 3600
            return round(uptime, 2)
        except:
            return 0.0
    
    def _get_process_memory(self) -> float:
        """Get current process memory usage."""
        import psutil
        
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            return round(mem_info.rss / (1024 * 1024), 2)
        except:
            return 0.0
    
    async def log_health_event(self, event_type: str, message: str, details: Dict = None):
        """Log a health event with context."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "message": message,
            "source": "cnaa.monitor"
        }
        
        if details:
            event["details"] = details
        
        if event_type == "error":
            logger.error(json.dumps(event))
        elif event_type == "warning":
            logger.warning(json.dumps(event))
        else:
            logger.info(json.dumps(event))
    
    def generate_report(self) -> str:
        """Generate human-readable health report."""
        import traceback
        
        report_lines = [
            "=" * 60,
            "CNAA Health Report",
            f"Generated: {datetime.utcnow().isoformat()}",
            "=" * 60
        ]
        
        report_lines.append("\n📊 System Status:")
        status = asyncio.run(self.check_all_systems())
        
        emoji_map = {
            "healthy": "✅",
            "degraded": "⚠️", 
            "unhealthy": "❌"
        }
        report_lines.append(f"   Overall: {emoji_map.get(status.status, '❓')} {status.status.upper()}")
        
        report_lines.append(f"\n🔧 Components ({len(status.components)} checked):")
        for name, detail in status.components.items():
            report_lines.append(f"   • {name}: {detail}")
        
        if status.errors:
            report_lines.append(f"\n❌ Errors ({len(status.errors)}):")
            for error in status.errors[:5]:
                report_lines.append(f"   ✗ {error}")
        
        if status.warnings:
            report_lines.append(f"\n⚠️ Warnings ({len(status.warnings)}):")
            for warning in status.warnings[:5]:
                report_lines.append(f"   ! {warning}")
        
        report_lines.append("\n📈 Key Metrics:")
        for name, value in status.metrics.items():
            report_lines.append(f"   {name}: {value:.2f}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)


# Async helper for convenience functions
async def get_health_status() -> HealthStatus:
    """Quick function to get current health status."""
    monitor = Monitor()
    return await monitor.check_all_systems()


def quick_check() -> str:
    """Quick command-line style health check."""
    monitor = Monitor()
    return monitor.generate_report()


if __name__ == "__main__":
    print(quick_check())

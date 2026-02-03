"""
Immutable audit logging for legal compliance and forensics.
All actions logged with cryptographic integrity.
"""

import json
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class AuditLogger:
    """
    Tamper-evident audit logging.
    Critical for legal admissibility of evidence.
    """
    
    def __init__(self, config: Dict):
        self.log_dir = Path(config.get('log_path', 'data/logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = config.get('retention_days', 365)
        self.encryption_enabled = config.get('encryption', True)
        
        # Chain of custody - each entry hashes previous
        self.chain_hash: Optional[str] = None
        self._load_chain_state()
        
        self.current_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m')}.log"
        
        logger.info("AuditLogger initialized")
    
    def _load_chain_state(self) -> None:
        """Load last hash for chain continuity"""
        # Find most recent log file
        log_files = sorted(self.log_dir.glob("audit_*.log"))
        if log_files:
            try:
                with open(log_files[-1], 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        self.chain_hash = last_entry.get('chain_hash')
            except Exception as e:
                logger.error(f"Failed to load chain state: {e}")
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Log event with cryptographic chaining.
        Returns entry hash.
        """
        timestamp = datetime.utcnow().isoformat()
        
        entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "previous_hash": self.chain_hash
        }
        
        # Calculate entry hash
        entry_str = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        
        # Create chain hash (entry_hash + previous_hash)
        if self.chain_hash:
            chain_input = f"{entry_hash}:{self.chain_hash}"
        else:
            chain_input = entry_hash
        self.chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()
        
        # Add hashes to entry
        entry["entry_hash"] = entry_hash
        entry["chain_hash"] = self.chain_hash
        
        # Write to log
        with open(self.current_log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        return entry_hash
    
    def verify_chain(self, log_file: Optional[Path] = None) -> bool:
        """
        Verify integrity of audit chain.
        """
        if log_file is None:
            log_file = self.current_log_file
        
        if not log_file.exists():
            return True
        
        previous_hash = None
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    entry_hash = entry.get('entry_hash')
                    stored_previous = entry.get('previous_hash')
                    stored_chain = entry.get('chain_hash')
                    
                    # Verify previous hash linkage
                    if previous_hash is not None and stored_previous != previous_hash:
                        logger.error(f"Chain broken at line {line_num}")
                        return False
                    
                    # Recalculate chain hash
                    entry_data = {
                        "timestamp": entry['timestamp'],
                        "event_type": entry['event_type'],
                        "data": entry['data'],
                        "previous_hash": stored_previous
                    }
                    calc_entry_hash = hashlib.sha256(
                        json.dumps(entry_data, sort_keys=True).encode()
                    ).hexdigest()
                    
                    if calc_entry_hash != entry_hash:
                        logger.error(f"Entry hash mismatch at line {line_num}")
                        return False
                    
                    previous_hash = stored_chain
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON at line {line_num}")
                    return False
        
        return True
    
    def get_events(
        self, 
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> list:
        """Query audit log"""
        events = []
        
        for log_file in self.log_dir.glob("audit_*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        # Filter by type
                        if event_type and entry['event_type'] != event_type:
                            continue
                        
                        # Filter by time
                        if start_time and entry['timestamp'] < start_time:
                            continue
                        if end_time and entry['timestamp'] > end_time:
                            continue
                        
                        events.append(entry)
                    except:
                        continue
        
        return sorted(events, key=lambda x: x['timestamp'])
    
    def close(self) -> None:
        """Finalize logging"""
        self.log_event("system_shutdown", {"status": "graceful"})
        logger.info("AuditLogger closed")
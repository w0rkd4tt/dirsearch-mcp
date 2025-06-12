"""
Data formats for Dirsearch MCP integration
Provides standardized data structures for exchange
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json


@dataclass
class ScanOptions:
    """Options for directory scanning"""
    wordlist: str = "common.txt"
    extensions: List[str] = field(default_factory=lambda: ["php", "html", "js", "txt"])
    threads: int = 10
    timeout: int = 10
    delay: float = 0
    user_agent: str = "Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)"
    follow_redirects: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None
    max_retries: int = 3
    exclude_status: Optional[str] = "404"
    include_status: Optional[str] = None
    use_mcp: bool = True  # Use MCP intelligence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanOptions':
        """Create from dictionary"""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ScanOptions':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class TargetData:
    """Target analysis data"""
    url: str
    domain: str
    server_type: Optional[str] = None
    technology_stack: List[str] = field(default_factory=list)
    detected_cms: Optional[str] = None
    security_headers: Dict[str, str] = field(default_factory=dict)
    response_patterns: Dict[str, Any] = field(default_factory=dict)
    _internal: Any = field(default=None, repr=False)  # Internal reference
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data.pop('_internal', None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetData':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ResultData:
    """Individual scan result"""
    path: str
    status: int
    size: int
    content_type: Optional[str] = None
    redirect_location: Optional[str] = None
    response_time: Optional[float] = None
    headers: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultData':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @property
    def is_success(self) -> bool:
        """Check if result is successful"""
        return self.status in [200, 201]
    
    @property
    def is_redirect(self) -> bool:
        """Check if result is redirect"""
        return self.status in [301, 302, 303, 307, 308]
    
    @property
    def is_auth_required(self) -> bool:
        """Check if authentication is required"""
        return self.status in [401, 403]


@dataclass
class ScanData:
    """Complete scan data"""
    target: str
    target_info: TargetData
    options: ScanOptions
    results: List[ResultData]
    statistics: Dict[str, Any]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: float = 0
    mcp_mode: str = "LOCAL"
    mcp_decisions: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target': self.target,
            'target_info': self.target_info.to_dict(),
            'options': self.options.to_dict(),
            'results': [r.to_dict() for r in self.results],
            'statistics': self.statistics,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'mcp_mode': self.mcp_mode,
            'mcp_decisions': self.mcp_decisions,
            'errors': self.errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanData':
        """Create from dictionary"""
        return cls(
            target=data['target'],
            target_info=TargetData.from_dict(data['target_info']),
            options=ScanOptions.from_dict(data['options']),
            results=[ResultData.from_dict(r) for r in data['results']],
            statistics=data['statistics'],
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            duration=data.get('duration', 0),
            mcp_mode=data.get('mcp_mode', 'LOCAL'),
            mcp_decisions=data.get('mcp_decisions', []),
            errors=data.get('errors', [])
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ScanData':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    @property
    def total_findings(self) -> int:
        """Total number of findings"""
        return len(self.results)
    
    @property
    def successful_findings(self) -> List[ResultData]:
        """Get successful findings (2xx status)"""
        return [r for r in self.results if r.is_success]
    
    @property
    def auth_required_findings(self) -> List[ResultData]:
        """Get auth required findings (401/403)"""
        return [r for r in self.results if r.is_auth_required]
    
    @property
    def redirect_findings(self) -> List[ResultData]:
        """Get redirect findings (3xx)"""
        return [r for r in self.results if r.is_redirect]
    
    def get_findings_by_status(self, status: Union[int, List[int]]) -> List[ResultData]:
        """Get findings by status code(s)"""
        if isinstance(status, int):
            status = [status]
        return [r for r in self.results if r.status in status]
    
    def get_findings_by_extension(self, extension: str) -> List[ResultData]:
        """Get findings by file extension"""
        return [r for r in self.results if r.path.endswith(f'.{extension}')]
    
    def export_to_file(self, filepath: str, format: str = 'json'):
        """Export scan data to file"""
        if format == 'json':
            with open(filepath, 'w') as f:
                f.write(self.to_json())
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @classmethod
    def import_from_file(cls, filepath: str, format: str = 'json') -> 'ScanData':
        """Import scan data from file"""
        if format == 'json':
            with open(filepath, 'r') as f:
                return cls.from_json(f.read())
        else:
            raise ValueError(f"Unsupported format: {format}")


@dataclass
class ExchangeFormat:
    """
    Standard exchange format for third-party tools
    Compatible with common security tool formats
    """
    version: str = "1.0"
    tool: str = "dirsearch-mcp"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    scan_data: Optional[ScanData] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version,
            'tool': self.tool,
            'timestamp': self.timestamp,
            'scan_data': self.scan_data.to_dict() if self.scan_data else None,
            'metadata': self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_xml(self) -> str:
        """Convert to XML format (for tools that prefer XML)"""
        # Simple XML conversion
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<scan version="{self.version}" tool="{self.tool}" timestamp="{self.timestamp}">\n'
        
        if self.scan_data:
            xml += f'  <target>{self.scan_data.target}</target>\n'
            xml += f'  <findings count="{self.scan_data.total_findings}">\n'
            
            for result in self.scan_data.results:
                xml += f'    <finding>\n'
                xml += f'      <path>{result.path}</path>\n'
                xml += f'      <status>{result.status}</status>\n'
                xml += f'      <size>{result.size}</size>\n'
                xml += f'    </finding>\n'
                
            xml += f'  </findings>\n'
            
        xml += '</scan>\n'
        return xml
    
    def to_csv(self) -> str:
        """Convert to CSV format"""
        if not self.scan_data:
            return ""
            
        csv = "path,status,size,content_type,response_time\n"
        for result in self.scan_data.results:
            csv += f'"{result.path}",{result.status},{result.size},"{result.content_type or ""}",{result.response_time or 0}\n'
            
        return csv
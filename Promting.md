# Dirsearch-MCP Development Prompts

## Giai Đoạn 1: Khởi Tạo Project và Cấu Trúc

### Prompt 1.1: Project Initialization
```
Tạo một project Python tên "dirsearch-mcp" với cấu trúc thư mục sau:

dirsearch-mcp/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dirsearch_engine.py
│   │   └── mcp_coordinator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── reporter.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── interactive_menu.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── tests/
│   ├── __init__.py
│   ├── test_dirsearch_engine.py
│   ├── test_mcp_coordinator.py
│   └── test_integration.py
├── log/
├── report/
├── requirements.txt
├── setup.py
└── main.py

Yêu cầu:
- Tạo file requirements.txt với các thư viện cần thiết cho pentesting tool
- Tạo setup.py cho local installation
- Tạo __init__.py files với proper imports
- Tạo main.py làm entry point
- Không cài đặt bất kỳ package nào, chỉ tạo cấu trúc
```

### Prompt 1.2: Configuration Setup
```
Tạo file src/config/settings.py với các cấu hình sau:

Yêu cầu:
- DEFAULT_WORDLISTS: paths tới các wordlist phổ biến
- DEFAULT_THREADS: số thread mặc định
- DEFAULT_TIMEOUT: timeout cho requests
- LOG_CONFIG: cấu hình logging (level, format, file paths)
- REPORT_CONFIG: cấu hình report formats (json, html, markdown)
- MCP_CONFIG: cấu hình cho MCP coordinator
- DIRSEARCH_CONFIG: migrate config từ dirsearch original

Tất cả config phải có khả năng override từ CLI arguments và environment variables.
Tạo class ConfigManager để quản lý tất cả configs với validation.
```

## Giai Đoạn 2: Core Engine Development

### Prompt 2.1: Dirsearch Engine Migration
```
Migrate dirsearch functionality vào src/core/dirsearch_engine.py:

Yêu cầu:
- Tạo class DirsearchEngine kế thừa chức năng chính từ dirsearch
- Implement methods:
  - scan_target(url, wordlist, options)
  - parse_response(response)
  - filter_results(results, filters)
  - get_scan_statistics()
- Hỗ trợ tất cả options của dirsearch gốc:
  - extensions, status codes, threads, timeout
  - recursive scanning, subdirectory detection
  - custom headers, cookies, authentication
- Thread-safe implementation
- Progress tracking và callback support
- Error handling và retry logic
- Integration points cho MCP coordinator

Không thêm features mới, chỉ migrate và optimize existing functionality.
Focus vào clean code và testability.
```

### Prompt 2.2: MCP Coordinator Implementation
```
Tạo src/core/mcp_coordinator.py - trái tim của intelligent automation với AI agent integration:

Yêu cầu:
- Class MCPCoordinator với dual intelligence modes:
  - LOCAL MODE: Rule-based decision making
  - AI AGENT MODE: API integration với ChatGPT/DeepSeek (nếu có api_key)

- Core Methods:
  - analyze_target(url) -> target_info
  - generate_scan_plan(target_info) -> scan_tasks  
  - execute_scan_plan(scan_tasks) -> results
  - optimize_parameters(target_info) -> optimized_config

- AI Agent Integration:
  - Class AIAgentConnector để kết nối ChatGPT/DeepSeek API
  - Method detect_ai_availability() -> check api_key validity
  - Method query_ai_agent(context, question) -> ai_response
  - Fallback mechanism: AI fail -> local rules

- Intelligence Capabilities:
  LOCAL MODE:
  - Rule-based technology stack detection
  - Predefined wordlist selection logic
  - Static parameter optimization rules
  
  AI AGENT MODE:
  - Send target analysis tới AI để get advanced insights
  - AI-powered wordlist recommendations
  - Dynamic parameter tuning based on AI analysis
  - Intelligent scan strategy adaptation
  - Advanced vulnerability pattern recognition

- Context-aware Decision Making:
  - Detect web server type -> AI suggests optimal strategy
  - Analyze response patterns -> AI optimizes wordlist selection
  - Monitor performance -> AI adjusts threading và timeout
  - Real-time learning từ scan results

- API Integration Structure:
  - Support multiple AI providers (ChatGPT, DeepSeek)
  - Configurable API endpoints và models
  - Rate limiting và error handling
  - Token usage optimization
  - Secure API key management

- Prompt Engineering cho AI Agents:
  - Structured prompts cho target analysis
  - Context-rich queries cho optimization decisions
  - Response parsing và validation
  - AI response caching để avoid redundant calls

- Hybrid Decision Making:
  - AI recommendations + local validation
  - Confidence scoring cho AI suggestions
  - Human override options
  - Learning từ successful scans

Real-time task coordination với detailed logging của cả local và AI decisions.
Integration với DirsearchEngine và proper error handling.

Focus vào intelligent automation, AI-enhanced decision making, và performance optimization.
```

## Giai Đoạn 3: Utility Components

### Prompt 3.1: Logging System
```
Tạo src/utils/logger.py - comprehensive logging system:

Yêu cầu:
- Class LogManager với multiple log levels và formats
- Separate loggers cho:
  - MCP decisions và task coordination
  - Dirsearch engine activities
  - Performance metrics
  - Error tracking
- Log files trong /log directory:
  - mcp_decisions.log: MCP coordination steps
  - scan_activities.log: Detailed scan logs
  - performance.log: Performance metrics
  - errors.log: Error tracking
- Console output với colors và progress indicators
- Log rotation và cleanup
- Integration với MCP coordinator để log decision making process
- Structured logging format (JSON) cho machine readability

Ensure logs cung cấp đầy đủ information để debug và audit.
```

### Prompt 3.2: Report Generation
```
Tạo src/utils/reporter.py - multi-format report generator:

Yêu cầu:
- Class ReportGenerator hỗ trợ formats: JSON, HTML, Markdown
- Report structure:
  - Executive summary
  - MCP coordination steps và decisions
  - Detailed scan results
  - Performance metrics
  - Recommendations
- Templates cho HTML reports với:
  - Interactive tables
  - Charts/graphs cho statistics
  - Responsive design
- Markdown reports với:
  - Clean formatting
  - Structured sections
  - Easy integration với documentation
- JSON reports với:
  - Machine-readable format
  - Complete data export
  - API integration friendly
- Save reports trong /report directory với timestamp
- Integration với MCP coordinator để include decision logs

Focus vào professional, detailed reporting.
```

## Giai Đoạn 4: Interactive CLI

### Prompt 4.1: Interactive Menu System
```
Tạo src/cli/interactive_menu.py - user-friendly CLI interface:

Yêu cầu:
- Class InteractiveMenu với rich console interface
- Main menu options:
  1. Quick Scan (MCP auto-configure)
  2. Advanced Scan (manual configuration)
  3. View Previous Reports
  4. Configuration Management
  5. Help & Documentation
- Sub-menus cho:
  - Target selection và validation
  - Wordlist selection
  - Advanced options configuration
  - MCP behavior tuning
- Real-time scan progress với:
  - Progress bars
  - Live statistics
  - MCP decision notifications
- Input validation và error handling
- Help system với examples
- Integration với tất cả core components

Focus vào user experience và ease of use.
```

## Giai Đoạn 5: Testing Framework

### Prompt 5.1: Unit Tests
```
Tạo comprehensive test suite:

tests/test_dirsearch_engine.py:
- Test DirsearchEngine methods
- Mock HTTP responses
- Test error handling
- Performance benchmarks

tests/test_mcp_coordinator.py:
- Test MCP decision making logic
- Test task coordination
- Test parameter optimization
- Mock target analysis

tests/test_integration.py:
- End-to-end testing
- Integration between components
- Test với real targets (controlled environment)
- Performance integration tests

Yêu cầu:
- Sử dụng pytest framework
- Mock external dependencies
- Test coverage >= 80%
- Performance benchmarks
- Fixtures cho common test data
- Parameterized tests cho multiple scenarios

Ensure tests cover edge cases và error conditions.
```

## Giai Đoạn 6: Integration và Optimization

### Prompt 6.1: Main Entry Point
```
Tạo main.py - application entry point:

Yêu cầu:
- Command line argument parsing
- Integration với InteractiveMenu
- Direct CLI mode support
- Configuration loading
- Error handling và graceful shutdown
- Signal handling (Ctrl+C)
- Version information
- Help documentation

Support cả interactive mode và direct command execution.
```

### Prompt 6.2: Module Integration
```
Tạo module integration interface để tích hợp với tools khác:

Yêu cầu:
- Export class DirsearchMCP với clean API
- Plugin architecture cho extensions
- Event hooks cho external tools
- Data exchange formats
- Example integration với wappalyzer
- Documentation cho third-party integration

Focus vào modularity và extensibility.
```

## Giai Đoạn 7: Performance Optimization

### Prompt 7.1: Performance Tuning
```
Optimize performance của toàn bộ system:

Yêu cầu:
- Profile và identify bottlenecks
- Optimize MCP decision making algorithms
- Tune threading và async operations
- Memory usage optimization
- Database/cache integration nếu cần
- Benchmark against original dirsearch
- Performance monitoring integration

Focus vào maintaining accuracy while improving speed.
```

## Giai Đoạn 8: Documentation và Deployment

### Prompt 8.1: Final Documentation
```
Tạo comprehensive documentation:

Yêu cầu:
- README.md với installation và usage
- API documentation
- Architecture overview
- Performance comparisons
- Troubleshooting guide
- Examples và use cases
- Integration guide cho third-party tools

Ensure documentation đầy đủ và dễ hiểu.
```

---

## Lưu Ý Quan Trọng Cho Mỗi Giai Đoạn:

1. **Luôn test trước khi chuyển giai đoạn tiếp theo**
2. **Maintain backward compatibility với dirsearch**
3. **Log tất cả MCP decisions để audit**
4. **Focus vào performance optimization**
5. **Ensure code quality và maintainability**
6. **Test với real-world scenarios**

## Thứ Tự Thực Hiện:
1. Chạy từng prompt theo thứ tự
2. Test thoroughly sau mỗi giai đoạn
3. Optimize performance continuously
4. Document decisions và changes
5. Validate against requirements
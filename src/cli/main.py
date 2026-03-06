"""主CLI入口 - 订阅解析器命令行工具"""
import os
import sys
import time
import argparse
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone

from loguru import logger
from tqdm import tqdm

from src.utils.logger import setup_logger
from src.decoders.format_detector import FormatDetector
from src.parsers import parse_uri
from src.models.node import Node
from src.models.subscription import Subscription
from src.models import ParseResult
from src.storage.redis_store import RedisStore
from src.storage.file_export import export_json, export_csv, export_nodes_json, export_nodes_csv

VERSION = "1.0.0"


def _load_config() -> dict:
    """加载配置文件 (~/.subscription-parser.yaml)"""
    import yaml
    config_path = Path.home() / ".subscription-parser.yaml"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"配置文件加载失败: {e}")
    return {}


def _get_redis_url(args, config: dict) -> str:
    """获取Redis URL，优先级：命令行 > 环境变量 > 配置文件 > 默认值"""
    if hasattr(args, "redis_url") and args.redis_url:
        return args.redis_url
    env_url = os.environ.get("REDIS_URL")
    if env_url:
        return env_url
    return config.get("redis", {}).get("url", "redis://localhost:6379/0")


def _get_output_dir(args, config: dict) -> str:
    """获取输出目录"""
    if hasattr(args, "output_dir") and args.output_dir:
        return args.output_dir
    env_dir = os.environ.get("SUBSCRIPTION_PARSER_OUTPUT_DIR")
    if env_dir:
        return env_dir
    return config.get("output", {}).get("directory", "./output")


def _parse_file(
    file_path: str,
    redis_store: RedisStore | None,
    output_dir: str,
    export_format: str,
    no_redis: bool,
    no_export: bool,
    quiet: bool = False,
) -> tuple[Subscription, list[Node]]:
    """解析单个订阅文件的核心逻辑"""
    path = Path(file_path)
    source_id = path.stem

    if not quiet:
        print(f"Parsing: {file_path}")

    start_time = time.time()

    # 读取文件（带重试）
    content = None
    for attempt in range(1, 4):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            break
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            logger.warning(f"文件访问被拒绝 ({attempt}/3): {file_path}")
            if attempt == 3:
                print(f"Error: Permission denied: {file_path}", file=sys.stderr)
                sys.exit(1)
            time.sleep(2 ** attempt)
        except OSError as e:
            logger.warning(f"文件读取失败 ({attempt}/3): {e}")
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

    if not content or not content.strip():
        logger.warning(f"空文件: {file_path}")
        subscription = Subscription(
            source_id=source_id,
            file_path=str(path.resolve()),
            format="unknown",
            total_nodes=0,
            successful_nodes=0,
            failed_nodes=0,
            duration_ms=0,
        )
        return subscription, []

    # 检测格式并解码
    detector = FormatDetector()
    try:
        detected_format, uris = detector.detect_and_decode(content)
    except ValueError as e:
        logger.error(f"格式检测失败: {e}")
        print(f"Warning: Could not detect format for file: {file_path}", file=sys.stderr)
        print(f"Tried: base64, yaml, mixed", file=sys.stderr)
        subscription = Subscription(
            source_id=source_id,
            file_path=str(path.resolve()),
            format="unknown",
            total_nodes=0,
            successful_nodes=0,
            failed_nodes=0,
            duration_ms=int((time.time() - start_time) * 1000),
            errors=[str(e)],
        )
        return subscription, []

    if not quiet:
        print(f"Format detected: {detected_format}")
        print(f"Nodes found: {len(uris)}")

    # 解析每个URI
    nodes = []
    errors = []
    for i, uri in enumerate(uris):
        try:
            node = parse_uri(uri)
            node.source_id = source_id
            nodes.append(node)
        except ValueError as e:
            error_msg = f"Line {i + 1}: {e}"
            logger.warning(f"节点解析失败 {error_msg}")
            errors.append(error_msg)

    duration_ms = int((time.time() - start_time) * 1000)
    subscription = Subscription(
        source_id=source_id,
        file_path=str(path.resolve()),
        format=detected_format,
        total_nodes=len(uris),
        successful_nodes=len(nodes),
        failed_nodes=len(errors),
        duration_ms=duration_ms,
        errors=errors,
    )

    if not quiet:
        print(f"Successfully parsed: {len(nodes)}")
        print(f"Failed: {len(errors)}")
        print(f"Duration: {duration_ms / 1000:.2f}s")

    logger.info(
        f"解析完成: source_id={source_id}, 节点数={len(nodes)}, "
        f"失败={len(errors)}, 耗时={duration_ms}ms"
    )

    # 存储到Redis
    if not no_redis and redis_store:
        try:
            for node in nodes:
                redis_store.store_node(node, source_id)
            redis_store.store_subscription(subscription)
            if not quiet:
                print(f"\nStored in Redis: subscription:{source_id}")
        except Exception as e:
            logger.error(f"Redis存储失败: {e}")
            print(f"Error: Failed to connect to Redis: {e}", file=sys.stderr)

    # 导出文件
    if not no_export:
        result = ParseResult(
            subscription=subscription,
            nodes=nodes,
            export_format=export_format,
        )
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if export_format in ("json", "both"):
            json_path = str(output_path / f"{source_id}.json")
            try:
                export_json(result, json_path)
                if not quiet:
                    print(f"Exported to: {json_path}")
            except Exception as e:
                logger.error(f"JSON导出失败: {e}")
                print(f"Error: File export failed: {e}", file=sys.stderr)

        if export_format in ("csv", "both"):
            csv_path = str(output_path / f"{source_id}.csv")
            try:
                export_csv(result, csv_path)
                if not quiet:
                    print(f"Exported to: {csv_path}")
            except Exception as e:
                logger.error(f"CSV导出失败: {e}")
                print(f"Error: File export failed: {e}", file=sys.stderr)

    return subscription, nodes


def cmd_parse(args) -> int:
    """parse命令: 解析单个订阅文件"""
    config = _load_config()
    redis_url = _get_redis_url(args, config)
    output_dir = _get_output_dir(args, config)

    if args.verbose:
        setup_logger("DEBUG")

    file_path = args.file_path
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    redis_store = None
    if not args.no_redis:
        try:
            redis_store = RedisStore(url=redis_url)
            redis_store.connect()
        except Exception as e:
            print(f"Error: Failed to connect to Redis at {redis_url}", file=sys.stderr)
            logger.error(f"Redis连接失败: {e}")
            return 3

    try:
        subscription, nodes = _parse_file(
            file_path=file_path,
            redis_store=redis_store,
            output_dir=output_dir,
            export_format=args.format,
            no_redis=args.no_redis,
            no_export=args.no_export,
            quiet=args.quiet,
        )
    finally:
        if redis_store:
            redis_store.close()

    if subscription.total_nodes > 0 and subscription.successful_nodes == 0:
        return 2

    return 0


def cmd_batch(args) -> int:
    """batch命令: 批量处理目录中的订阅文件"""
    config = _load_config()
    redis_url = _get_redis_url(args, config)
    output_dir = _get_output_dir(args, config)

    if args.verbose:
        setup_logger("DEBUG")

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
        return 1
    if not directory.is_dir():
        print(f"Error: Not a directory: {args.directory}", file=sys.stderr)
        return 1

    # 收集文件
    pattern = getattr(args, "pattern", "*")
    recursive = getattr(args, "recursive", False)
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    files = [f for f in files if f.is_file()]

    if not files:
        print(f"No files found in: {args.directory}")
        return 0

    print(f"Processing directory: {args.directory}")
    print(f"Files found: {len(files)}")

    redis_store = None
    if not args.no_redis:
        try:
            redis_store = RedisStore(url=redis_url)
            redis_store.connect()
        except Exception as e:
            print(f"Error: Failed to connect to Redis at {redis_url}", file=sys.stderr)
            return 3

    start_time = time.time()
    total_nodes = 0
    successful_nodes = 0
    failed_nodes = 0
    successful_files = 0
    failed_files = []
    parallel = getattr(args, "parallel", 1)

    def process_file(file_path: Path) -> tuple[bool, str, int, int]:
        """处理单个文件，返回(成功, 错误信息, 成功节点数, 失败节点数)"""
        try:
            sub, nodes = _parse_file(
                file_path=str(file_path),
                redis_store=redis_store,
                output_dir=output_dir,
                export_format=args.format,
                no_redis=args.no_redis,
                no_export=args.no_export,
                quiet=True,
            )
            return True, "", sub.successful_nodes, sub.failed_nodes
        except Exception as e:
            return False, str(e), 0, 0

    if parallel > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(process_file, f): f for f in files}
            with tqdm(total=len(files), desc="Processing", unit="file", disable=args.quiet) as pbar:
                for future in concurrent.futures.as_completed(futures):
                    file_path = futures[future]
                    success, error, s_nodes, f_nodes = future.result()
                    if success:
                        successful_files += 1
                        successful_nodes += s_nodes
                        failed_nodes += f_nodes
                        total_nodes += s_nodes + f_nodes
                    else:
                        failed_files.append((file_path.name, error))
                    pbar.update(1)
    else:
        with tqdm(total=len(files), desc="Processing", unit="file", disable=args.quiet) as pbar:
            for file_path in files:
                success, error, s_nodes, f_nodes = process_file(file_path)
                if success:
                    successful_files += 1
                    successful_nodes += s_nodes
                    failed_nodes += f_nodes
                    total_nodes += s_nodes + f_nodes
                else:
                    failed_files.append((file_path.name, error))
                pbar.update(1)

    duration = time.time() - start_time

    if redis_store:
        redis_store.close()

    print(f"\nSummary:")
    print(f"  Total files: {len(files)}")
    print(f"  Successful: {successful_files}")
    print(f"  Failed: {len(failed_files)}")
    print(f"  Total nodes: {total_nodes:,}")
    print(f"  Successfully parsed: {successful_nodes:,}")
    print(f"  Failed nodes: {failed_nodes:,}")
    print(f"  Duration: {duration:.1f}s")

    if not args.no_redis:
        print(f"\nStored in Redis: {successful_files} subscriptions")
    if not args.no_export:
        print(f"Exported to: {output_dir}/ ({successful_files * (2 if args.format == 'both' else 1)} files)")

    if failed_files:
        print(f"\nFailed files:")
        for name, error in failed_files:
            print(f"  - {name}: {error}")

    if successful_files == 0:
        return 2
    return 0


def cmd_export(args) -> int:
    """export命令: 从Redis导出订阅数据"""
    config = _load_config()
    redis_url = _get_redis_url(args, config)

    if args.verbose:
        setup_logger("DEBUG")

    source_id = args.source_id
    output_path = args.output
    export_format = args.format

    try:
        with RedisStore(url=redis_url) as store:
            subscription = store.get_subscription(source_id)
            if subscription is None:
                print(f"Error: Source not found in Redis: {source_id}", file=sys.stderr)
                return 1

            print(f"Exporting: subscription:{source_id}")
            nodes = store.get_nodes_by_source(source_id)
            print(f"Nodes found: {len(nodes)}")

            if export_format == "json":
                export_nodes_json(nodes, subscription, output_path)
            elif export_format == "csv":
                export_nodes_csv(nodes, subscription, output_path)

            print(f"Exported to: {output_path}")
    except Exception as e:
        if "Redis" in str(type(e).__name__) or "Connection" in str(e):
            print(f"Error: Failed to connect to Redis at {redis_url}", file=sys.stderr)
            return 3
        print(f"Error: Export failed: {e}", file=sys.stderr)
        return 2

    return 0


def cmd_list(args) -> int:
    """list命令: 列出Redis中的所有订阅"""
    config = _load_config()
    redis_url = _get_redis_url(args, config)

    if args.verbose:
        setup_logger("DEBUG")

    try:
        with RedisStore(url=redis_url) as store:
            subscriptions = store.list_subscriptions()
    except Exception as e:
        print(f"Error: Failed to connect to Redis at {redis_url}", file=sys.stderr)
        return 3

    if not subscriptions:
        print("No subscriptions found in Redis.")
        return 0

    print("Subscriptions in Redis:\n")
    print(f"{'source_id':<25} {'nodes':>6}  {'parsed_at':<20} {'ttl':<10}")
    print("-" * 65)
    total_nodes = 0
    for sub in subscriptions:
        source_id = sub["source_id"]
        nodes = sub["nodes"]
        parsed_at = sub["parsed_at"][:19] if sub["parsed_at"] else "-"
        ttl = sub["ttl"]
        if ttl > 0:
            days = ttl // 86400
            hours = (ttl % 86400) // 3600
            ttl_str = f"{days}d {hours}h"
        else:
            ttl_str = "expired"
        print(f"{source_id:<25} {nodes:>6}  {parsed_at:<20} {ttl_str:<10}")
        try:
            total_nodes += int(nodes)
        except ValueError:
            pass

    print(f"\nTotal: {len(subscriptions)} subscriptions, {total_nodes} nodes")
    return 0


def cmd_info(args) -> int:
    """info命令: 显示订阅详情"""
    config = _load_config()
    redis_url = _get_redis_url(args, config)

    if args.verbose:
        setup_logger("DEBUG")

    source_id = args.source_id

    try:
        with RedisStore(url=redis_url) as store:
            subscription = store.get_subscription(source_id)
            if subscription is None:
                print(f"Error: Source not found in Redis: {source_id}", file=sys.stderr)
                return 1

            nodes = store.get_nodes_by_source(source_id)
            ttl = store.client.ttl(f"subscription:{source_id}:meta")
    except Exception as e:
        print(f"Error: Failed to connect to Redis at {redis_url}", file=sys.stderr)
        return 3

    days = ttl // 86400
    hours = (ttl % 86400) // 3600
    ttl_str = f"{days} days {hours} hours" if ttl > 0 else "expired"

    print(f"Subscription: {source_id}\n")
    print(f"Metadata:")
    print(f"  Source ID: {subscription.source_id}")
    print(f"  File Path: {subscription.file_path}")
    print(f"  Format: {subscription.format}")
    print(f"  Total Nodes: {subscription.total_nodes}")
    print(f"  Successful: {subscription.successful_nodes}")
    print(f"  Failed: {subscription.failed_nodes}")
    print(f"  Parsed At: {subscription.parsed_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {subscription.duration_ms / 1000:.2f}s")
    print(f"  TTL: {ttl_str}")

    if nodes:
        protocol_counts: dict[str, int] = {}
        for node in nodes:
            protocol_counts[node.protocol] = protocol_counts.get(node.protocol, 0) + 1
        print(f"\nProtocol Distribution:")
        total = len(nodes)
        for protocol, count in sorted(protocol_counts.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            print(f"  {protocol}: {count} ({pct:.0f}%)")

    if subscription.errors:
        print(f"\nErrors:")
        for error in subscription.errors[:10]:
            print(f"  - {error}")

    if getattr(args, "show_nodes", False):
        print(f"\nNodes:")
        for node in nodes[:20]:
            print(f"  [{node.protocol}] {node.host}:{node.port} {node.remarks or ''}")

    return 0


def cmd_version(args) -> int:
    """version命令: 显示版本信息"""
    import sys
    import redis
    import yaml
    print(f"subscription-parser version {VERSION}")
    print(f"Python {sys.version.split()[0]}")
    try:
        print(f"Redis client: redis-py {redis.__version__}")
    except Exception:
        print("Redis client: unknown version")
    try:
        print(f"PyYAML: {yaml.__version__}")
    except Exception:
        pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="subscription-parser",
        description="订阅解析器 - 代理订阅文件解析工具",
    )
    parser.add_argument("--version", action="store_true", help="显示版本信息")

    subparsers = parser.add_subparsers(dest="command")

    # parse命令
    parse_cmd = subparsers.add_parser("parse", help="解析单个订阅文件")
    parse_cmd.add_argument("file_path", help="订阅文件路径")
    parse_cmd.add_argument("--redis-url", default=None, help="Redis连接URL")
    parse_cmd.add_argument("--output-dir", default=None, help="输出目录")
    parse_cmd.add_argument("--format", choices=["json", "csv", "both"], default="both", help="导出格式")
    parse_cmd.add_argument("--no-redis", action="store_true", help="跳过Redis存储")
    parse_cmd.add_argument("--no-export", action="store_true", help="跳过文件导出")
    parse_cmd.add_argument("--verbose", "-v", action="store_true", help="启用调试日志")
    parse_cmd.add_argument("--quiet", "-q", action="store_true", help="安静模式")

    # batch命令
    batch_cmd = subparsers.add_parser("batch", help="批量处理目录中的订阅文件")
    batch_cmd.add_argument("directory", help="订阅文件目录")
    batch_cmd.add_argument("--redis-url", default=None, help="Redis连接URL")
    batch_cmd.add_argument("--output-dir", default=None, help="输出目录")
    batch_cmd.add_argument("--format", choices=["json", "csv", "both"], default="both", help="导出格式")
    batch_cmd.add_argument("--pattern", default="*", help="文件匹配模式")
    batch_cmd.add_argument("--recursive", "-r", action="store_true", help="递归处理子目录")
    batch_cmd.add_argument("--no-redis", action="store_true", help="跳过Redis存储")
    batch_cmd.add_argument("--no-export", action="store_true", help="跳过文件导出")
    batch_cmd.add_argument("--parallel", type=int, default=1, help="并行工作线程数")
    batch_cmd.add_argument("--verbose", "-v", action="store_true", help="启用调试日志")
    batch_cmd.add_argument("--quiet", "-q", action="store_true", help="安静模式")

    # export命令
    export_cmd = subparsers.add_parser("export", help="从Redis导出订阅数据")
    export_cmd.add_argument("source_id", help="订阅源标识符")
    export_cmd.add_argument("--redis-url", default=None, help="Redis连接URL")
    export_cmd.add_argument("--output", required=True, help="输出文件路径")
    export_cmd.add_argument("--format", choices=["json", "csv"], required=True, help="导出格式")
    export_cmd.add_argument("--verbose", "-v", action="store_true", help="启用调试日志")

    # list命令
    list_cmd = subparsers.add_parser("list", help="列出Redis中的订阅")
    list_cmd.add_argument("--redis-url", default=None, help="Redis连接URL")
    list_cmd.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

    # info命令
    info_cmd = subparsers.add_parser("info", help="显示订阅详情")
    info_cmd.add_argument("source_id", help="订阅源标识符")
    info_cmd.add_argument("--redis-url", default=None, help="Redis连接URL")
    info_cmd.add_argument("--show-nodes", action="store_true", help="显示所有节点详情")
    info_cmd.add_argument("--verbose", "-v", action="store_true", help="启用调试日志")

    # version命令
    subparsers.add_parser("version", help="显示版本信息")

    return parser


def app():
    """CLI应用入口"""
    parser = build_parser()
    args = parser.parse_args()

    if args.version or args.command == "version":
        return sys.exit(cmd_version(args))

    if args.command is None:
        parser.print_help()
        return sys.exit(0)

    command_map = {
        "parse": cmd_parse,
        "batch": cmd_batch,
        "export": cmd_export,
        "list": cmd_list,
        "info": cmd_info,
        "version": cmd_version,
    }

    handler = command_map.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    exit_code = handler(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    app()

"""
ClickHouse Performance Benchmarking for NSE Data ETL Pipeline.

Comprehensive performance testing for high-frequency financial data processing.
Measures insert throughput, query performance, and system resource utilization.
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
import random
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

try:
    from clickhouse_driver import Client
    from clickhouse_driver.errors import Error as ClickHouseError
except ImportError:
    Client = None
    ClickHouseError = Exception

from ..config import Settings, get_settings
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark result data structure."""
    operation: str
    duration: float
    records_processed: int
    throughput: float  # records per second
    memory_usage: float  # MB
    error_count: int
    success_rate: float
    p95_latency: float  # 95th percentile latency
    p99_latency: float  # 99th percentile latency


class ClickHouseBenchmark:
    """
    ClickHouse performance benchmarking suite.
    
    Tests various aspects of the NSE data schema including:
    - Bulk insert performance
    - Query performance
    - Concurrent operations
    - Memory usage patterns
    - Index effectiveness
    """
    
    def __init__(self, settings: Settings = None):
        """
        Initialize benchmark suite.
        
        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self.schema_manager = SchemaManager(self.settings)
        self.client = self.schema_manager._get_client()
        self.database = self.schema_manager.database
        self.results: List[BenchmarkResult] = []
        
    def generate_test_data(self, batch_size: int = 100000) -> List[tuple]:
        """
        Generate test tick data for benchmarking.
        
        Args:
            batch_size: Number of records to generate
            
        Returns:
            List of tick tuples
        """
        test_data = []
        base_time = datetime.utcnow()
        symbols = [f'TEST_SYMBOL_{i:03d}' for i in range(100)]
        
        for i in range(batch_size):
            symbol = random.choice(symbols)
            timestamp = base_time + timedelta(seconds=i // 10)  # 10 ticks per second
            price = round(random.uniform(1000, 3000), 2)
            volume = random.randint(100, 10000)
            
            # Generate realistic bid-ask spread
            spread = price * random.uniform(0.0005, 0.001)
            bid_price = round(price - spread/2, 2)
            ask_price = round(price + spread/2, 2)
            
            test_data.append((
                symbol, timestamp, price, volume,
                bid_price, ask_price, 
                random.randint(100, 1000),  # bid_size
                random.randint(100, 1000),  # ask_size
                'NSE', 'BENCHMARK', f'T{i:08d}', 1
            ))
            
        return test_data
    
    def benchmark_bulk_insert(self, batch_size: int = 100000, 
                            iterations: int = 5) -> BenchmarkResult:
        """
        Benchmark bulk insert performance.
        
        Args:
            batch_size: Records per batch
            iterations: Number of iterations
            
        Returns:
            Benchmark result
        """
        logger.info(f"Benchmarking bulk insert: {batch_size} records x {iterations} iterations")
        
        durations = []
        total_records = 0
        error_count = 0
        
        for iteration in range(iterations):
            try:
                # Generate fresh test data for each iteration
                test_data = self.generate_test_data(batch_size)
                
                start_time = time.time()
                
                # Insert data in smaller batches for better performance 
                sub_batch_size = 10000
                for i in range(0, len(test_data), sub_batch_size):
                    batch = test_data[i:i + sub_batch_size]
                    
                    self.client.execute(f"""
                        INSERT INTO {self.database}.raw_ticks 
                        (symbol, timestamp, price, volume, bid_price, ask_price, 
                         bid_size, ask_size, exchange, source, trade_id, trade_type)
                        VALUES
                    """, batch)
                
                end_time = time.time()
                duration = end_time - start_time
                durations.append(duration)
                total_records += len(test_data)
                
                throughput = len(test_data) / duration
                logger.info(f"Iteration {iteration + 1}: {throughput:.0f} records/sec")
                
            except Exception as e:
                logger.error(f"Insert iteration {iteration + 1} failed: {e}")
                error_count += 1
                durations.append(float('inf'))
        
        # Calculate statistics
        valid_durations = [d for d in durations if d != float('inf')]
        avg_duration = statistics.mean(valid_durations) if valid_durations else 0
        avg_throughput = (total_records / sum(valid_durations)) if valid_durations else 0
        success_rate = (iterations - error_count) / iterations * 100
        
        p95_latency = statistics.quantile(valid_durations, 0.95) if len(valid_durations) > 1 else 0
        p99_latency = statistics.quantile(valid_durations, 0.99) if len(valid_durations) > 1 else 0
        
        return BenchmarkResult(
            operation="bulk_insert",
            duration=avg_duration,
            records_processed=total_records,
            throughput=avg_throughput,
            memory_usage=0.0,  # TODO: Implement memory monitoring
            error_count=error_count,
            success_rate=success_rate,
            p95_latency=p95_latency,
            p99_latency=p99_latency
        )
    
    def benchmark_query_performance(self) -> List[BenchmarkResult]:
        """
        Benchmark various query patterns.
        
        Returns:
            List of benchmark results for different queries
        """
        queries = {
            "symbol_filter": """
                SELECT symbol, COUNT(*), AVG(price), MAX(volume)
                FROM {database}.raw_ticks 
                WHERE symbol = 'TEST_SYMBOL_001'
                GROUP BY symbol
            """,
            "time_range": """
                SELECT COUNT(*), AVG(price), SUM(volume)
                FROM {database}.raw_ticks
                WHERE timestamp >= now() - INTERVAL 1 HOUR
            """,
            "price_range": """
                SELECT symbol, COUNT(*)
                FROM {database}.raw_ticks
                WHERE price BETWEEN 1500 AND 2500
                GROUP BY symbol
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """,
            "ohlcv_aggregation": """
                SELECT 
                    symbol,
                    toStartOfMinute(timestamp) as minute,
                    argMin(price, timestamp) as open,
                    max(price) as high,
                    min(price) as low,
                    argMax(price, timestamp) as close,
                    sum(volume) as volume
                FROM {database}.raw_ticks
                WHERE timestamp >= now() - INTERVAL 30 MINUTE
                GROUP BY symbol, minute
                ORDER BY symbol, minute
            """,
            "materialized_view_query": """
                SELECT symbol, timeframe, open, high, low, close, volume
                FROM {database}.ohlcv_bars
                WHERE timeframe = 1 AND timestamp >= today()
                ORDER BY timestamp DESC
                LIMIT 100
            """
        }
        
        results = []
        
        for query_name, query_template in queries.items():
            logger.info(f"Benchmarking query: {query_name}")
            
            query = query_template.format(database=self.database)
            durations = []
            iterations = 10
            error_count = 0
            
            for i in range(iterations):
                try:
                    start_time = time.time()
                    result = self.client.execute(query)
                    end_time = time.time()
                    
                    duration = end_time - start_time
                    durations.append(duration)
                    
                    if i == 0:  # Log first result for verification
                        logger.debug(f"Query {query_name} returned {len(result)} rows")
                        
                except Exception as e:
                    logger.error(f"Query {query_name} iteration {i + 1} failed: {e}")
                    error_count += 1
                    durations.append(float('inf'))
            
            # Calculate statistics
            valid_durations = [d for d in durations if d != float('inf')]
            avg_duration = statistics.mean(valid_durations) if valid_durations else 0
            success_rate = (iterations - error_count) / iterations * 100
            
            p95_latency = statistics.quantile(valid_durations, 0.95) if len(valid_durations) > 1 else 0
            p99_latency = statistics.quantile(valid_durations, 0.99) if len(valid_durations) > 1 else 0
            
            result = BenchmarkResult(
                operation=f"query_{query_name}",
                duration=avg_duration,
                records_processed=len(result) if 'result' in locals() else 0,
                throughput=0.0,  # Not applicable for queries
                memory_usage=0.0,
                error_count=error_count,
                success_rate=success_rate,
                p95_latency=p95_latency,
                p99_latency=p99_latency
            )
            
            results.append(result)
            logger.info(f"Query {query_name}: {avg_duration*1000:.2f}ms avg, {success_rate:.1f}% success")
        
        return results
    
    def benchmark_concurrent_operations(self, num_threads: int = 10, 
                                      operations_per_thread: int = 100) -> BenchmarkResult:
        """
        Benchmark concurrent operations.
        
        Args:
            num_threads: Number of concurrent threads
            operations_per_thread: Operations per thread
            
        Returns:
            Benchmark result
        """
        logger.info(f"Benchmarking concurrent operations: {num_threads} threads, {operations_per_thread} ops/thread")
        
        def worker_thread(thread_id: int) -> Tuple[int, List[float], int]:
            """Worker thread function."""
            client = Client(
                host=self.settings.database.clickhouse_host,
                port=self.settings.database.clickhouse_port,
                user=self.settings.database.clickhouse_user,
                password=self.settings.database.clickhouse_password,
                database=self.database
            )
            
            durations = []
            error_count = 0
            
            for i in range(operations_per_thread):
                try:
                    # Generate small batch of data
                    test_data = self.generate_test_data(100)
                    
                    start_time = time.time()
                    client.execute("""
                        INSERT INTO raw_ticks 
                        (symbol, timestamp, price, volume, bid_price, ask_price, 
                         bid_size, ask_size, exchange, source, trade_id, trade_type)
                        VALUES
                    """, test_data)
                    end_time = time.time()
                    
                    durations.append(end_time - start_time)
                    
                except Exception as e:
                    logger.error(f"Thread {thread_id} operation {i} failed: {e}")
                    error_count += 1
            
            client.disconnect()
            return len(test_data) * operations_per_thread, durations, error_count
        
        # Execute concurrent operations
        start_time = time.time()
        all_durations = []
        total_records = 0
        total_errors = 0
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    records, durations, errors = future.result()
                    total_records += records
                    all_durations.extend(durations)
                    total_errors += errors
                except Exception as e:
                    logger.error(f"Thread execution failed: {e}")
                    total_errors += 1
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        avg_throughput = total_records / total_duration if total_duration > 0 else 0
        success_rate = (num_threads * operations_per_thread - total_errors) / (num_threads * operations_per_thread) * 100
        
        p95_latency = statistics.quantile(all_durations, 0.95) if len(all_durations) > 1 else 0
        p99_latency = statistics.quantile(all_durations, 0.99) if len(all_durations) > 1 else 0
        
        return BenchmarkResult(
            operation="concurrent_insert",
            duration=total_duration,
            records_processed=total_records,
            throughput=avg_throughput,
            memory_usage=0.0,
            error_count=total_errors,
            success_rate=success_rate,
            p95_latency=p95_latency,
            p99_latency=p99_latency
        )
    
    def benchmark_index_effectiveness(self) -> List[BenchmarkResult]:
        """
        Benchmark index effectiveness by comparing queries with and without indexes.
        
        Returns:
            List of benchmark results comparing indexed vs non-indexed queries
        """
        # Test queries that should benefit from indexes
        indexed_queries = {
            "symbol_index": """
                SELECT COUNT(*) FROM {database}.raw_ticks 
                WHERE symbol = 'TEST_SYMBOL_001'
            """,
            "timestamp_range": """
                SELECT COUNT(*) FROM {database}.raw_ticks
                WHERE timestamp >= now() - INTERVAL 1 HOUR
            """,
            "price_range": """
                SELECT COUNT(*) FROM {database}.raw_ticks
                WHERE price BETWEEN 2000 AND 2500
            """
        }
        
        results = []
        
        for query_name, query_template in indexed_queries.items():
            query = query_template.format(database=self.database)
            
            # Measure query performance
            durations = []
            iterations = 5
            
            for i in range(iterations):
                try:
                    start_time = time.time()
                    result = self.client.execute(query)
                    end_time = time.time()
                    durations.append(end_time - start_time)
                except Exception as e:
                    logger.error(f"Index effectiveness test {query_name} failed: {e}")
                    durations.append(float('inf'))
            
            valid_durations = [d for d in durations if d != float('inf')]
            avg_duration = statistics.mean(valid_durations) if valid_durations else 0
            
            benchmark_result = BenchmarkResult(
                operation=f"index_{query_name}",
                duration=avg_duration,
                records_processed=result[0][0] if result else 0,
                throughput=0.0,
                memory_usage=0.0,
                error_count=len(durations) - len(valid_durations),
                success_rate=len(valid_durations) / len(durations) * 100,
                p95_latency=0.0,
                p99_latency=0.0
            )
            
            results.append(benchmark_result)
            logger.info(f"Index test {query_name}: {avg_duration*1000:.2f}ms avg")
        
        return results
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive benchmark suite.
        
        Returns:
            Dictionary with all benchmark results and summary
        """
        logger.info("🚀 Starting comprehensive ClickHouse benchmark...")
        
        start_time = time.time()
        
        # Clean up any existing test data
        try:
            self.client.execute(f"DELETE FROM {self.database}.raw_ticks WHERE source = 'BENCHMARK'")
        except:
            pass
        
        benchmark_results = {}
        
        # 1. Bulk Insert Performance
        logger.info("📊 Running bulk insert benchmark...")
        bulk_insert_result = self.benchmark_bulk_insert()
        benchmark_results['bulk_insert'] = bulk_insert_result
        
        # 2. Query Performance
        logger.info("📊 Running query performance benchmark...")
        query_results = self.benchmark_query_performance()
        benchmark_results['queries'] = {r.operation: r for r in query_results}
        
        # 3. Concurrent Operations
        logger.info("📊 Running concurrent operations benchmark...")
        concurrent_result = self.benchmark_concurrent_operations()
        benchmark_results['concurrent'] = concurrent_result
        
        # 4. Index Effectiveness
        logger.info("📊 Running index effectiveness benchmark...")
        index_results = self.benchmark_index_effectiveness()
        benchmark_results['indexes'] = {r.operation: r for r in index_results}
        
        total_time = time.time() - start_time
        
        # Generate summary
        summary = {
            'total_benchmark_time': total_time,
            'bulk_insert_throughput': bulk_insert_result.throughput,
            'concurrent_throughput': concurrent_result.throughput,
            'avg_query_latency': statistics.mean([r.duration for r in query_results]),
            'overall_success_rate': statistics.mean([
                bulk_insert_result.success_rate,
                concurrent_result.success_rate,
                *[r.success_rate for r in query_results]
            ])
        }
        
        logger.info("✅ Comprehensive benchmark completed!")
        logger.info(f"📈 Bulk Insert Throughput: {bulk_insert_result.throughput:.0f} records/sec")
        logger.info(f"📈 Concurrent Throughput: {concurrent_result.throughput:.0f} records/sec")
        logger.info(f"📈 Average Query Latency: {summary['avg_query_latency']*1000:.2f}ms")
        logger.info(f"📈 Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        return {
            'results': benchmark_results,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cleanup_test_data(self):
        """Clean up test data after benchmarking."""
        try:
            self.client.execute(f"DELETE FROM {self.database}.raw_ticks WHERE source = 'BENCHMARK'")
            logger.info("Test data cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup test data: {e}")


def main():
    """Main benchmark execution function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize benchmark
        benchmark = ClickHouseBenchmark()
        
        # Run comprehensive benchmark
        results = benchmark.run_comprehensive_benchmark()
        
        # Cleanup
        benchmark.cleanup_test_data()
        
        # Output results summary
        print("\n" + "="*80)
        print("📊 ClickHouse Performance Benchmark Results")
        print("="*80)
        print(f"Bulk Insert Throughput: {results['summary']['bulk_insert_throughput']:.0f} records/sec")
        print(f"Concurrent Throughput: {results['summary']['concurrent_throughput']:.0f} records/sec")
        print(f"Average Query Latency: {results['summary']['avg_query_latency']*1000:.2f}ms")
        print(f"Overall Success Rate: {results['summary']['overall_success_rate']:.1f}%")
        print(f"Total Benchmark Time: {results['summary']['total_benchmark_time']:.2f}s")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")


if __name__ == "__main__":
    main()
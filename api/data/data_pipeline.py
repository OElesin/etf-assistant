"""
ETF Data Pipeline Management
Orchestrates data collection, processing, and quality checks
"""

import asyncio
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from .etf_scraper import ETFDataScraper

logger = logging.getLogger(__name__)

class ETFDataPipeline:
    """
    Manages the complete ETF data pipeline:
    1. Data collection from multiple sources
    2. Data quality validation
    3. Data enrichment (calculate metrics)
    4. Storage and indexing
    5. Monitoring and alerting
    """
    
    def __init__(self):
        self.scraper = ETFDataScraper()
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Data quality thresholds
        self.quality_thresholds = {
            'min_etfs': 100,  # Minimum number of ETFs
            'max_missing_data': 0.1,  # Max 10% missing critical fields
            'max_stale_hours': 25,  # Data older than 25 hours is stale
        }

    async def run_daily_pipeline(self) -> Dict:
        """
        Run the complete daily data pipeline
        """
        
        pipeline_start = datetime.utcnow()
        results = {
            'start_time': pipeline_start.isoformat(),
            'status': 'running',
            'stages': {}
        }
        
        try:
            # Stage 1: Data Collection
            logger.info("Starting data collection stage...")
            collection_result = await self._collect_data()
            results['stages']['collection'] = collection_result
            
            # Stage 2: Data Quality Validation
            logger.info("Starting data quality validation...")
            quality_result = await self._validate_data_quality(collection_result['etfs'])
            results['stages']['quality'] = quality_result
            
            # Stage 3: Data Enrichment
            logger.info("Starting data enrichment...")
            enrichment_result = await self._enrich_data(collection_result['etfs'])
            results['stages']['enrichment'] = enrichment_result
            
            # Stage 4: Storage
            logger.info("Starting data storage...")
            storage_result = await self._store_processed_data(enrichment_result['enriched_etfs'])
            results['stages']['storage'] = storage_result
            
            # Stage 5: Monitoring
            logger.info("Publishing metrics...")
            await self._publish_metrics(results)
            
            results['status'] = 'completed'
            results['end_time'] = datetime.utcnow().isoformat()
            results['duration_minutes'] = (datetime.utcnow() - pipeline_start).total_seconds() / 60
            
            logger.info(f"Pipeline completed successfully in {results['duration_minutes']:.1f} minutes")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            results['end_time'] = datetime.utcnow().isoformat()
            
            logger.error(f"Pipeline failed: {e}")
            await self._send_alert(f"ETF Data Pipeline Failed: {e}")
        
        return results

    async def _collect_data(self) -> Dict:
        """
        Collect ETF data from all sources
        """
        
        collection_start = datetime.utcnow()
        
        # Collect from JustETF (primary source)
        justetf_etfs = await self.scraper.scrape_justetf_data()
        
        # Collect from alternative sources
        alternative_etfs = await self.scraper.scrape_alternative_sources()
        
        # Merge and deduplicate
        all_etfs = justetf_etfs + alternative_etfs
        unique_etfs = {}
        
        for etf in all_etfs:
            isin = etf.get('isin')
            if isin:
                if isin not in unique_etfs or etf.get('source') == 'justetf':
                    # Prefer JustETF data if duplicate
                    unique_etfs[isin] = etf
        
        final_etfs = list(unique_etfs.values())
        
        return {
            'etfs': final_etfs,
            'total_count': len(final_etfs),
            'justetf_count': len(justetf_etfs),
            'alternative_count': len(alternative_etfs),
            'duration_seconds': (datetime.utcnow() - collection_start).total_seconds()
        }

    async def _validate_data_quality(self, etfs: List[Dict]) -> Dict:
        """
        Validate data quality and flag issues
        """
        
        quality_issues = []
        
        # Check minimum ETF count
        if len(etfs) < self.quality_thresholds['min_etfs']:
            quality_issues.append(f"Too few ETFs: {len(etfs)} < {self.quality_thresholds['min_etfs']}")
        
        # Check for missing critical fields
        critical_fields = ['isin', 'name', 'ter', 'domicile']
        missing_data_count = 0
        
        for etf in etfs:
            for field in critical_fields:
                if not etf.get(field):
                    missing_data_count += 1
        
        missing_data_rate = missing_data_count / (len(etfs) * len(critical_fields))
        if missing_data_rate > self.quality_thresholds['max_missing_data']:
            quality_issues.append(f"Too much missing data: {missing_data_rate:.1%}")
        
        # Check data freshness
        now = datetime.utcnow()
        stale_count = 0
        
        for etf in etfs:
            scraped_at = etf.get('scraped_at')
            if scraped_at:
                scraped_time = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                hours_old = (now - scraped_time).total_seconds() / 3600
                if hours_old > self.quality_thresholds['max_stale_hours']:
                    stale_count += 1
        
        if stale_count > 0:
            quality_issues.append(f"Stale data found: {stale_count} ETFs")
        
        # Validate specific ETF data
        validation_errors = []
        for etf in etfs:
            errors = self._validate_etf_data(etf)
            validation_errors.extend(errors)
        
        return {
            'passed': len(quality_issues) == 0 and len(validation_errors) == 0,
            'issues': quality_issues,
            'validation_errors': validation_errors[:10],  # Limit to first 10
            'missing_data_rate': missing_data_rate,
            'stale_count': stale_count
        }

    def _validate_etf_data(self, etf: Dict) -> List[str]:
        """
        Validate individual ETF data
        """
        
        errors = []
        
        # Validate ISIN format
        isin = etf.get('isin', '')
        if not isin or len(isin) != 12 or not isin[:2].isalpha():
            errors.append(f"Invalid ISIN: {isin}")
        
        # Validate TER range
        ter = etf.get('ter')
        if ter is not None and (ter < 0 or ter > 0.05):  # 0-5% range
            errors.append(f"Invalid TER: {ter}")
        
        # Validate AUM
        aum = etf.get('aum')
        if aum is not None and aum < 0:
            errors.append(f"Invalid AUM: {aum}")
        
        # Validate domicile
        valid_domiciles = ['Ireland', 'Luxembourg', 'Germany', 'France', 'Netherlands']
        domicile = etf.get('domicile')
        if domicile and domicile not in valid_domiciles:
            errors.append(f"Unusual domicile: {domicile}")
        
        return errors

    async def _enrich_data(self, etfs: List[Dict]) -> Dict:
        """
        Enrich ETF data with calculated metrics and additional information
        """
        
        enriched_etfs = []
        
        for etf in etfs:
            enriched_etf = etf.copy()
            
            # Calculate tax efficiency score
            enriched_etf['tax_efficiency_score'] = self._calculate_tax_efficiency(etf)
            
            # Calculate liquidity score
            enriched_etf['liquidity_score'] = self._calculate_liquidity_score(etf)
            
            # Calculate overall quality score
            enriched_etf['quality_score'] = self._calculate_quality_score(enriched_etf)
            
            # Add risk category
            enriched_etf['risk_category'] = self._categorize_risk(etf)
            
            # Add geographic exposure
            enriched_etf['geographic_exposure'] = self._extract_geographic_exposure(etf)
            
            # Add sector exposure (if available)
            enriched_etf['sector_exposure'] = self._extract_sector_exposure(etf)
            
            enriched_etfs.append(enriched_etf)
        
        return {
            'enriched_etfs': enriched_etfs,
            'enrichment_count': len(enriched_etfs)
        }

    def _calculate_tax_efficiency(self, etf: Dict) -> float:
        """
        Calculate tax efficiency score (0-1)
        """
        
        score = 0.5  # Base score
        
        # Accumulating ETFs are more tax efficient
        if etf.get('is_accumulating', False):
            score += 0.3
        
        # Irish domicile is optimal for EU
        if etf.get('domicile') == 'Ireland':
            score += 0.2
        elif etf.get('domicile') == 'Luxembourg':
            score += 0.15
        
        # Physical replication is more tax efficient
        replication = etf.get('replication', '').lower()
        if 'physical' in replication:
            score += 0.1
        
        # Lower TER is better
        ter = etf.get('ter', 0.01)
        if ter < 0.002:  # < 0.2%
            score += 0.05
        elif ter > 0.008:  # > 0.8%
            score -= 0.05
        
        return min(max(score, 0), 1)

    def _calculate_liquidity_score(self, etf: Dict) -> float:
        """
        Calculate liquidity score based on AUM and trading volume
        """
        
        aum = etf.get('aum', 0)
        
        if aum > 1000:  # > €1bn
            return 1.0
        elif aum > 500:  # > €500m
            return 0.9
        elif aum > 100:  # > €100m
            return 0.8
        elif aum > 50:   # > €50m
            return 0.6
        else:
            return 0.3

    def _calculate_quality_score(self, etf: Dict) -> float:
        """
        Calculate overall quality score
        """
        
        tax_score = etf.get('tax_efficiency_score', 0.5)
        liquidity_score = etf.get('liquidity_score', 0.5)
        
        # Weight the scores
        quality_score = (tax_score * 0.4 + liquidity_score * 0.3)
        
        # Bonus for low TER
        ter = etf.get('ter', 0.01)
        if ter < 0.003:
            quality_score += 0.1
        
        # Bonus for established funds (age proxy via AUM)
        aum = etf.get('aum', 0)
        if aum > 500:
            quality_score += 0.1
        
        return min(quality_score, 1.0)

    def _categorize_risk(self, etf: Dict) -> str:
        """
        Categorize ETF risk level based on name and characteristics
        """
        
        name = etf.get('name', '').lower()
        
        if any(word in name for word in ['emerging', 'small cap', 'growth']):
            return 'high'
        elif any(word in name for word in ['bond', 'government', 'treasury']):
            return 'low'
        else:
            return 'medium'

    def _extract_geographic_exposure(self, etf: Dict) -> str:
        """
        Extract geographic exposure from ETF name
        """
        
        name = etf.get('name', '').lower()
        
        if 'world' in name or 'global' in name:
            return 'global'
        elif 'europe' in name or 'euro' in name:
            return 'europe'
        elif 'emerging' in name:
            return 'emerging_markets'
        elif 'us' in name or 'america' in name:
            return 'us'
        elif 'asia' in name or 'pacific' in name:
            return 'asia_pacific'
        else:
            return 'other'

    def _extract_sector_exposure(self, etf: Dict) -> Optional[str]:
        """
        Extract sector exposure from ETF name
        """
        
        name = etf.get('name', '').lower()
        
        sectors = {
            'technology': ['tech', 'technology', 'information'],
            'healthcare': ['health', 'pharma', 'biotech'],
            'financials': ['financial', 'bank', 'insurance'],
            'energy': ['energy', 'oil', 'gas'],
            'utilities': ['utilities', 'utility'],
            'real_estate': ['real estate', 'reit', 'property']
        }
        
        for sector, keywords in sectors.items():
            if any(keyword in name for keyword in keywords):
                return sector
        
        return None

    async def _store_processed_data(self, enriched_etfs: List[Dict]) -> Dict:
        """
        Store processed and enriched ETF data
        """
        
        timestamp = datetime.utcnow().isoformat()
        
        # Store to S3
        s3_key = f"processed/{timestamp}.json"
        self.s3.put_object(
            Bucket='etf-data-prod',
            Key=s3_key,
            Body=json.dumps(enriched_etfs, indent=2),
            ContentType='application/json'
        )
        
        # Store to DynamoDB
        table = self.dynamodb.Table('etf-data-prod')
        with table.batch_writer() as batch:
            for etf in enriched_etfs:
                item = {
                    'isin': etf['isin'],
                    'updated_at': timestamp,
                    **etf
                }
                batch.put_item(Item=item)
        
        return {
            'stored_count': len(enriched_etfs),
            's3_key': s3_key,
            'timestamp': timestamp
        }

    async def _publish_metrics(self, pipeline_results: Dict):
        """
        Publish pipeline metrics to CloudWatch
        """
        
        try:
            metrics = []
            
            # Pipeline duration
            if 'duration_minutes' in pipeline_results:
                metrics.append({
                    'MetricName': 'PipelineDuration',
                    'Value': pipeline_results['duration_minutes'],
                    'Unit': 'Count'
                })
            
            # ETF count
            if 'stages' in pipeline_results and 'collection' in pipeline_results['stages']:
                etf_count = pipeline_results['stages']['collection'].get('total_count', 0)
                metrics.append({
                    'MetricName': 'ETFCount',
                    'Value': etf_count,
                    'Unit': 'Count'
                })
            
            # Data quality score
            if 'stages' in pipeline_results and 'quality' in pipeline_results['stages']:
                quality_passed = 1 if pipeline_results['stages']['quality']['passed'] else 0
                metrics.append({
                    'MetricName': 'DataQualityPassed',
                    'Value': quality_passed,
                    'Unit': 'Count'
                })
            
            # Publish to CloudWatch
            if metrics:
                self.cloudwatch.put_metric_data(
                    Namespace='AmpliFolio/ETFPipeline',
                    MetricData=metrics
                )
                
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")

    async def _send_alert(self, message: str):
        """
        Send alert for pipeline failures
        """
        
        try:
            # In production, send to SNS topic for alerts
            sns = boto3.client('sns')
            sns.publish(
                TopicArn='arn:aws:sns:eu-west-1:123456789:etf-pipeline-alerts',
                Message=message,
                Subject='AmpliFolio ETF Pipeline Alert'
            )
        except Exception as e:
            logger.error(f"Error sending alert: {e}")


# Lambda handler for the data pipeline
async def handler(event, context):
    """
    AWS Lambda handler for the ETF data pipeline
    """
    
    pipeline = ETFDataPipeline()
    results = await pipeline.run_daily_pipeline()
    
    return {
        'statusCode': 200 if results['status'] == 'completed' else 500,
        'body': json.dumps(results)
    }
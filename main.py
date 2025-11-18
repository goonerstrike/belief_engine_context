#!/usr/bin/env python3
"""
Belief Engine - Main CLI Entry Point

Usage:
    python main.py --episode matthew_lacroix.txt
    python main.py --episode matthew_lacroix.txt --resume
    python main.py --episode matthew_lacroix.txt --no-wandb --verbose
"""
import sys
import time
import argparse
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from logging_config import EpisodeLogContext
import wandb_config
from src.utils.quality_scorer import QualityScorer
from src.utils.wandb_logger import WandBLogger
from src.utils.checkpoint import CheckpointManager, cleanup_old_checkpoints
from src.ingestion import TranscriptParser
from src.utterance import UtteranceSplitter
from src.beliefs import BeliefExtractor, BeliefRegistryManager

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Belief Engine - Extract and track beliefs from transcripts"
    )
    
    parser.add_argument(
        "--episode",
        required=True,
        help="Path to diarized transcript file"
    )
    
    parser.add_argument(
        "--episode-id",
        help="Custom episode ID (default: generated from filename)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    
    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Disable checkpointing"
    )
    
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable W&B logging"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        help=f"Number of parallel workers (default: {config.MAX_WORKERS})"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        help=f"Batch size for processing (default: {config.BATCH_SIZE})"
    )
    
    return parser.parse_args()

def run_pipeline(args):
    """Run the belief extraction pipeline."""
    
    # Generate episode ID
    transcript_path = Path(args.episode)
    episode_id = args.episode_id or transcript_path.stem
    
    logger.info("="*80)
    logger.info(f"BELIEF ENGINE - Starting Pipeline")
    logger.info(f"Episode ID: {episode_id}")
    logger.info(f"Transcript: {transcript_path}")
    logger.info("="*80)
    
    # Override config if specified
    if args.workers:
        config.MAX_WORKERS = args.workers
    if args.batch_size:
        config.BATCH_SIZE = args.batch_size
    if args.no_checkpoint:
        config.CHECKPOINT_ENABLED = False
    if args.no_wandb:
        config.WANDB_ENABLED = False
    if args.verbose:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    
    # Start timer
    start_time = time.time()
    
    # Initialize components
    quality_scorer = QualityScorer(episode_id=episode_id)
    checkpoint_manager = CheckpointManager(episode_id=episode_id)
    
    # Initialize W&B
    wandb_run = None
    wandb_logger_obj = None
    
    if config.WANDB_ENABLED:
        wandb_run = wandb_config.initialize_wandb(
            episode_id=episode_id,
            tags=["pipeline-run"]
        )
        wandb_logger_obj = WandBLogger()
    
    try:
        with EpisodeLogContext(episode_id=episode_id):
            
            # =================================================================
            # STAGE 1: INGESTION
            # =================================================================
            logger.info("STAGE 1: Ingestion")
            
            parser = TranscriptParser(quality_scorer=quality_scorer)
            episode, utterances = parser.parse(
                str(transcript_path),
                episode_id=episode_id
            )
            
            if wandb_logger_obj:
                wandb_logger_obj.log_utterances_parsed(len(utterances))
            
            # =================================================================
            # STAGE 2: UTTERANCE SPLITTING
            # =================================================================
            logger.info("STAGE 2: Utterance Splitting")
            
            splitter = UtteranceSplitter()
            atomic_utterances = splitter.split(utterances)
            
            # Checkpoint
            if config.CHECKPOINT_ENABLED:
                utterances_data = [u.dict() for u in atomic_utterances]
                checkpoint_manager.save(
                    "utterances",
                    utterances_data,
                    stats={"count": len(atomic_utterances)}
                )
            
            # =================================================================
            # STAGE 3: BELIEF EXTRACTION
            # =================================================================
            logger.info("STAGE 3: Belief Extraction")
            
            extractor = BeliefExtractor(
                quality_scorer=quality_scorer,
                wandb_logger=wandb_logger_obj
            )
            
            # Extract beliefs from first 10 utterances for demo
            # In production, process all utterances
            sample_utterances = atomic_utterances[:10]
            logger.info(f"Processing {len(sample_utterances)} utterances (demo mode)")
            
            beliefs = extractor.extract(sample_utterances)
            
            # Checkpoint
            if config.CHECKPOINT_ENABLED:
                beliefs_data = [b.dict() for b in beliefs]
                checkpoint_manager.save(
                    "beliefs_raw",
                    beliefs_data,
                    stats={"count": len(beliefs)}
                )
            
            # =================================================================
            # STAGE 4: CANONICALIZATION
            # =================================================================
            logger.info("STAGE 4: Canonicalization")
            
            registry_manager = BeliefRegistryManager()
            registry_manager.load()
            
            canonical_beliefs = registry_manager.canonicalize(beliefs, episode_id)
            
            registry_manager.save()
            
            if wandb_logger_obj:
                wandb_logger_obj.log_canonical_beliefs_created(len(canonical_beliefs))
            
            # Checkpoint
            if config.CHECKPOINT_ENABLED:
                canonical_data = [c.dict() for c in canonical_beliefs]
                checkpoint_manager.save(
                    "canonical_beliefs",
                    canonical_data,
                    stats={"count": len(canonical_beliefs)}
                )
            
            # =================================================================
            # PIPELINE COMPLETE
            # =================================================================
            
            execution_time = time.time() - start_time
            quality_scorer.metrics.execution_time_seconds = execution_time
            
            # Generate quality report
            quality_report = quality_scorer.generate_report()
            quality_scorer.save_report()
            
            logger.info("="*80)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"Episode: {episode_id}")
            logger.info(f"Utterances: {len(atomic_utterances)}")
            logger.info(f"Beliefs Extracted: {len(beliefs)}")
            logger.info(f"Canonical Beliefs: {len(canonical_beliefs)}")
            logger.info(f"Quality Score: {quality_report['quality_score']:.1f}")
            logger.info(f"Quality Grade: {quality_report['quality_grade']}")
            logger.info(f"Execution Time: {execution_time:.1f}s")
            logger.info("="*80)
            
            # Log to W&B
            if wandb_logger_obj:
                wandb_logger_obj.log_quality_metrics(
                    score=quality_report['quality_score'],
                    grade=quality_report['quality_grade'],
                    errors_count=quality_report['errors_count'],
                    malformed_beliefs=quality_report['malformed_beliefs_count'],
                    registry_mismatches=quality_report['registry_mismatches_count']
                )
                
                # Upload artifacts
                wandb_logger_obj.upload_quality_report(
                    config.CHECKPOINTS_DIR / episode_id / "quality_report.json"
                )
            
            # Finish W&B
            if wandb_run:
                wandb_config.finish_wandb(exit_code=0)
            
            return 0
            
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        if wandb_run:
            wandb_config.finish_wandb(exit_code=1)
        return 1
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        if wandb_run:
            wandb_config.log_alert(
                title="Pipeline Failed",
                text=f"Error: {str(e)}",
                level="ERROR"
            )
            wandb_config.finish_wandb(exit_code=1)
        return 1

def main():
    """Main entry point."""
    try:
        # Validate configuration
        config.validate_config()
        
        # Parse arguments
        args = parse_args()
        
        # Run pipeline
        exit_code = run_pipeline(args)
        
        # Cleanup old checkpoints
        if config.CHECKPOINT_ENABLED:
            cleanup_old_checkpoints()
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()


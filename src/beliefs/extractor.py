"""
Belief extraction using OpenAI API.
"""
from typing import List, Dict, Any
import json
import uuid
import time
from loguru import logger
import openai
import config
from src.models import Utterance, Belief
from src.utils.retry import retry_openai_call
from src.utils.parallel import ParallelExecutor, RateLimiter, batch_items
from src.utils.quality_scorer import QualityScorer
from src.utils.wandb_logger import WandBLogger
from src.utils.exceptions import BeliefExtractionError

class BeliefExtractor:
    """
    Extract beliefs from utterances using OpenAI GPT-4.
    
    Usage:
        extractor = BeliefExtractor(quality_scorer=scorer, wandb_logger=wb)
        beliefs = extractor.extract(utterances)
    """
    
    def __init__(
        self,
        quality_scorer: QualityScorer = None,
        wandb_logger: WandBLogger = None
    ):
        """
        Initialize belief extractor.
        
        Args:
            quality_scorer: Optional quality scorer
            wandb_logger: Optional W&B logger
        """
        self.quality_scorer = quality_scorer
        self.wandb_logger = wandb_logger
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    def extract(self, utterances: List[Utterance]) -> List[Belief]:
        """
        Extract beliefs from utterances (parallel).
        
        Args:
            utterances: List of utterances
        
        Returns:
            List of beliefs
        """
        logger.info(f"Extracting beliefs from {len(utterances)} utterances")
        
        # Batch utterances
        batches = batch_items(utterances, config.BATCH_SIZE)
        logger.info(f"Created {len(batches)} batches of size {config.BATCH_SIZE}")
        
        # Process batches in parallel with rate limiting
        rate_limiter = RateLimiter()
        executor = ParallelExecutor(rate_limiter=rate_limiter)
        
        all_beliefs = []
        
        if config.ENABLE_PARALLEL:
            batch_results = executor.map(self._extract_batch, batches)
            for batch_result in batch_results:
                if batch_result:
                    all_beliefs.extend(batch_result)
        else:
            for batch in batches:
                batch_result = self._extract_batch(batch)
                if batch_result:
                    all_beliefs.extend(batch_result)
        
        logger.info(f"Extracted {len(all_beliefs)} beliefs total")
        
        if self.wandb_logger:
            self.wandb_logger.log_beliefs_extracted(len(all_beliefs))
        
        return all_beliefs
    
    def _extract_batch(self, utterances: List[Utterance]) -> List[Belief]:
        """Extract beliefs from a batch of utterances."""
        beliefs = []
        
        for utterance in utterances:
            try:
                utt_beliefs = self._extract_from_utterance(utterance)
                beliefs.extend(utt_beliefs)
                
            except Exception as e:
                logger.error(f"Failed to extract from utterance {utterance.id}: {e}")
                if self.quality_scorer:
                    self.quality_scorer.metrics.add_api_error(str(e))
        
        return beliefs
    
    @retry_openai_call(max_retries=3)
    def _extract_from_utterance(self, utterance: Utterance) -> List[Belief]:
        """Extract beliefs from a single utterance."""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_extraction_prompt(utterance)
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting beliefs from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=config.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            latency = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost = self._estimate_cost(tokens_used)
            
            # Log API call
            if self.wandb_logger:
                self.wandb_logger.log_api_call(
                    tokens=tokens_used,
                    cost=cost,
                    latency=latency,
                    success=True
                )
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Create Belief objects
            beliefs = []
            for belief_data in data.get("beliefs", []):
                try:
                    belief = Belief(
                        id=str(uuid.uuid4()),
                        utterance_id=utterance.id,
                        belief_text=belief_data["belief_text"],
                        confidence=belief_data["confidence"],
                        original_quote=belief_data.get("original_quote", utterance.text),
                        extraction_flags=belief_data.get("extraction_flags", {})
                    )
                    beliefs.append(belief)
                except Exception as e:
                    logger.warning(f"Malformed belief in response: {e}")
                    if self.quality_scorer:
                        self.quality_scorer.metrics.add_malformed_belief()
            
            return beliefs
            
        except Exception as e:
            if self.wandb_logger:
                self.wandb_logger.log_api_call(tokens=0, cost=0, latency=time.time() - start_time, success=False)
            raise
    
    def _build_extraction_prompt(self, utterance: Utterance) -> str:
        """Build extraction prompt."""
        return f"""Extract atomic, declarative beliefs from the following utterance.

Speaker: {utterance.speaker}
Utterance: "{utterance.text}"

For each belief, provide:
1. belief_text: The atomic belief statement (declarative, concise)
2. confidence: Confidence score 0.0-1.0
3. original_quote: Direct quote from utterance
4. extraction_flags: Boolean flags (at least one must be true)

Extraction Flags:
- q16_first_principles: Core belief (first principles)
- q17_worldview: Worldview belief
- q18_moral_framework: Moral/ethical framework
- q19_epistemology: How knowledge is acquired
- q20_ontology: Nature of reality
- q21_reasoning_pattern: Reasoning/logic pattern
- q22_assumption: Underlying assumption
- q23_surface_opinion: Surface-level opinion
- q24_factual_claim: Factual claim
- q25_prediction: Future prediction
- q26_value_judgment: Value judgment

Return JSON format:
{{
  "beliefs": [
    {{
      "belief_text": "...",
      "confidence": 0.0-1.0,
      "original_quote": "...",
      "extraction_flags": {{
        "q16_first_principles": true/false,
        ...
      }}
    }}
  ]
}}

Only extract genuine beliefs, not questions or commands."""
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate API cost (rough approximation)."""
        # GPT-4 pricing: ~$0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)
        # Simplified: average $0.045 per 1K tokens
        return (tokens / 1000) * 0.045


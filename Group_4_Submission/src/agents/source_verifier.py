from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import ResearchState
from ..config import Config
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    from sklearn.feature_extraction.text import TfidfVectorizer

class SourceVerifier:
    """
    Agent responsible for verifying claims against source content.
    
    Uses a two-step verification process:
    1. Fast pass using cosine similarity (embeddings or TF-IDF).
    2. Slow pass using LLM for claims that fail the fast pass.
    """
    def __init__(self):
        """
        Initializes the SourceVerifier with LLM and embedding models.
        """
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.prompt = ChatPromptTemplate.from_template(
            """Verify the following claims against the source text.
            
            Claim: {claim}
            Source URL: {source}
            Source Text: {content}
            
            Is the claim supported by the source text?
            Return JSON:
            {{
                "supported": boolean,
                "reasoning": "explanation",
                "hallucination_score": float (0.0 means supported, 1.0 means hallucination)
            }}
            """
        )
        
        # Initialize Embedding Model
        if HAS_TRANSFORMERS:
            # Reusing the lighter model for speed
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.vectorizer = TfidfVectorizer(stop_words='english')

    def run(self, state: ResearchState) -> dict:
        """
        Executes the source verification process.
        
        Args:
            state: Current research state containing claims and documents.
            
        Returns:
            Dictionary containing hallucination flags and verification logs.
        """
        print("--- DE-BUNKER AGENT ---")
        claims = state.get("claims", [])
        documents = state.get("documents", [])
        
        hallucination_flags = []
        logs = []
        
        # Create a map of url -> content for valid verification
        doc_map = {d.get("metadata", {}).get("url"): d.get("content", "") for d in documents}
        
        llm_calls = 0
        fast_pass_count = 0
        
        for claim in claims:
            source_url = claim.get("source")
            content = doc_map.get(source_url)
            
            if content:
                try:
                    is_verified = False
                    similarity_score = 0.0
                    
                    # --- FAST PASS: Cosine Similarity ---
                    # Split content into rough chunks (sentences/paragraphs)
                    # Simple split by newline or period for efficiency
                    chunks = [c.strip() for c in content.replace('.', '\n').split('\n') if len(c.strip()) > 20]
                    
                    if not chunks:
                        chunks = [content[:1000]] # Fallback to single chunk
                    
                    claim_text = claim.get("claim_text", "")
                    
                    if HAS_TRANSFORMERS:
                        # Encode claim and chunks
                        claim_embedding = self.embedding_model.encode([claim_text])
                        chunk_embeddings = self.embedding_model.encode(chunks)
                        
                        # Compute similarity
                        sims = cosine_similarity(claim_embedding, chunk_embeddings)[0]
                        max_sim = np.max(sims)
                        similarity_score = float(max_sim)
                        
                    else:
                        # TF-IDF Fallback
                        all_texts = [claim_text] + chunks
                        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
                        # Cosine sim of claim (idx 0) vs all chunks (idx 1:)
                        sims = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
                        if len(sims) > 0:
                            max_sim = np.max(sims)
                            similarity_score = float(max_sim)
                    
                    # Threshold check
                    if similarity_score > 0.85:
                        is_verified = True
                        fast_pass_count += 1
                        # print(f"✅ Fast-Pass Verified: '{claim_text}' (Sim: {similarity_score:.2f})")
                    
                    # --- SLOW PASS: LLM Verification ---
                    if not is_verified:
                        llm_calls += 1
                        # Truncate content for LLM context window
                        truncated_content = content[:2000]
                        chain = self.prompt | self.llm
                        result = chain.invoke({
                            "claim": claim_text,
                            "source": source_url,
                            "content": truncated_content
                        })
                        
                        analysis = result.content.strip()
                        if analysis.startswith("```json"):
                            analysis = analysis[7:-3]
                        elif analysis.startswith("```"):
                            analysis = analysis[3:-3]
                            
                        verification = json.loads(analysis)
                        
                        if verification.get("hallucination_score", 0) > 0.5:
                            print(f"Potential hallucination detected: {claim_text}")
                            hallucination_flags.append({
                                "claim": claim_text,
                                "reason": verification.get("reasoning"),
                                "score": verification.get("hallucination_score")
                            })
                    
                except Exception as e:
                    print(f"Error verifying claim: {e}")
            else:
                 # No source text found to verify against
                 pass
        
        msg = f"De-bunker finished. {fast_pass_count} verified via Similarity. {llm_calls} verified via LLM. {len(hallucination_flags)} flagged."
        print(msg)
        logs.append(msg)
        
        return {"hallucination_flags": hallucination_flags, "logs": logs, "stage": "insight"}

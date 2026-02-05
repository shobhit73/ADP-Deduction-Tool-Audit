
import numpy as np
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticRouter:
    def __init__(self):
        self.model = None
        self.intent_embeddings = None
        self.intents = []
        self.tool_map = {}
        self.initialized = False

    def initialize(self):
        """Lazy load the model to avoid startup lag if not needed immediately"""
        if self.initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
            # Load a tiny, fast model (80MB)
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self._train_routes()
            self.initialized = True
            logger.info("Semantic Router initialized successfully.")
        except ImportError:
            st.warning("⚠️ Library 'sentence-transformers' not found. AI features disabled (using keyword fallback).")
            logger.error("sentence-transformers not installed.")
        except Exception as e:
            st.error(f"⚠️ Error loading model: {e}")
            logger.error(f"Model load error: {e}")

    def _train_routes(self):
        """Define the intent phrasing for each tool"""
        
        # Define Training Data: {Tool_Key: [List of Phrases]}
        routes = {
            "Deduction Audit": [
                "run deduction audit",
                "check tax discrepancies",
                "compare benefit deductions",
                "find mismatch in withholding",
                "medical deduction audit",
                "401k mismatch",
                "adp vs uzio deductions"
            ],
            "Prior Payroll Audit": [
                "run prior payroll audit",
                "check year to date values",
                "ytd mismatch",
                "migration data check",
                "verify payroll history",
                "gross pay comparison",
                "net pay mismatch"
            ],
            "Census Audit": [
                "run census audit",
                "employee demographic check",
                "dob mismatch",
                "wrong social security number",
                "address mismatch",
                "name spelling check",
                "termination date verify"
            ],
            "Payment & Emergency Audit": [
                "check payment methods",
                "verify direct deposit",
                "emergency contact missing",
                "account number mismatch",
                "routing number check",
                "payment distribution issue"
            ],
            "Paycom Census Audit": [
                "run paycom census",
                "compare paycom and uzio",
                "paycom demographic check",
                "switch to paycom audit",
                "paycom file check"
            ]
        }

        self.intents = []
        self.tool_map = {}
        corpus = []

        for tool, phrases in routes.items():
            for phrase in phrases:
                self.intents.append(phrase)
                self.tool_map[phrase] = tool
                corpus.append(phrase)

        # Pre-compute embeddings for all phrases
        if self.model:
            self.intent_embeddings = self.model.encode(corpus)

    def predict(self, query):
        """
        Returns the best matching tool and a confidence score.
        If library is missing, returns None.
        """
        if not self.initialized:
            self.initialize()
        
        if not self.initialized or self.model is None:
            return None, 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            # Fallback simple dot product if sklearn not present (less accurate normalizing but works for unit vectors)
           pass

        # Encode user query
        query_vec = self.model.encode([query])
        
        # Calculate similarities (Cosine Similarity)
        # SentenceTransformer embeddings are often normalized, but let's be safe.
        # Simple dot product for speed usually suffices for ranking.
        scores = np.dot(self.intent_embeddings, query_vec.T).flatten()
        
        best_idx = np.argmax(scores)
        best_score = scores[best_idx]
        best_phrase = self.intents[best_idx]
        predicted_tool = self.tool_map[best_phrase]

        logger.info(f"Query: '{query}' -> Matched: '{best_phrase}' ({best_score:.4f}) -> Tool: {predicted_tool}")

        return predicted_tool, float(best_score)

# Singleton Instance 
router = SemanticRouter()

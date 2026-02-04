"""
Base Form Agent class - Foundation for all IRS form agents
Implements the codebase-style architecture from the paper
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.types import AgentResponse, Citation
from src.core.llm_engine import LLMEngine
from src.tools.pdf_navigator import PDFNavigator


class FormAgent(ABC):
    """
    Base class for all IRS form agents.
    
    Each form agent:
    1. Has typed inputs/outputs (defined in subclass)
    2. Uses IRS PDF instructions for grounding
    3. Can cite sources for decisions
    4. Follows a clear processing pipeline
    """
    
    def __init__(
        self,
        form_name: str,
        llm: Optional[LLMEngine] = None,
        pdf_navigator: Optional[PDFNavigator] = None,
        enable_citations: bool = True
    ):
        """
        Initialize form agent
        
        Args:
            form_name: IRS form name (e.g., "1040", "schedule-c")
            llm: LLM engine instance
            pdf_navigator: PDF navigator instance
            enable_citations: Whether to track IRS citations
        """
        self.form_name = form_name
        self.llm = llm or LLMEngine()
        self.pdf_nav = pdf_navigator or PDFNavigator()
        self.enable_citations = enable_citations
        
        # Storage for citations and errors
        self.citations: List[Citation] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Load form PDF
        self._load_form_pdf()
    
    def _load_form_pdf(self):
        """Load IRS instructions PDF for this form"""
        try:
            # Try to open instruction PDF
            success = self.pdf_nav.open(f"i{self.form_name}")  # Instructions
            if not success:
                # Fallback to form PDF
                success = self.pdf_nav.open(self.form_name)
            
            if not success:
                self.warnings.append(
                    f"Could not load PDF for {self.form_name}. "
                    "Agent will work without IRS grounding."
                )
        except Exception as e:
            self.warnings.append(f"Error loading PDF: {e}")
    
    @abstractmethod
    def process(self, inputs: Any) -> Any:
        """
        Process the form with given inputs.
        Must be implemented by each form agent.
        
        Args:
            inputs: Typed input data (specific to form)
            
        Returns:
            Typed output data (specific to form)
        """
        pass
    
    def get_irs_instructions(self, line: str) -> str:
        """
        Get IRS instructions for a specific line.
        This grounds the agent's reasoning in official documentation.
        
        Args:
            line: Line identifier (e.g., "Line 11", "Line 1z")
            
        Returns:
            IRS instructions text
        """
        try:
            instructions = self.pdf_nav.get_line_instructions(line, self.form_name)
            return instructions if instructions else f"No instructions found for {line}"
        except Exception as e:
            self.warnings.append(f"Error getting instructions for {line}: {e}")
            return f"Unable to retrieve instructions for {line}"
    
    def cite(self, line: str, source: str, reasoning: str):
        """
        Record an IRS citation for a decision.
        
        Args:
            line: Form line (e.g., "Line 11")
            source: IRS source (e.g., "Form 1040 Instructions, Page 25")
            reasoning: Agent's reasoning
        """
        if self.enable_citations:
            citation = Citation(
                form=self.form_name,
                line=line,
                source=source,
                reasoning=reasoning
            )
            self.citations.append(citation)
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
    
    def create_response(self, outputs: Any) -> AgentResponse:
        """
        Create standardized agent response.
        
        Args:
            outputs: Form-specific output data
            
        Returns:
            AgentResponse with outputs, citations, errors
        """
        return AgentResponse(
            form_name=self.form_name,
            outputs=outputs,
            citations=self.citations,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def generate_with_context(
        self,
        prompt: str,
        irs_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate LLM response with optional IRS context.
        
        Args:
            prompt: User prompt
            irs_context: IRS instructions to include
            system_prompt: System instructions
            
        Returns:
            LLM response
        """
        # Build full prompt with IRS grounding
        full_prompt = prompt
        
        if irs_context:
            full_prompt = f"""IRS Official Instructions:
{irs_context}

---

{prompt}
"""
        
        default_system = f"""You are a tax preparation agent specialized in IRS Form {self.form_name}.

Your responsibilities:
1. Follow IRS instructions exactly
2. Cite sources for non-trivial decisions
3. Flag any ambiguities or errors
4. Use deterministic calculations when possible
5. Be conservative - when in doubt, consult instructions

Respond with clear, step-by-step reasoning."""

        system = system_prompt or default_system
        
        return self.llm.generate(full_prompt, system)
    
    def calculate_line(
        self,
        line: str,
        calculation_prompt: str,
        use_irs_context: bool = True
    ) -> float:
        """
        Calculate a specific form line using LLM with optional IRS grounding.
        
        Args:
            line: Line identifier
            calculation_prompt: Prompt describing the calculation
            use_irs_context: Whether to include IRS instructions
            
        Returns:
            Calculated value
        """
        irs_context = None
        if use_irs_context:
            irs_context = self.get_irs_instructions(line)
        
        prompt = f"""{calculation_prompt}

Respond with ONLY the numeric value, no explanation or currency symbols.
If the value is 0 or not applicable, respond with "0".
"""
        
        try:
            response = self.generate_with_context(prompt, irs_context)
            # Extract number from response
            value = self._extract_number(response)
            return value
        except Exception as e:
            self.add_error(f"Error calculating {line}: {e}")
            return 0.0
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text response"""
        import re
        
        # Remove common currency symbols and commas
        text = text.replace('$', '').replace(',', '').strip()
        
        # Find first number in text
        match = re.search(r'-?\d+\.?\d*', text)
        if match:
            return float(match.group())
        
        return 0.0
    
    def __str__(self) -> str:
        return f"FormAgent({self.form_name})"
    
    def __repr__(self) -> str:
        return self.__str__()

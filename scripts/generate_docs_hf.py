"""
Aether Wireless Telecom Policy Document Generator
==================================================

Self-contained document generator using Hugging Face Inference Providers.

Setup
-----

Install:

    pip install huggingface_hub python-dotenv reportlab pypdf

Create .env:

    HF_TOKEN=hf_your_token_here

Run:

    python scripts/generate_docs.py --limit 1 --keep-md --keep-txt

Examples:

    python scripts/generate_docs.py --limit 1
    python scripts/generate_docs.py --limit 2 --keep-md
    python scripts/generate_docs.py --only billing --limit 2
    python scripts/generate_docs.py --only roaming
"""


from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from pypdf import PdfReader

    HAVE_PDF_READER = True
except ImportError:
    HAVE_PDF_READER = False


# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_PATH = PROJECT_ROOT / ".env"

RAW_DIR = PROJECT_ROOT / "data" / "raw"


# ============================================================================
# HUGGING FACE CONFIGURATION
# ============================================================================

HF_TOKEN = None

MODEL = "openai/gpt-oss-120b"

TEMPERATURE = 0.3
MAX_TOKENS = 4096

TIMEOUT_SECONDS = 120

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3


# ============================================================================
# DOCUMENT GENERATION CONFIGURATION
# ============================================================================

LONG_DOC_SECTIONS = 8

OUTLINE_MAX_TOKENS = 1200
SECTION_MAX_TOKENS = 2500
FAQ_MAX_TOKENS = 1500
TABLE_SECTION_MAX_TOKENS = 1000

MAX_COMPLETION_TOKENS_TO_WARN = 4096

MIN_PAGES = 5

TABLE_SECTION_NAME = "Key Rules Summary"


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger("document-generator")


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass(frozen=True)
class KnowledgeMetadata:
    """Metadata describing a telecom policy document."""

    doc_id: str
    title: str
    version: str
    department: str
    category: str
    last_updated: str
    description: str


@dataclass
class KnowledgeDocument:
    """Generated knowledge-base document."""

    metadata: KnowledgeMetadata
    body_md: str


# ============================================================================
# DOCUMENT CATALOG
# ============================================================================

DOCUMENT_CATALOG: list[KnowledgeMetadata] = [
    KnowledgeMetadata(
        doc_id="BILL-001",
        title="Postpaid Billing and Payment Policy",
        version="v1.0",
        department="Billing",
        category="billing",
        last_updated="2026-09-01",
        description=(
            "Rules governing postpaid billing cycles, payment methods, "
            "due dates, failed payments, and account status."
        ),
    ),
    KnowledgeMetadata(
        doc_id="BILL-002",
        title="Late Payment and Account Suspension Policy",
        version="v1.0",
        department="Billing",
        category="billing",
        last_updated="2026-09-01",
        description=(
            "Rules governing overdue balances, payment reminders, "
            "suspension, restoration, and account handling."
        ),
    ),
    KnowledgeMetadata(
        doc_id="MOB-001",
        title="Mobile Plan Change Policy",
        version="v1.0",
        department="Mobile",
        category="mobile",
        last_updated="2026-09-01",
        description=(
            "Rules governing changes between mobile plans, effective dates, "
            "eligibility, and customer responsibilities."
        ),
    ),
    KnowledgeMetadata(
        doc_id="MOB-002",
        title="SIM Replacement Policy",
        version="v1.0",
        department="Mobile",
        category="mobile",
        last_updated="2026-09-01",
        description=(
            "Rules governing lost, damaged, stolen, and replacement SIM cards."
        ),
    ),
    KnowledgeMetadata(
        doc_id="ROAM-001",
        title="International Roaming Policy",
        version="v1.0",
        department="Roaming",
        category="roaming",
        last_updated="2026-09-01",
        description=(
            "Rules governing international roaming eligibility, usage, "
            "charges, restrictions, and customer notifications."
        ),
    ),
    KnowledgeMetadata(
        doc_id="ROAM-002",
        title="Roaming Data Usage Policy",
        version="v1.0",
        department="Roaming",
        category="roaming",
        last_updated="2026-09-01",
        description=(
            "Rules governing international mobile data usage, limits, "
            "notifications, and billing."
        ),
    ),
    KnowledgeMetadata(
        doc_id="CUST-001",
        title="Customer Account Verification Policy",
        version="v1.0",
        department="Customer Service",
        category="customer",
        last_updated="2026-09-01",
        description=(
            "Rules governing customer identity and account verification "
            "during customer-service interactions."
        ),
    ),
    KnowledgeMetadata(
        doc_id="CUST-002",
        title="Customer Account Closure Policy",
        version="v1.0",
        department="Customer Service",
        category="customer",
        last_updated="2026-09-01",
        description=(
            "Rules governing account closure requests, outstanding balances, "
            "equipment, and final billing."
        ),
    ),
    KnowledgeMetadata(
        doc_id="COMP-001",
        title="Customer Data Protection Policy",
        version="v1.0",
        department="Compliance",
        category="compliance",
        last_updated="2026-09-01",
        description=(
            "Rules governing protection, access, handling, and disclosure "
            "of customer information."
        ),
    ),
    KnowledgeMetadata(
        doc_id="COMP-002",
        title="Customer Identity and KYC Policy",
        version="v1.0",
        department="Compliance",
        category="compliance",
        last_updated="2026-09-01",
        description=(
            "Rules governing customer identity verification and KYC controls."
        ),
    ),
]


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """
You are a senior telecom policy documentation specialist.

You create structured internal knowledge-base documents for Aether Wireless.

Your output will be consumed by a Retrieval-Augmented Generation (RAG)
system, so accuracy, clarity, consistency, and explicit policy rules are
more important than creative writing.

IMPORTANT RULES:

1. Never invent company-specific policies.
2. Never invent prices, fees, thresholds, dates, deadlines, percentages,
   eligibility requirements, or penalties unless they are explicitly
   provided in the input.
3. If a specific value is not provided, describe the rule generically.
4. Keep terminology consistent throughout the document.
5. Clearly distinguish requirements, exceptions, procedures, and examples.
6. Prefer short, factual paragraphs.
7. Use Markdown headings.
8. Use tables when structured comparison is useful.
9. Do not mention that the document was generated by an AI.
10. Do not add commentary outside the requested document.
11. Do not create fictional contact information.
12. Do not reference policies that are not described in the metadata or
    requested topic.
13. The document should be suitable for enterprise RAG retrieval.

The company name is:

Aether Wireless
"""


# ============================================================================
# LLM CLIENT
# ============================================================================


class LLMClient:
    """
    Hugging Face LLM client.

    This class intentionally exposes the same basic generate() contract
    used by the document generator.
    """

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("HF_TOKEN is missing.")

        self.model = MODEL
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS

        self.client = InferenceClient(
            api_key=token,
            timeout=TIMEOUT_SECONDS,
        )

    def generate(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int | None = None,
        retries: int = MAX_RETRIES,
    ) -> tuple[str, dict]:
        """
        Generate a response using Hugging Face.

        Returns:
            (content, usage)
        """

        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    "LLM request | model=%s | attempt=%d/%d",
                    self.model,
                    attempt,
                    retries,
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=list(messages),
                    temperature=self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )

                if not response.choices:
                    raise RuntimeError(
                        "Hugging Face returned no choices."
                    )

                content = response.choices[0].message.content

                if not content:
                    raise RuntimeError(
                        "Hugging Face returned empty content."
                    )

                usage: dict = {}

                if response.usage:
                    usage = {
                        "prompt_tokens": getattr(
                            response.usage,
                            "prompt_tokens",
                            0,
                        ),
                        "completion_tokens": getattr(
                            response.usage,
                            "completion_tokens",
                            0,
                        ),
                        "total_tokens": getattr(
                            response.usage,
                            "total_tokens",
                            0,
                        ),
                    }

                logger.info(
                    "LLM request successful | model=%s",
                    self.model,
                )

                return content.strip(), usage

            except Exception as exc:
                last_error = exc

                error_text = str(exc)

                logger.warning(
                    "LLM request failed | attempt=%d/%d | error=%s",
                    attempt,
                    retries,
                    error_text,
                )

                if attempt >= retries:
                    break

                time.sleep(RETRY_DELAY_SECONDS)

        raise RuntimeError(
            "Hugging Face generation failed."
        ) from last_error


# ============================================================================
# PROMPT HELPERS
# ============================================================================


def build_document_context(
    metadata: KnowledgeMetadata,
) -> str:
    """Build shared document context."""

    return f"""
Document ID: {metadata.doc_id}
Title: {metadata.title}
Version: {metadata.version}
Department: {metadata.department}
Category: {metadata.category}
Last Updated: {metadata.last_updated}

Document description:
{metadata.description}
""".strip()


# ============================================================================
# DOCUMENT GENERATOR
# ============================================================================


class DocumentGenerator:
    """Generate a complete telecom policy document."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(
        self,
        metadata: KnowledgeMetadata,
    ) -> KnowledgeDocument:
        """Generate a complete document."""

        logger.info(
            "Generating document | id=%s | title=%s",
            metadata.doc_id,
            metadata.title,
        )

        if LONG_DOC_SECTIONS <= 0:
            raise ValueError(
                "LONG_DOC_SECTIONS must be greater than zero."
            )

        body_md = self._generate_long_document(metadata)

        body_md = self._clean_markdown(body_md)

        return KnowledgeDocument(
            metadata=metadata,
            body_md=body_md,
        )

    # ------------------------------------------------------------------------
    # LONG DOCUMENT
    # ------------------------------------------------------------------------

    def _generate_long_document(
        self,
        metadata: KnowledgeMetadata,
    ) -> str:
        """Generate the complete multi-section document."""

        outline = self._generate_outline(metadata)

        headings = self._extract_h2_headings(outline)

        if not headings:
            logger.warning(
                "No H2 headings found in generated outline. "
                "Using fallback headings."
            )

            headings = self._fallback_headings()

        headings = headings[:LONG_DOC_SECTIONS]

        sections: list[str] = []

        for index, heading in enumerate(headings, start=1):
            logger.info(
                "Generating section %d/%d | %s",
                index,
                len(headings),
                heading,
            )

            section = self._generate_section(
                metadata,
                heading,
            )

            sections.append(section)

        table_section = self._generate_table_section(metadata)

        overview = self._generate_section(
            metadata,
            "Overview",
        )

        faq = self._generate_faq(metadata)

        document_parts = [
            overview,
            *sections,
            table_section,
            faq,
        ]

        return "\n\n".join(
            part.strip()
            for part in document_parts
            if part and part.strip()
        )

    # ------------------------------------------------------------------------
    # OUTLINE
    # ------------------------------------------------------------------------

    def _generate_outline(
        self,
        metadata: KnowledgeMetadata,
    ) -> str:
        """Generate document outline."""

        prompt = f"""
Create a Markdown outline for this telecom policy document.

{build_document_context(metadata)}

Requirements:

- Start with H2 headings using exactly this format:

## Heading

- Create approximately {LONG_DOC_SECTIONS} substantive policy sections.
- Include sections covering rules, eligibility, procedures,
  exceptions, responsibilities, and operational handling where relevant.
- Do not include Overview as an outline section.
- Do not include FAQs as an outline section.
- Do not include the final Key Rules Summary table as an outline section.
- Do not write the actual document content.
- Return only the Markdown outline.
"""

        content, usage = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=OUTLINE_MAX_TOKENS,
        )

        self._log_usage(
            metadata.doc_id,
            usage,
            "outline",
        )

        return content

    # ------------------------------------------------------------------------
    # SECTION
    # ------------------------------------------------------------------------

    def _generate_section(
        self,
        metadata: KnowledgeMetadata,
        heading: str,
    ) -> str:
        """Generate one policy section."""

        prompt = f"""
Write one complete section of the telecom policy.

Document:

{build_document_context(metadata)}

Section title:

{heading}

Requirements:

- Start with exactly:

## {heading}

- Provide factual policy content.
- Explain the applicable rule clearly.
- Include operational steps when appropriate.
- Include exceptions when relevant.
- Include customer responsibilities when relevant.
- Include internal staff responsibilities when relevant.
- Do not invent specific prices, fees, deadlines, thresholds,
  percentages, or penalties.
- Do not refer to information that is unavailable.
- Use concise paragraphs and bullet lists where useful.
- Do not create another H2 section.
- Do not create FAQs.
"""

        content, usage = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=SECTION_MAX_TOKENS,
        )

        self._log_usage(
            metadata.doc_id,
            usage,
            f"section:{heading}",
        )

        return content.strip()

    # ------------------------------------------------------------------------
    # TABLE
    # ------------------------------------------------------------------------

    def _generate_table_section(
        self,
        metadata: KnowledgeMetadata,
    ) -> str:
        """Generate a structured summary table."""

        prompt = f"""
Create the final Key Rules Summary for this telecom policy.

Document:

{build_document_context(metadata)}

Requirements:

- Start with:

## {TABLE_SECTION_NAME}

- Then provide a Markdown table.
- Use columns such as:
  Rule | Requirement | Operational Handling
- Include only rules supported by the document metadata and topic.
- Do not invent prices, fees, dates, thresholds, or percentages.
- Keep each table cell concise.
- Return only this section.
"""

        content, usage = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=TABLE_SECTION_MAX_TOKENS,
        )

        self._log_usage(
            metadata.doc_id,
            usage,
            "table",
        )

        return content.strip()

    # ------------------------------------------------------------------------
    # FAQ
    # ------------------------------------------------------------------------

    def _generate_faq(
        self,
        metadata: KnowledgeMetadata,
    ) -> str:
        """Generate FAQ section."""

        prompt = f"""
Create a Frequently Asked Questions section for this telecom policy.

Document:

{build_document_context(metadata)}

Requirements:

- Start with:

## FAQs

- Generate 5 to 8 useful questions.
- Format each question as:

Q: Question

A: Answer

- Answers must be grounded in the policy topic.
- Do not invent exact prices, deadlines, thresholds, or penalties.
- Keep answers concise and operationally useful.
"""

        content, usage = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=FAQ_MAX_TOKENS,
        )

        self._log_usage(
            metadata.doc_id,
            usage,
            "faq",
        )

        return content.strip()

    # ------------------------------------------------------------------------
    # FALLBACK HEADINGS
    # ------------------------------------------------------------------------

    @staticmethod
    def _fallback_headings() -> list[str]:
        """Return fallback headings if the LLM fails to produce an outline."""

        return [
            "Purpose and Scope",
            "Eligibility",
            "Policy Rules",
            "Customer Responsibilities",
            "Employee Responsibilities",
            "Operational Procedure",
            "Exceptions and Special Cases",
            TABLE_SECTION_NAME,
        ]

    # ------------------------------------------------------------------------
    # H2 EXTRACTION
    # ------------------------------------------------------------------------

    @staticmethod
    def _extract_h2_headings(
        markdown: str,
    ) -> list[str]:
        """
        Extract H2 headings.

        Important:
        This intentionally does NOT require a trailing '*'.
        """

        pattern = re.compile(
            r"^##\s+(.+?)\s*$",
            re.MULTILINE,
        )

        headings = []

        for match in pattern.finditer(markdown):
            heading = match.group(1).strip()

            if heading:
                headings.append(heading)

        return headings

    # ------------------------------------------------------------------------
    # CLEAN MARKDOWN
    # ------------------------------------------------------------------------

    @staticmethod
    def _clean_markdown(
        markdown: str,
    ) -> str:
        """Remove common unwanted Markdown wrappers."""

        markdown = markdown.strip()

        if markdown.startswith("```markdown"):
            markdown = markdown[len("```markdown"):].strip()

        elif markdown.startswith("```md"):
            markdown = markdown[len("```md"):].strip()

        elif markdown.startswith("```"):
            markdown = markdown[3:].strip()

        if markdown.endswith("```"):
            markdown = markdown[:-3].strip()

        return markdown

    # ------------------------------------------------------------------------
    # USAGE
    # ------------------------------------------------------------------------

    @staticmethod
    def _log_usage(
        doc_id: str,
        usage: dict,
        operation: str,
    ) -> None:
        """Log token usage."""

        if not usage:
            return

        prompt_tokens = usage.get(
            "prompt_tokens",
            0,
        )

        completion_tokens = usage.get(
            "completion_tokens",
            0,
        )

        total_tokens = usage.get(
            "total_tokens",
            0,
        )

        logger.info(
            "LLM usage | doc=%s | operation=%s | "
            "prompt=%s | completion=%s | total=%s",
            doc_id,
            operation,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )

        if completion_tokens >= MAX_COMPLETION_TOKENS_TO_WARN:
            logger.warning(
                "Completion reached warning threshold | "
                "doc=%s | operation=%s | completion=%s",
                doc_id,
                operation,
                completion_tokens,
            )


# ============================================================================
# MARKDOWN → PLAIN TEXT
# ============================================================================


_TABLE_SEPARATOR_RE = re.compile(
    r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$"
)


def markdown_to_plain_text(
    markdown: str,
) -> str:
    """
    Convert generated Markdown into clean plain text.

    Tables are flattened into column-separated rows.
    """

    output: list[str] = []

    for raw_line in markdown.splitlines():

        line = raw_line.strip()

        if not line:
            output.append("")
            continue

        heading_match = re.match(
            r"^#{2,6}\s+(.+)",
            line,
        )

        if heading_match:
            text = heading_match.group(1).strip()

            output.append(text.upper())
            output.append("-" * len(text))

            continue

        if _TABLE_SEPARATOR_RE.match(line):
            continue

        if line.startswith("|") and line.endswith("|"):
            cells = [
                cell.strip()
                for cell in line.strip("|").split("|")
            ]

            line = "  |  ".join(cells)

        line = re.sub(
            r"`(.+?)`",
            r"\1",
            line,
        )

        line = re.sub(
            r"\*\*(.+?)\*\*",
            r"\1",
            line,
        )

        line = re.sub(
            r"\*(.+?)\*",
            r"\1",
            line,
        )

        output.append(line)

    text = "\n".join(output).strip()

    return text + "\n"


# ============================================================================
# PDF RENDERER
# ============================================================================


class PDFRenderer:
    """Render generated Markdown into a simple PDF."""

    def __init__(self) -> None:

        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "DocumentTitle",
            parent=self.styles["Title"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=16,
        )

        self.h2_style = ParagraphStyle(
            "H2",
            parent=self.styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=8,
        )

        self.h3_style = ParagraphStyle(
            "H3",
            parent=self.styles["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=5,
        )

        self.body_style = ParagraphStyle(
            "Body",
            parent=self.styles["BodyText"],
            fontSize=9.5,
            leading=13,
            spaceAfter=6,
        )

        self.small_style = ParagraphStyle(
            "Small",
            parent=self.styles["BodyText"],
            fontSize=8,
            leading=10,
            spaceAfter=4,
        )

    # ------------------------------------------------------------------------
    # RENDER
    # ------------------------------------------------------------------------

    def render(
        self,
        document: KnowledgeDocument,
        output_path: Path,
    ) -> None:
        """Render a KnowledgeDocument to PDF."""

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf = SimpleDocTemplate(
            str(output_path),
            pagesize=LETTER,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
            title=document.metadata.title,
            author="Aether Wireless",
        )

        story: list = []

        self._add_title(
            story,
            document.metadata,
        )

        markdown_lines = document.body_md.splitlines()

        index = 0

        while index < len(markdown_lines):

            line = markdown_lines[index].strip()

            if not line:
                index += 1
                continue

            # ----------------------------------------------------------------
            # H2
            # ----------------------------------------------------------------

            if line.startswith("## "):

                heading = line[3:].strip()

                story.append(
                    Paragraph(
                        self._escape(heading),
                        self.h2_style,
                    )
                )

                index += 1
                continue

            # ----------------------------------------------------------------
            # H3
            # ----------------------------------------------------------------

            if line.startswith("### "):

                heading = line[4:].strip()

                story.append(
                    Paragraph(
                        self._escape(heading),
                        self.h3_style,
                    )
                )

                index += 1
                continue

            # ----------------------------------------------------------------
            # TABLE
            # ----------------------------------------------------------------

            if self._is_table_start(
                markdown_lines,
                index,
            ):

                table, new_index = self._parse_table(
                    markdown_lines,
                    index,
                )

                if table:

                    story.append(table)
                    story.append(Spacer(1, 8))

                index = new_index
                continue

            # ----------------------------------------------------------------
            # NUMBERED LIST
            # ----------------------------------------------------------------

            numbered_match = re.match(
                r"^(\d+)\.\s+(.+)",
                line,
            )

            if numbered_match:

                number = numbered_match.group(1)
                text = numbered_match.group(2)

                story.append(
                    Paragraph(
                        f"<b>{number}.</b> "
                        f"{self._format_inline(text)}",
                        self.body_style,
                    )
                )

                index += 1
                continue

            # ----------------------------------------------------------------
            # BULLET
            # ----------------------------------------------------------------

            if line.startswith("- ") or line.startswith("* "):

                text = line[2:].strip()

                story.append(
                    Paragraph(
                        f"• {self._format_inline(text)}",
                        self.body_style,
                    )
                )

                index += 1
                continue

            # ----------------------------------------------------------------
            # FAQ
            # ----------------------------------------------------------------

            if line.startswith("Q:"):

                question = line[2:].strip()

                story.append(
                    Paragraph(
                        f"<b>Q:</b> "
                        f"{self._format_inline(question)}",
                        self.body_style,
                    )
                )

                index += 1
                continue

            if line.startswith("A:"):

                answer = line[2:].strip()

                story.append(
                    Paragraph(
                        f"<b>A:</b> "
                        f"{self._format_inline(answer)}",
                        self.body_style,
                    )
                )

                index += 1
                continue

            # ----------------------------------------------------------------
            # REGULAR PARAGRAPH
            # ----------------------------------------------------------------

            paragraph_lines = [line]

            next_index = index + 1

            while next_index < len(markdown_lines):

                next_line = markdown_lines[next_index].strip()

                if not next_line:
                    break

                if (
                    next_line.startswith("## ")
                    or next_line.startswith("### ")
                    or next_line.startswith("- ")
                    or next_line.startswith("* ")
                    or next_line.startswith("Q:")
                    or next_line.startswith("A:")
                    or re.match(
                        r"^\d+\.\s+",
                        next_line,
                    )
                    or self._is_table_start(
                        markdown_lines,
                        next_index,
                    )
                ):
                    break

                paragraph_lines.append(next_line)

                next_index += 1

            paragraph = " ".join(paragraph_lines)

            story.append(
                Paragraph(
                    self._format_inline(paragraph),
                    self.body_style,
                )
            )

            index = next_index

        pdf.build(story)

    # ------------------------------------------------------------------------
    # TITLE
    # ------------------------------------------------------------------------

    def _add_title(
        self,
        story: list,
        metadata: KnowledgeMetadata,
    ) -> None:
        """Add document title and metadata."""

        story.append(
            Paragraph(
                self._escape(metadata.title),
                self.title_style,
            )
        )

        metadata_table = Table(
            [
                [
                    "<b>Document ID</b>",
                    self._escape(metadata.doc_id),
                    "<b>Version</b>",
                    self._escape(metadata.version),
                ],
                [
                    "<b>Department</b>",
                    self._escape(metadata.department),
                    "<b>Category</b>",
                    self._escape(metadata.category),
                ],
                [
                    "<b>Last Updated</b>",
                    self._escape(metadata.last_updated),
                    "<b>Status</b>",
                    "Active",
                ],
            ],
            colWidths=[
                1.0 * inch,
                1.55 * inch,
                1.0 * inch,
                1.55 * inch,
            ],
        )

        metadata_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, -1),
                        "Helvetica",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(metadata_table)
        story.append(Spacer(1, 16))

    # ------------------------------------------------------------------------
    # TABLE DETECTION
    # ------------------------------------------------------------------------

    @staticmethod
    def _is_table_start(
        lines: list[str],
        index: int,
    ) -> bool:
        """Check whether the current line starts a Markdown table."""

        if index + 1 >= len(lines):
            return False

        current = lines[index].strip()
        separator = lines[index + 1].strip()

        if "|" not in current:
            return False

        return bool(
            _TABLE_SEPARATOR_RE.match(separator)
        )

    # ------------------------------------------------------------------------
    # TABLE PARSING
    # ------------------------------------------------------------------------

    def _parse_table(
        self,
        lines: list[str],
        index: int,
    ) -> tuple[Table | None, int]:
        """Parse a basic Markdown table."""

        rows: list[list[str]] = []

        while index < len(lines):

            line = lines[index].strip()

            if not line or "|" not in line:
                break

            if (
                len(rows) == 1
                and _TABLE_SEPARATOR_RE.match(line)
            ):
                index += 1
                continue

            cells = [
                cell.strip()
                for cell in line.strip("|").split("|")
            ]

            rows.append(
                [
                    self._format_inline(cell)
                    for cell in cells
                ]
            )

            index += 1

        if not rows:
            return None, index

        table = Table(
            rows,
            repeatRows=1,
            hAlign="LEFT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table, index

    # ------------------------------------------------------------------------
    # ESCAPE
    # ------------------------------------------------------------------------

    @staticmethod
    def _escape(
        text: str,
    ) -> str:
        """Escape text for ReportLab."""

        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    # ------------------------------------------------------------------------
    # INLINE MARKDOWN
    # ------------------------------------------------------------------------

    def _format_inline(
        self,
        text: str,
    ) -> str:
        """Convert basic Markdown inline formatting to ReportLab HTML."""

        text = self._escape(text)

        # Inline code
        text = re.sub(
            r"`(.+?)`",
            r"<font name='Courier'>\1</font>",
            text,
        )

        # Bold
        text = re.sub(
            r"\*\*(.+?)\*\*",
            r"<b>\1</b>",
            text,
        )

        # Italic
        text = re.sub(
            r"\*(.+?)\*",
            r"<i>\1</i>",
            text,
        )

        return text


# ============================================================================
# PDF PAGE COUNT
# ============================================================================


def count_pdf_pages(
    pdf_path: Path,
) -> int | None:
    """Return PDF page count."""

    if not HAVE_PDF_READER:
        return None

    try:
        return len(
            PdfReader(str(pdf_path)).pages
        )

    except Exception:
        logger.warning(
            "Could not read PDF page count: %s",
            pdf_path,
        )

        return None


# ============================================================================
# FILE OUTPUT
# ============================================================================


def document_output_dir(
    metadata: KnowledgeMetadata,
) -> Path:
    """Return category directory."""

    return RAW_DIR / metadata.category


def document_filename(
    metadata: KnowledgeMetadata,
) -> str:
    """Create filesystem-safe filename."""

    filename = metadata.title.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename,
    )

    filename = filename.strip("_")

    return (
        f"{metadata.doc_id}_{filename}"
    )


def save_document(
    document: KnowledgeDocument,
    renderer: PDFRenderer,
    *,
    keep_md: bool,
    keep_txt: bool,
) -> dict[str, Path]:
    """
    Save PDF and optionally Markdown/plain text.
    """

    output_dir = document_output_dir(
        document.metadata
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = document_filename(
        document.metadata
    )

    paths: dict[str, Path] = {}

    # ------------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------------

    if keep_md:

        md_path = (
            output_dir
            / f"{base_name}.md"
        )

        md_path.write_text(
            document.body_md,
            encoding="utf-8",
        )

        paths["md"] = md_path

    # ------------------------------------------------------------------------
    # Plain text
    # ------------------------------------------------------------------------

    if keep_txt:

        txt_path = (
            output_dir
            / f"{base_name}.txt"
        )

        txt_path.write_text(
            markdown_to_plain_text(
                document.body_md
            ),
            encoding="utf-8",
        )

        paths["txt"] = txt_path

    # ------------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------------

    pdf_path = (
        output_dir
        / f"{base_name}.pdf"
    )

    renderer.render(
        document,
        pdf_path,
    )

    paths["pdf"] = pdf_path

    return paths


# ============================================================================
# CATALOG FILTERING
# ============================================================================


def select_documents(
    *,
    limit: int | None,
    category: str | None,
) -> list[KnowledgeMetadata]:
    """Select documents from the catalog."""

    documents = DOCUMENT_CATALOG

    if category:

        category = category.lower()

        documents = [
            document
            for document in documents
            if document.category.lower()
            == category
        ]

    if limit is not None:
        documents = documents[:limit]

    return documents


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate Aether Wireless telecom "
            "policy knowledge-base documents."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum number of documents "
            "to generate."
        ),
    )

    parser.add_argument(
        "--only",
        dest="category",
        choices=[
            "billing",
            "mobile",
            "roaming",
            "customer",
            "compliance",
        ],
        help=(
            "Generate only documents "
            "from one category."
        ),
    )

    parser.add_argument(
        "--keep-md",
        action="store_true",
        help=(
            "Also save the generated "
            "Markdown source file."
        ),
    )

    parser.add_argument(
        "--keep-txt",
        action="store_true",
        help=(
            "Also save a plain-text "
            "rendering."
        ),
    )

    return parser.parse_args()


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    """Application entry point."""

    global HF_TOKEN

    # ------------------------------------------------------------------------
    # Load environment
    # ------------------------------------------------------------------------

    load_dotenv(ENV_PATH)

    HF_TOKEN = os.getenv(
        "HF_TOKEN"
    )

    if not HF_TOKEN:

        logger.error(
            "HF_TOKEN is missing. "
            "Add HF_TOKEN=... to %s",
            ENV_PATH,
        )

        return 1

    # ------------------------------------------------------------------------
    # Parse CLI
    # ------------------------------------------------------------------------

    args = parse_args()

    documents = select_documents(
        limit=args.limit,
        category=args.category,
    )

    if not documents:

        logger.warning(
            "No documents selected."
        )

        return 0

    # ------------------------------------------------------------------------
    # Startup information
    # ------------------------------------------------------------------------

    logger.info(
        "Selected %d document(s).",
        len(documents),
    )

    logger.info(
        "Hugging Face model: %s",
        MODEL,
    )

    logger.info(
        "Output directory: %s",
        RAW_DIR,
    )

    logger.info(
        "Sections per document: %d",
        LONG_DOC_SECTIONS,
    )

    if not HAVE_PDF_READER:

        logger.info(
            "pypdf is not installed. "
            "Page-count verification "
            "will be skipped."
        )

    # ------------------------------------------------------------------------
    # Generator
    # ------------------------------------------------------------------------

    renderer = PDFRenderer()

    successful = 0
    failed = 0
    short_pages = 0

    start_time = time.perf_counter()

    llm = LLMClient(HF_TOKEN)

    generator = DocumentGenerator(llm)

    # ------------------------------------------------------------------------
    # Generate documents
    # ------------------------------------------------------------------------

    for index, metadata in enumerate(
        documents,
        start=1,
    ):

        logger.info(
            "Processing document %d/%d: %s",
            index,
            len(documents),
            metadata.title,
        )

        try:

            document = generator.generate(
                metadata
            )

            paths = save_document(
                document,
                renderer,
                keep_md=args.keep_md,
                keep_txt=args.keep_txt,
            )

            for fmt, path in paths.items():

                logger.info(
                    "Generated %s: %s",
                    fmt.upper(),
                    path,
                )

            # ---------------------------------------------------------------
            # Page count
            # ---------------------------------------------------------------

            page_count = count_pdf_pages(
                paths["pdf"]
            )

            if page_count is not None:

                if page_count < MIN_PAGES:

                    short_pages += 1

                    logger.warning(
                        "%s has only %d page(s), "
                        "below the %d-page target.",
                        metadata.doc_id,
                        page_count,
                        MIN_PAGES,
                    )

                else:

                    logger.info(
                        "%s rendered with %d page(s).",
                        metadata.doc_id,
                        page_count,
                    )

            successful += 1

        except Exception:

            failed += 1

            logger.exception(
                "Failed to generate %s (%s)",
                metadata.title,
                metadata.doc_id,
            )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    elapsed = (
        time.perf_counter()
        - start_time
    )

    logger.info(
        "Generation completed | "
        "successful=%d | "
        "failed=%d | "
        "below_page_target=%d | "
        "elapsed=%.2fs",
        successful,
        failed,
        short_pages,
        elapsed,
    )

    return 1 if failed else 0


# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    raise SystemExit(
        main()
    )


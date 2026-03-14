"""
Configuration constants and source URLs for the Global AI Governance data pipeline.

All EU and India law sources to fetch. Each source includes metadata for
storage and categorization.
"""

from typing import TypedDict


class LawSource(TypedDict, total=False):
    """Schema for a single law source."""

    regulation_id: str
    source_url: str
    law_name: str
    law_category: str
    law_type: str
    country: str
    year: int
    fallback_urls: list[str]  # Alternate URLs if primary returns HTML


# Law categories for tagging
LAW_CATEGORIES = [
    "data_protection",
    "criminal",
    "labour",
    "consumer",
    "cyber",
    "civil",
    "constitutional",
    "financial",
    "environmental",
    "health",
]

# -----------------------------------------------------------------------------
# EU LAWS (eur-lex.europa.eu)
# -----------------------------------------------------------------------------

EU_LAWS: list[LawSource] = [
    # Data Protection & Privacy
    {
        "regulation_id": "EU_GDPR_2016",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
        "law_name": "General Data Protection Regulation",
        "law_category": "data_protection",
        "law_type": "regulation",
        "country": "EU",
        "year": 2016,
    },
    {
        "regulation_id": "EU_ePRIVACY_2002",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058",
        "law_name": "ePrivacy Directive",
        "law_category": "data_protection",
        "law_type": "directive",
        "country": "EU",
        "year": 2002,
    },
    # Cybersecurity
    {
        "regulation_id": "EU_CYBER_ACT_2019",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0881",
        "law_name": "EU Cybersecurity Act",
        "law_category": "cyber",
        "law_type": "regulation",
        "country": "EU",
        "year": 2019,
    },
    {
        "regulation_id": "EU_NIS2_2022",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555",
        "law_name": "NIS2 Directive",
        "law_category": "cyber",
        "law_type": "directive",
        "country": "EU",
        "year": 2022,
    },
    # Digital & Tech
    {
        "regulation_id": "EU_AI_ACT_2024",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        "law_name": "EU AI Act",
        "law_category": "cyber",
        "law_type": "regulation",
        "country": "EU",
        "year": 2024,
    },
    {
        "regulation_id": "EU_DSA_2022",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2065",
        "law_name": "Digital Services Act",
        "law_category": "cyber",
        "law_type": "regulation",
        "country": "EU",
        "year": 2022,
    },
    {
        "regulation_id": "EU_DMA_2022",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R1925",
        "law_name": "Digital Markets Act",
        "law_category": "cyber",
        "law_type": "regulation",
        "country": "EU",
        "year": 2022,
    },
    {
        "regulation_id": "EU_DATA_ACT_2023",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2854",
        "law_name": "Data Act",
        "law_category": "data_protection",
        "law_type": "regulation",
        "country": "EU",
        "year": 2023,
    },
    # Consumer & Liability
    {
        "regulation_id": "EU_PRODUCT_LIABILITY_2024",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L2853",
        "law_name": "Product Liability Directive",
        "law_category": "consumer",
        "law_type": "directive",
        "country": "EU",
        "year": 2024,
    },
    {
        "regulation_id": "EU_CONSUMER_RIGHTS_2011",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011L0083",
        "law_name": "Consumer Rights Directive",
        "law_category": "consumer",
        "law_type": "directive",
        "country": "EU",
        "year": 2011,
    },
    # Financial
    {
        "regulation_id": "EU_DORA_2022",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R2554",
        "law_name": "Digital Operational Resilience Act (DORA)",
        "law_category": "financial",
        "law_type": "regulation",
        "country": "EU",
        "year": 2022,
    },
    # Employment
    {
        "regulation_id": "EU_WORKING_TIME_2003",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32003L0088",
        "law_name": "Working Time Directive",
        "law_category": "labour",
        "law_type": "directive",
        "country": "EU",
        "year": 2003,
    },
    {
        "regulation_id": "EU_PLATFORM_WORK_2024",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L2831",
        "law_name": "Platform Work Directive",
        "law_category": "labour",
        "law_type": "directive",
        "country": "EU",
        "year": 2024,
    },
]

# -----------------------------------------------------------------------------
# INDIA LAWS (legislative.gov.in) — PDF URLs
# indiacode.nic.in blocks scrapers; legislative.gov.in allows direct PDF access
# -----------------------------------------------------------------------------

INDIA_LAWS: list[LawSource] = [
    # Data & Tech
    {
        "regulation_id": "INDIA_DPDP_2023",
        "source_url": "https://legislative.gov.in/sites/default/files/A2023-22.pdf",
        "law_name": "Digital Personal Data Protection Act",
        "law_category": "data_protection",
        "law_type": "act",
        "country": "India",
        "year": 2023,
    },
    {
        "regulation_id": "INDIA_IT_ACT_2000",
        "source_url": "https://legislative.gov.in/sites/default/files/A2000-21.pdf",
        "law_name": "Information Technology Act",
        "law_category": "cyber",
        "law_type": "act",
        "country": "India",
        "year": 2000,
    },
    {
        "regulation_id": "INDIA_IT_AMENDMENT_2008",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/15386/1/it_amendment_act2008.pdf",
        "law_name": "IT (Amendment) Act",
        "law_category": "cyber",
        "law_type": "act",
        "country": "India",
        "year": 2008,
    },
    # Criminal
    {
        "regulation_id": "INDIA_BNS_2023",
        "source_url": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
        "law_name": "Bharatiya Nyaya Sanhita (Criminal Code)",
        "law_category": "criminal",
        "law_type": "act",
        "country": "India",
        "year": 2023,
    },
    {
        "regulation_id": "INDIA_BNSS_2023",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/20064/1/bnss_2023.pdf",
        "law_name": "Bharatiya Nagarik Suraksha Sanhita (Criminal Procedure)",
        "law_category": "criminal",
        "law_type": "act",
        "country": "India",
        "year": 2023,
    },
    # Consumer & Commerce
    {
        "regulation_id": "INDIA_CONSUMER_PROTECTION_2019",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/16939/1/a2019-35.pdf",
        "law_name": "Consumer Protection Act",
        "law_category": "consumer",
        "law_type": "act",
        "country": "India",
        "year": 2019,
    },
    {
        "regulation_id": "INDIA_COMPETITION_2002",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/2010/7/A2003-12.pdf",
        "law_name": "Competition Act",
        "law_category": "consumer",
        "law_type": "act",
        "country": "India",
        "year": 2002,
    },
    # Financial
    {
        "regulation_id": "INDIA_RBI_1934",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/2398/1/a1934-2.pdf",
        "law_name": "Reserve Bank of India Act",
        "law_category": "financial",
        "law_type": "act",
        "country": "India",
        "year": 1934,
    },
    {
        "regulation_id": "INDIA_SEBI_1992",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/1890/1/AA1992__15secu.pdf",
        "law_name": "SEBI Act",
        "law_category": "financial",
        "law_type": "act",
        "country": "India",
        "year": 1992,
    },
    # Labour
    {
        "regulation_id": "INDIA_INDUSTRIAL_RELATIONS_2020",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/22040/1/aa202035.pdf",
        "law_name": "Industrial Relations Code",
        "law_category": "labour",
        "law_type": "act",
        "country": "India",
        "year": 2020,
    },
    {
        "regulation_id": "INDIA_WAGES_2019",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/15793/1/aA2019-29.pdf",
        "law_name": "Code on Wages",
        "law_category": "labour",
        "law_type": "act",
        "country": "India",
        "year": 2019,
    },
    # Health
    {
        "regulation_id": "INDIA_CLINICAL_EST_2010",
        "source_url": "https://www.indiacode.nic.in/bitstream/123456789/7798/1/201023_clinical_establishments_(registration_and_regulation)_act,_2010.pdf",
        "law_name": "Clinical Establishments Act",
        "law_category": "health",
        "law_type": "act",
        "country": "India",
        "year": 2010,
    },
]

# -----------------------------------------------------------------------------
# HTTP settings
# -----------------------------------------------------------------------------

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 30
PDF_DOWNLOAD_TIMEOUT = 90

# -----------------------------------------------------------------------------
# Clause extraction
# -----------------------------------------------------------------------------

MIN_CLAUSE_LENGTH = 30
CLAUSE_BATCH_SIZE = 50

# Patterns for article/section detection
ARTICLE_PATTERNS = [
    r"Article\s+(\d+[a-z]?(?:\([a-z]\))?(?:\s*[-–][^\n]+)?)",
    r"Section\s+(\d+[A-Za-z]?(?:\([a-z]\))?)",
    r"^(\d+)\.\s+",
    r"Clause\s+(\d+)",
]
